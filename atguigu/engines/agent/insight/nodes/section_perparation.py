from typing import Any
from loguru import logger
from atguigu.engines.agent.insight.state import InsightState
from atguigu.engines.contract.context import ResearchBaseNode
from atguigu.engines.contract.evidence import RetrievedEvidence
from atguigu.engines.contract.role import get_role_display_name
from atguigu.engines.contract.section import SECTION_DEFINITIONS, HEAT_AND_SPREAD
from atguigu.engines.contract.state import SectionState


def _select_section_evidences(section_key:str, state:InsightState) -> list[RetrievedEvidence]:
    """
    职责：这个函数：给某一章，挑证据，并排好序。
    1. channel_scores 每一条证据，各通道给的分。
    2. relevance_scores 每条证据的"总分" 是把 channel_scores 里两路加起来。
    3. hotness 每条证据的"互动热度"。 是 SourceDocument 里的字段。 是互动量的加权和。
    """

    # 1 获取基础信息
    record_ids_by_section = state['record_ids_by_section']  # 每个章节 → 该章节的证据 ID 列表。
    records_by_id = state['records_by_id']
    relevance_scores:dict[str,float] = state['relevance_scores']

    # 2 把这一章的 ID 列表，换成对象列表。(因为后面要排序，排序要读对象里的字段。)
    section_evidences:list[RetrievedEvidence] = [
        records_by_id[doc_id]
        for doc_id in record_ids_by_section[section_key] # 拿到章节id
    ]
    # relevance_score 是一个"小函数"。跟 def 定义的函数一样。
    # 只是用 lambda 写的，没名字，一行搞定。
    relevance_score = lambda record:relevance_scores[record.id]
    if section_key == HEAT_AND_SPREAD:
        '''
        第二个位置放什么  就按照第二个位置的大小排第一个位置的东西 默认从小到大
        '''
        return sorted(
            section_evidences,
            # 元组 : 第一个值：这条证据的 hotness（热度）。 第二个值：这条证据的 relevance_score（相关性分）。
            key = lambda record:(record.document.hotness,relevance_score(record)),
            reverse = True
        )
    return sorted(
        section_evidences,
        key = lambda record:relevance_score(record),
        reverse = True
    )




class SectionPreparationNode(ResearchBaseNode):
    """初始化固定章节并为各章节选择、排序和截取证据"""

    # 对象当函数
    async def __call__(self,state:InsightState) -> dict[str, Any]:
        '''
        生成五个章节的状态。
        给每一章，准备一份证据列表，交给后面的摘要节点用。
        '''
        agent_name = get_role_display_name(self.context.role)

        logger.info(f"{agent_name} 开始固定章节与证据准备")

        sections_state:list[SectionState] = []  # 这是一个空列表，用来装五章的"章节状态"。
        section_evidence_records:list[list[RetrievedEvidence]] = []  # 外面一层是"五章"，里面一层是"每章的证据"。
        for section_key ,section_definition in SECTION_DEFINITIONS.items():
            # 1 构建SectionState对象
            sections_state.append({
                'section_key': section_key,
                'title':section_definition.title,
            })

            # 2 选择该章节的证据列表
            section_evidences:list[RetrievedEvidence] = _select_section_evidences(section_key,state)
            section_evidence_records.append(section_evidences)

        logger.info(f"{agent_name} 固定章节与证据准备完成")
        return {
            'sections': sections_state,
            'section_evidence_records': section_evidence_records
        }


