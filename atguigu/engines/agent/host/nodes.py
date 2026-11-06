import json
from typing import Any
from loguru import logger
from atguigu.engines.agent.host.discussion import build_agent_discussion_event, build_judgement_discussion_event
from atguigu.engines.agent.host.section.judge import judge_section
from atguigu.engines.agent.host.section.output import AgentSectionOutput
from atguigu.engines.agent.host.state import HostState
from atguigu.engines.common.utils import get_report_dir, save_report
from atguigu.engines.contract.role import get_role_display_name


class HostNodes:
    """Host LangGraph 的章节收集、研判与持久化节点"""

    async def collect_agent_output(self,state:HostState) -> dict[str,Any]:
        """保存当前 Agent 章节输出并生成对应讨论事件"""
        agent_output = AgentSectionOutput.from_section_ready_event(
            state['event_payload']
        )
        # _outputs_by_section 存进了这里
        state['section_pair_store'].store_output(agent_output)

        # 讨论事件就是给前端看的状态
        discussion_events = [
            build_agent_discussion_event(state['task_id'],agent_output),
        ]

        return {
            'discussion_events': discussion_events,
        }

    async def generate_section_judgement(
            self,
            state:HostState,
    ) -> dict[str,Any]:
        """调用 Host LLM 研判当前已齐备章节，并记录研判结果与讨论事件"""
        section_pair = state['section_pair_store'].get_ready_pair() # 取对子

        logger.info(f"【{get_role_display_name('host')}】双Agent章节已齐备,开始研判 章节={section_pair.section_key}")

        section_judgement = await judge_section(section_pair) # 出结果
        state['section_pair_store'].mark_judged(section_judgement.section_key) # 标记已研判
        # 五个章节的研判后的结果【结构化对象】
        judgements = [*state['judgements'],section_judgement]
        discussion_events = [
            *state['discussion_events'],
            build_agent_discussion_event(
                state['task_id'],
                section_judgement
            )
        ]

        logger.info(f"【{get_role_display_name('host')}】章节研判完成 章节={section_judgement.section_key}")

        # 节点（Node）的返回规则是：你改了什么，就只返回什么。 这是LangGraph这个框架的规定
        return {
            'judgements': judgements,
            'discussion_events': discussion_events,
        }

    async def save_judgement(self,state:HostState) -> dict[str,Any]:
        """保存研判结果"""
        output_dir = get_report_dir(state['task_id'],'host')

        structured_content = json.dumps(
            # model_dump() : 把“对象”扒掉外衣，变成最基础的“字典”（dict）
            [ i.model_dump() for i in state['judgements']],
            ensure_ascii=False, # 中文原样写入
            indent=2,
        )
        # json_path 就是output_dir加上具体文件名
        json_path = save_report(
            output_dir,
            'judgement.json',
            structured_content,
        )

        logger.info(f"Host 结构化研判已保存 {json_path}")

        return {} # 干完了 不需要更新任何state里的数据










