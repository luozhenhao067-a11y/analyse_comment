"""
它是"专门负责发网络请求"的工具类——你告诉它"发什么请求"，它帮你发出去，把结果拿回来。
它不管业务，只管"发请求"这一件事。
"""

from typing import Any, TypedDict

import httpx

# total=True 字段都必填
# TypedDict 就是这个类跟字典是一样的
class HttpRequestOptions(TypedDict,total=False):
    '''
    http 请求的参数类型
    '''

    headers: dict[str, str]
    params: dict[str, Any] # 网址后面的参数
    json: dict[str, Any]


class BaseHttpClient:
    '''
    BaseHttpClient = 一个专门帮人"上网请求数据"的工具类。谁继承它，谁就自动会发请求。
    '''

    @staticmethod
    def build_request_headers(api_key:str,*, accept: str = "application/json") -> dict[str, str]:
        '''
        类型 / 子类型
        application / json
        '''
        headers = {
            'Authorization': f'Bearer {api_key}', # 身份令牌
            'Content-Type': 'application/json', # 含义：告诉服务器，我这次发过去的数据是什么格式。
            'Accept': accept  # 含义：告诉服务器，我希望你返回什么格式。
        }
        return headers

    async def send_request(
            self,
            method: str,
            url: str,
            kwargs: HttpRequestOptions
    ) -> dict[str,Any]:
        '''
        用httpx异步发请求，返回json结果
        httpx 是 Python 里一个专门发 HTTP 请求的库——它就是干这个的，用它最方便
        '''
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=kwargs.get("headers"),
                params=kwargs.get("params"),
                json=kwargs.get("json")
            )
            response.raise_for_status()  # 里面就是if 失败就raise出来
            data = response.json()  # json() 是"把 JSON 转成 Python 对象"
        return data
