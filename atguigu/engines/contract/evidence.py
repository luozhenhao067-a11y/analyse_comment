from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

ENGAGEMENT_FIELDS = ("likes", "comments", "shares", "collects", "replies")


def build_doc_id(platform:str, source_type:str, source_id:str) -> str:
    return f'{platform}:{source_type}:{source_id}'

@dataclass(slots=True)   # slot 游戏机卡槽   DataClass 就是一个“死板的表格”，只负责把数据整整齐齐地存进去。
class SourceDocument:
    """
        Insight 与 Media 共用的文档对象[检索结果的归一化]。
        source_type 是 platform 之下的来源细分，与 source_id 一起构成 doc_id：
        Insight 填采集表名(douyin_aweme / douyin_aweme_comment ...)，Media 固定 "webpage"。
        hotness 是互动量的加权和，无上界，不是归一化分数；Media 侧没有互动数据，保持为 0。
    """

    # 侧重的 Insight 从本地上检索到的结果做映射(内部档案)
    platform:str
    source_type:str # 来源类型
    source_id:str
    content:str
    published_at:datetime|None
    engagement_counts:dict[str,float]=field(default_factory=dict)
    hotness:float=0.0

    # 侧重的 Media 从网络上检索到的结果做映射(外部线报)
    url:str=''
    title:str=''

    @property  # @property 的意象就是：“把方法伪装成属性”  property 资产
    def doc_id(self) -> str:
        return build_doc_id(self.platform,self.source_type,self.source_id)


@dataclass(slots=True)
class RetrievedEvidence:  # Retrieve 最核心、最原始的画面是：“猎犬把扔出去的猎物，精准地叼回来
    """
        被某次召回命中、作为证据。

        channel_scores 以召回通道为键。Insight 两路(db_call / vector_call)存的是检索
        服务自己按名次换算的 1/rank，并非通道原始分——MySQL 没有相关度分数，Milvus 的
        余弦距离也刻意不采用；Media(web_call)存的是搜索 Provider 返回的分数。两者分属
        独立流水线，不会放在一起比较。
    """

    document:SourceDocument
    channel_scores:dict[str,float]=field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.document.doc_id

def render_evidence_context(records: list[RetrievedEvidence]) -> str:
    '''
    把一堆证据文字块，拼成一段文本，塞进提示词里喂给 LLM
    '''
    return '\n\n'.join(_render_evidence_records(records))


def _render_content(content:str,max_length:int = 3000) -> str:
    '''
    确保内容3000字内
    '''
    if len(content) > max_length:
        return content[:max_length] + '...'
    else:
        return content


def _render_published_at(published_at:datetime|None) -> str:
    '''
    规范化时间
    '''
    if published_at:
        # 把 datetime 对象，格式化成"年-月-日 时:分:秒"的字符串
        return published_at.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return ""


def _render_engagement(engagement_counts:dict[str,Any]) -> str:
    '''
    互动数据格式化并拼接
    '''
    values = (
        ("点赞", engagement_counts.get('likes')),
        ("评论", engagement_counts.get('comments')),
        ("转发", engagement_counts.get('shares')),
        ("收藏", engagement_counts.get('collects')),
        ("回复", engagement_counts.get('replies')),
    )
    return ' / '.join(f'{label}:{value}' for label, value in values)


def _render_evidence_record(record:RetrievedEvidence, evidence_number:int) -> str:
    '''
    将单条证据变成格式块
    '''
    document = record.document
    # 元组套元组 因为这几个字段是"定死的、不会改的"，元组正合适。
    fields = (
        ("证据ID", document.doc_id),
        ("平台/站点", document.platform),
        ("来源类型", document.source_type),
        ("标题", document.title),
        ("内容", _render_content(document.content)),
        ("发布时间", _render_published_at(document.published_at)),
        ("来源链接", document.url),
        ("互动数据", _render_engagement(document.engagement_counts) if document.engagement_counts else "")
    )

    lines = [f'[证据{evidence_number}]']  # 这是第一行
    # append(x) → 把 x 当整体塞进去
    # extend(一堆) → 把一堆拆开，一个个加进去
    lines.extend([f'{label}: {value}' for label,value in fields])
    return '\n'.join(lines)




def _render_evidence_records(records: list[RetrievedEvidence]) -> list[str]:
    '''
    把每条证据，渲染成"带编号的文字块"，返回一堆文字块。
    '''
    return [
        _render_evidence_record(record,evidence_number)
        for evidence_number, record in enumerate(records, start=1)
    ]






