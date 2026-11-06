from typing import Callable, Awaitable

from loguru import logger

from atguigu.engines.agent.insight.invoker import invoke_insight_agent
from atguigu.engines.agent.media.invoker import invoke_media_agent
from atguigu.engines.common.llm import LLMClient
from atguigu.engines.common.log import execute_logger
from atguigu.engines.common.task import ResearchTask, task_manager
from atguigu.engines.common.utils import get_report_dir
from atguigu.engines.contract.events import publish_role_result, RoleResultEvent
from atguigu.engines.contract.role import RoleId

# callable 就是可以通过()来调用
# awaitable 就是可以await的对象
AGENT_INVOKER: Callable[[str,str,str,LLMClient,str],Awaitable[None]]


class ResearchOrchestrator:
    def __init__(self):
        self.agent_invoker: dict[RoleId,AGENT_INVOKER] = {
            'insight': invoke_insight_agent,
            'media': invoke_media_agent
        }

    # dispatch 分发
    def dispatch_task(self, research_task: ResearchTask):
        """
        职责：将研究任务转发给两个研究Agent 并发执行
        :param research_task:
        :return:
        """
        for role in self.agent_invoker:
            task_manager.create_background_task(self.invoke_research_agent(role,research_task))

    async def invoke_research_agent(self, role, research_task):
        # 1 获得两个角色的llm客户端
        llm_client = LLMClient.from_role(role)

        # 2 获得md文档的目录
        output_dir = get_report_dir(research_task.task_id,role)

        # 3 执行两个角色的agent
        with execute_logger(role):
            try:
                # agent_invoker[role] 得到函数
                await self.agent_invoker[role](
                    role,
                    research_task.query,
                    research_task.task_id,
                    llm_client,
                    output_dir
                )
            except Exception as exc:
                logger.error(f'{role} 研究智能体执行期间出现了异常,异常情况: {exc}')
                publish_role_result(RoleResultEvent(task_id=research_task.task_id, role=role, error=str(exc)))
                return

            publish_role_result(RoleResultEvent(task_id=research_task.task_id, role=role))


