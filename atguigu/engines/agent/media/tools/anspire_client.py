import datetime
from typing import Any
from loguru import logger

from atguigu.engines.agent.media.tools.base import (
    BaseSearchClient,
    SearchProviderResponse,
    WebpageResult
)
from atguigu.engines.common.retryer import with_retry
from atguigu.engines.contract.config import get_config_settings

# 权威来源
AUTHORITATIVE_SOURCES = (
    "www.gov.cn,"
    "news.cn,"
    "xinhuanet.com,"
    "people.com.cn,"
    "news.cctv.com,"
    "chinanews.com.cn"
)
# 社媒来源
SOCIAL_SOURCES = "weibo.com,zhihu.com,toutiao.com"

class AnspireSearchClient(BaseSearchClient):
    '''
    Anspire 搜索客户端
    '''

    def __init__(self):
        '''
        读取Anspire密钥与地址并构建请求头
        '''
        super().__init__()
        self.api_key = get_config_settings().ANSPIRE_API_KEY
        self.base_url = get_config_settings().ANSPIRE_BASE_URL
        self.headers = self.build_request_headers(self.api_key)

    # comprehensive = "全都抓住、一个不漏" —— 铺开一张大网，把方方面面都罩进去。
    async def comprehensive_search(self,query:str) -> SearchProviderResponse:
        '''
        全面搜索,涵盖权威来源和社媒来源,不限站点
        '''
        return await self._execute_search(query=query,top_k=15)

    async def source_search(self,query:str) -> SearchProviderResponse:
        '''
        溯源搜索,仅限权威来源
        '''
        return await self._execute_search(query=query,top_k=10,insite=AUTHORITATIVE_SOURCES)

    async def realtime_search(self,query:str) -> SearchProviderResponse:
        '''
        实时搜索,仅限近一周社媒来源
        '''
        to_time = datetime.datetime.now()
        # delta:变化量,差值
        from_time = to_time - datetime.timedelta(weeks=1)
        return await self._execute_search(
            query=query,
            top_k=5,
            insite=SOCIAL_SOURCES,
            from_time=from_time.strftime("%Y-%m-%d %H:%M:%S"),
            to_time=to_time.strftime("%Y-%m-%d %H:%M:%S")
        )

    @with_retry
    async def _execute_search(
            self,
            query: str,
            top_k: int,
            insite: str = None,
            from_time: str = None,
            to_time: str = None,
    ) -> SearchProviderResponse:
        '''
        拼好网址参数，用 GET 方式把请求发出去，再把对方返回的东西解析出来。
        '''

        params = {
            "query": query,
            "top_k": top_k,
            "Insite": insite,
            "FromTime": from_time,
            "ToTime": to_time
        }

        response = await self.send_request(
            "GET",
            self.base_url,
            {'headers':self.headers,'params':params}
        )

        # process 加工处理
        return self._process_response(response,query)

    @staticmethod
    def _process_response(response_dict:dict[str,Any],query:str) -> SearchProviderResponse:
        '''
        将 Anspire 原始结果映射为网页模型
        '''

        results = response_dict.get('results')
        # webpages 是一个"列表"，里面装着一堆"网页结果"；= [] 表示默认是个空列表。
        webpages: list[WebpageResult] = []

        for result in results:
            webpages.append(
                # "网页对象" = 用一个 Python 对象，来表示"一条网页搜索结果"。
                WebpageResult(
                    title=result.get("title"),  # ① 标题
                    url=result.get("url"),  # ② 网址
                    content=result.get("content"),  # ③ 正文
                    date=result.get("date"),  # ④ 日期
                    score=result.get("score")  # ⑤ 相关度分数
                )
            )

        return SearchProviderResponse(
            query=query,
            webpages=webpages
        )

