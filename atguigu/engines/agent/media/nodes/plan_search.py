import json
from typing import Any
from loguru import logger
from langchain_core.prompts import PromptTemplate

from atguigu.engines.agent.media.output import MediaSearchPlanOutput
from atguigu.engines.agent.media.state import MediaState, MediaSectionState
from atguigu.engines.agent.media.tools.catalog import SEARCH_TOOL_DESCRIPTIONS
from atguigu.engines.contract.context import ResearchBaseNode
from atguigu.engines.contract.role import get_role_display_name
from atguigu.engines.contract.section import (
    SECTION_DEFINITIONS,
    get_section_definitions_for_role
)
from atguigu.engines.prompts.media import MEDIA_SEARCH_PLAN_USER_PROMPT, MEDIA_SEARCH_PLAN_SYSTEM_PROMPT


class PlanSearchNode(ResearchBaseNode):
    '''
    这个节点是"搜索规划师"：让 LLM 为固定的几个 Media 章节，各挑一个搜索工具 + 配几个关键词。
    '''


    async def __call__(self,state:MediaState) -> dict[str,Any]:
        '''
        让 LLM 给固定章节配"搜索工具 + 关键词"，拼好后返回。
        '''

        agent_name = get_role_display_name(self.context.role)

        planned_output = await self._generate_search_plan(self.context.query)

        sections:list[MediaSectionState] = [
            MediaSectionState(
                section_key=section_definition.key,
                title=section_definition.title,
                search_tool=planned_section.search_tool,
                search_keywords=[keyword.strip() for keyword in planned_section.search_keywords],
            )
            for section_definition,planned_section in zip(
                SECTION_DEFINITIONS.values(),  # 章节定义
                planned_output.sections  # 搜索计划
            )
        ]

        logger.info(f"{agent_name} 公域搜索策略规划完成")

        return {
            "sections": sections  # 章节信息列表(章节信息:章节定义+搜索策略)
        }

    async def _generate_search_plan(self, research_topic:str) -> MediaSearchPlanOutput:
        """组装搜索规划提示词并调用 LLM 返回结构化搜索计划"""

        search_tools = [
            {'name':tool, 'description':description}
            for tool, description in SEARCH_TOOL_DESCRIPTIONS.items()
        ]

        # PromptTemplate.from_template 把一段带占位符的提示词模板，变成一个能填值的模板对象。
        user_prompt = PromptTemplate.from_template(MEDIA_SEARCH_PLAN_USER_PROMPT).format(
            research_topic=research_topic,
            section_contexts=json.dumps(
                get_section_definitions_for_role('media'),
                # ensure_ascii=True（默认）：中文转义成 \u9ad8\u8003 这种形式
                ensure_ascii=False,
                indent=2
            ),
            search_tools=json.dumps(
                search_tools,
                ensure_ascii=False,
                indent=2
            )
        )

        return await self.context.llm_client.generate_object(
            system_prompt=MEDIA_SEARCH_PLAN_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            structed_object=MediaSearchPlanOutput
        )
















