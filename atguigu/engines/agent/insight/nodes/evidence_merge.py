"""Insight 两路证据的通道分合并与相关性打分。"""

from typing import Any

from loguru import logger

from atguigu.engines.agent.insight.state import InsightState
from atguigu.engines.contract.context import ResearchBaseNode
from atguigu.engines.contract.evidence import RetrievedEvidence
from atguigu.engines.contract.role import get_role_display_name


def _get_candidate_evidence(retrieved_records:list[RetrievedEvidence]) -> dict[str,RetrievedEvidence]:
    '''
    这个函数就干一件事：把两路重复的证据合到一起
    '''
    records_by_id:dict[str,RetrievedEvidence] = {}
    for retrieved_record in retrieved_records:
        # retrieved_record 是当前遍历到的那条。
        doc_id = retrieved_record.id
        # retrieved_evidence 是record_by_id里的值
        retrieved_evidence = records_by_id.get(doc_id) # 第一次循环拿的全是None,不过由于是get(),他不会报错,往下
        if retrieved_evidence is None:
            records_by_id[doc_id] = retrieved_record
            continue
        exist_evidence = records_by_id.get(doc_id)
        new_evidence = RetrievedEvidence(
            # * 在函数定义时是打包 在其他任何时候都是解包
            document=retrieved_record.document,
            channel_scores={**exist_evidence.channel_scores, **retrieved_evidence.channel_scores},
        )
        records_by_id[doc_id] = new_evidence # 用新证据替换旧证据

    return records_by_id


def _compute_relevance_score(retrieved_evidence:Any) -> dict[str,float]:
    relevance_scores:dict[str,float] = {}
    for evidence in retrieved_evidence:
        relevance_scores[evidence.id] = evidence.channel_scores.get('db_channal',0)+  evidence.channel_scores.get('vector_channel',0)
    return  relevance_scores



class EvidenceMergedNode(ResearchBaseNode):
    '''
    把两路重复的东西合成一份。
    '''

    async def __call__(self,state: InsightState) -> dict[str, Any]:
        agent_name = get_role_display_name(self.context.role)

        logger.info(f"{agent_name} 开始合并两通道检索证据")

        retrieved_records:list[RetrievedEvidence] = state.get('retrieved_records') or []
        # candidate 候选人 此处就是改变证据的形状
        records_by_id:dict[str, RetrievedEvidence] = _get_candidate_evidence(retrieved_records)
        relevance_scores:dict[str,float] = _compute_relevance_score(records_by_id.values()) # 各个通道的分数加起来

        logger.info(f"{agent_name} 合并两通道检索证据完成")

        return {
            'records_by_id': records_by_id,
            'relevance_scores': relevance_scores,
        }



