from typing import Any

from atguigu.engines.common.section_summary import BaseSectionSummaryNode
from atguigu.engines.prompts.media import MEDIA_SECTION_SUMMARY_SYSTEM_PROMPT


class SectionSummaryNode(BaseSectionSummaryNode):
    """给某一章，用搜到的证据写正文"""

    system_prompt = MEDIA_SECTION_SUMMARY_SYSTEM_PROMPT
    # fallback 兜底方案
    fallback_body = "【数据缺口】该章节未在可用数据源中检索到相关内容,本章节暂无分析结论。"

    def _query(self,state:dict[str, Any],cursor :int) -> str:
        '''
        按位置取出"当前这一章用过的查询词"
        '''

        return state['section_queries'][cursor]