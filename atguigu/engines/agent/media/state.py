from atguigu.engines.agent.media.tools.catalog import SearchTool
from atguigu.engines.contract.evidence import RetrievedEvidence
from atguigu.engines.contract.state import SectionState, ResearchGraphState


class MediaSectionState(SectionState):
    """搜索计划 这一章用哪个搜索工具，以及搜哪些关键词"""

    search_tool : SearchTool
    search_keywords : list[str]

# 类似于 list[int]
class MediaState(ResearchGraphState[MediaSectionState], total=False):
    """
    检索阶段产生的结果(当前状态):
    section_evidence_records 是每章搜到的网页证据，
    section_queries 是每章实际用的查询文本
    """

    section_evidence_records: list[list[RetrievedEvidence]]
    section_queries: list[str]