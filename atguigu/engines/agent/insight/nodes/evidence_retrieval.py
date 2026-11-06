from typing import Any
from loguru import logger
from atguigu.engines.agent.insight.state import InsightState
from atguigu.engines.agent.insight.tools.retrieve_tool import retrieval_evidence
from atguigu.engines.contract.context import ResearchBaseNode
from atguigu.engines.contract.role import get_role_display_name

class EvidenceRetrievalNode(ResearchBaseNode):
    """调检索工具，拿证据"""

    async def __call__(self,state:InsightState) -> dict[str, Any]:
        agent_name = get_role_display_name(self.context.role)

        logger.info(f"{agent_name} 开始执行私域信息搜索")

        query = self.context.query
        topic_key = state['topic_key']
        retrieved_evidence = await retrieval_evidence(query=query, topic_key=topic_key)

        logger.info(f'{agent_name}执行私域信息搜索完成')

        # retrieved_records 是状态里的一个字段。
        # 它装的是：检索节点拿回来的证据列表 record 记录
        return {"retrieved_records": retrieved_evidence}

