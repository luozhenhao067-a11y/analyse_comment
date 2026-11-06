"""
它是"搜索总调度"：接到"用哪个工具、搜什么词"，去调对应的搜索，把搜到的网页标准化成统一格式的证据。
"""
import hashlib
from datetime import datetime
from urllib.parse import urlparse

from atguigu.engines.agent.media.tools.anspire_client import AnspireSearchClient
from atguigu.engines.agent.media.tools.base import SearchProviderResponse, BaseSearchClient
from atguigu.engines.agent.media.tools.catalog import SearchTool
from atguigu.engines.contract.evidence import SourceDocument, RetrievedEvidence

# 这里的provider是服务商
async def _search_webpage(tool_name:SearchTool, query:str) -> SearchProviderResponse:
    """按工具类型分派综合、溯源或实时检索"""

    client = AnspireSearchClient()

    match tool_name:
        case "source_search":
            return await client.source_search(query)
        case "realtime_search":
            return await client.realtime_search(query)
        case _:
            return await client.comprehensive_search(query)


def _extract_source_name(url:str) -> str:
    '''
    从网页url来提取来源域名

    urlparse(url) — 把一条完整 URL 拆成几部分：协议（scheme）、域名（netloc）、路径（path）等。
    .hostname — 取其中的主机名部分，并且会去掉端口号、转成小写。(www.example.com,news.sina.com.cn,api.github.com)
    '''
    return urlparse(url).hostname


def _extract_source_id(content:str) -> str:
    '''
    生成唯一标识
    '''
    raw_key = ' '.join(content.split())
    # .hexdigest() — 转成十六进制字符串，32 位，比如 d41d8cd98f00b204e9800998ecf8427e。
    return hashlib.md5(raw_key.encode('utf-8')).hexdigest()


def _extract_publish_at(date_text:str|None) -> datetime|None:
    if not date_text:
        return None
    # 这是 Python 里 datetime 模块的一个函数，作用是把符合 ISO 8601 格式的字符串，转换成 Python 的 datetime 对象。
    # .replace() 是 datetime 的方法，用来“替换”它的某个属性，返回一个新的 datetime 对象（原来的不变）。
    # tzinfo=None 表示把时区信息替换成“空”，也就是去掉时区。  time zone information
    # fromisoformat 只认标准的 ISO 8601 格式。 以防不标准 try一下
    try:
        return datetime.fromisoformat(date_text.strip()).replace(tzinfo=None)
    except ValueError:
        return None


def _map_to_evidence_records(response:SearchProviderResponse) -> list[RetrievedEvidence]:
    '''
    把搜到的网页，变成一条条带“身份证号”的记录，方便后面引用。
    '''

    records:list[RetrievedEvidence] = []
    for page in response.webpages:
        '''
        title: str  # 标题
        url: str  # 网址
        content: str  # 正文
        date: str | None  # 日期（可能没有）
        score: float  # 相关度分数
        '''
        content = page.content
        url = page.url
        records.append(
            RetrievedEvidence(
                document=SourceDocument(
                    platform=_extract_source_name(page.url),
                    source_type='webpage',
                    source_id=_extract_source_id(content),
                    content=content,
                    published_at=_extract_publish_at(page.date),
                    url=url,
                    title=page.title,
                ),
                channel_scores={"web_call": page.score}
            )
        )
    return records


async def retrieve_evidence(
        tool_name:SearchTool,
        query:str
) -> list[RetrievedEvidence]:
    '''
    按工具执行web检索并返回标准化证据
    '''

    response = await _search_webpage(tool_name,query)
    if response is None:
        return []
    return _map_to_evidence_records(response)


