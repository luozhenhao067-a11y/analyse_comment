import asyncio
import json
from itertools import zip_longest
from typing import Any
from loguru import logger
from langchain_core.prompts import PromptTemplate

from atguigu.engines.agent.media.output import MediaSearchPlanOutput
from atguigu.engines.agent.media.state import MediaState, MediaSectionState
from atguigu.engines.agent.media.tools.catalog import SEARCH_TOOL_DESCRIPTIONS
from atguigu.engines.agent.media.tools.retrieval_tool import retrieve_evidence
from atguigu.engines.contract.context import ResearchBaseNode
from atguigu.engines.contract.evidence import RetrievedEvidence
from atguigu.engines.contract.role import get_role_display_name
from atguigu.engines.contract.section import (
    SECTION_DEFINITIONS,
    get_section_definitions_for_role
)
from atguigu.engines.prompts.media import MEDIA_SEARCH_PLAN_USER_PROMPT, MEDIA_SEARCH_PLAN_SYSTEM_PROMPT


def _merge_query_results(query_results:list[list[RetrievedEvidence]]) -> list[RetrievedEvidence]:
    '''
    几堆结果轮流取，去重，凑够 10 条(anspire返回的结果的是按照相关性排好的)

    query_results = [
    [证据, 证据, ...],   # 第1个查询词搜到的
    [证据, 证据, ...],   # 第2个查询词搜到的
    [证据, 证据, ...],   # 第3个查询词搜到的
    ]
    '''

    selected_records:list[RetrievedEvidence] = []
    # 查重都用集合
    # 每条证据，先看 record.id 在不在 seen_ids 里 在 → 说明重复了，跳过 不在 → 加进 seen_ids，然后收下这条
    seen_ids:set[str] = set()
    # 把多堆东西"并排"起来，其中一堆不够长就补 None。
    for ranked_records in zip_longest(*query_results):
        for record in ranked_records:  # record 是"一条证据"。 一条条过，最终把每一堆、每一条都走一遍。
            if record is None or record.id in seen_ids:
                continue
            selected_records.append(record)
            seen_ids.add(record.id)
    return selected_records[:10]

class SearchNode(ResearchBaseNode):
    """核心：把每个章节的关键词拿去搜，搜完的结果去重、合并。"""

    async def __call__(self, state:MediaState) -> dict[str,Any]:
        '''遍历章节执行检索并去重'''
        agent_name = get_role_display_name(self.context.role)

        logger.info(f"{agent_name} 开始执行公域信息搜索")

        query = self.context.query
        sections:list[MediaSectionState] = state.get('sections')
        section_evidence_records = []
        section_queries:list[str] = []

        for section in sections:
            tool = section.get('search_tool')
            keywords = section.get('search_keywords')
            queries = [f'{query}{keyword}'.strip() for keyword in keywords]

            # 把多个异步任务"同时"跑，等它们都跑完，一起收结果
            query_results = await asyncio.gather(
                *(
                    # 一个"生成器"——里面装着每个查询词的检索任务。
                    retrieve_evidence(tool,search_query)
                    for search_query in queries
                ),
                # 某个任务报错了，不中断，把"错误"当结果一起收回来。c
                return_exceptions=True
            )

            # 把同一个章节、多个查询词搜到的结果，合并成一份、去重。
            section_records = _merge_query_results(query_results)
            section_evidence_records.append(section_records)
            section_queries.append(
                '\n'.join([f'{query}' for query in queries])
            )

            logger.info(f"{agent_name} 执行公域信息搜索完成")

        return {
            "section_evidence_records": section_evidence_records,  # 给后面写正文用
            "section_queries": section_queries  # 记录"这证据是怎么搜来的"
        }















