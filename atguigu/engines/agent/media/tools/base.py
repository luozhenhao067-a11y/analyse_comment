"""Web 搜索 Provider 的契约：三个检索方法及其返回类型。"""


from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from atguigu.engines.infra.http import BaseHttpClient


# frozen=True = "冻结"这个对象，创建之后不能改——只读(搜索结果改鸡毛呢)
@dataclass(frozen=True, slots=True)
class WebpageResult:
    '''
    一条搜索结果长什么样
    '''
    title: str  # 标题
    url: str  # 网址
    content: str  # 正文
    date: str | None  # 日期（可能没有）
    score: float  # 相关度分数

# 该类是第一个类的汇总
@dataclass(frozen=True, slots=True)
class SearchProviderResponse:
    '''
    所有搜索工具搜完，都按这一个格式返回结果
    '''
    query:str
    # 如果没给这个字段传值，就默认给它一个空列表 [] (搜索结果集合)
    webpages:list[WebpageResult] = field(default_factory=list)

# 两个父类
# 一个"会发 HTTP 请求"的基类——封装了"上网请求"这件事，谁继承它，谁就会发请求。
class BaseSearchClient(BaseHttpClient,ABC):
    '''
    这是'网页搜索工具'的模板。只定规矩，不干实际活，谁想当搜索工具，就得照着它来。
    这个模板里有 3 个方法，名字就是之前那 3 个搜索工具的选项名，一模一样
    因为你没去实例化它。抽象方法不实现，只有"实例化"时才报错。
    '''

    @abstractmethod
    async def comprehensive_search(self, query: str) -> SearchProviderResponse:
        """综合检索某主题的全面公开媒体信息"""

    @abstractmethod
    async def source_search(self, query: str) -> SearchProviderResponse:
        """溯源检索可核查的原始网页出处"""

    @abstractmethod
    async def realtime_search(self, query: str) -> SearchProviderResponse:
        """实时检索最新报道与传播动态"""