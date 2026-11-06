'''
从 MySQL 已有的主题标签里，选一个最符合用户问题的。
'''
import asyncio
from hmac import compare_digest
from typing import Any

from jupyter_builder.jupyterlab_semver import compare_loose
from typesafe_sdk import AsyncTypeSafeClient, Choice

from atguigu.engines.contract.context import ResearchBaseNode
from atguigu.engines.contract.config import get_config_settings
from atguigu.engines.agent.insight.state import InsightState
from atguigu.engines.agent.insight.tools.db.repository import list_topic_keys


# route 路线 选择路线
class TopicRouteNode(ResearchBaseNode):
    """读取 MySQL 事件标签，并用 Jev 选择本次研究范围"""

    async def __call__(self,state:InsightState) -> dict[str, Any]:
        topics = await list_topic_keys()  # topics 就是从数据库里读出来的一堆主题标签。

        topic_key = await select_topic(self.context.query,topics)        # topic_key 就是被选中的那个topic

        # 防止模型乱选
        if topic_key not in topics:
            raise ValueError("Insight 主题选择结果不在 MySQL主题中")

        return {'topic_key': topic_key}

async def select_topic(query:str, topics:list[str]) -> str:
    """用 Jev 从已有标签中选一个，返回已有标签"""
    # dict.fromkeys 是造一个字典，把传进来的东西当成键(键不重复)
    topic_keys = list(dict.fromkeys(topic.strip() for topic in topics if topic.strip()))
    if not topic_keys:
        raise ValueError("MySQL 中没有可供研究的主题")
    if len(topic_keys) == 1:
        return topic_keys[0]   # 只有一个 直接返回
    if len(topic_keys) > 255:
        raise ValueError(f"主题超过 Jev 单次选择上限")

    # 字典 { 主题x : 主题内容 }
    choices = {f'topic_{index}':topic for index,topic in enumerate(topic_keys)}

    async with AsyncTypeSafeClient(
            api_key=get_config_settings().TYPESAFE_API_KEY,
            model="jev-latest",
            timeout=30.0  # 服务器最多等你30秒
    ) as client:
        # client.system_one 是 TypeSafe 客户端里调用 System One 模型的方法。jev 是system one 类型的模型
        response = await client.system_one(
            state=query,  # state 当前已知的背景信息 / 上下文
            questions={
                # 'topic' —— 是你给这个问题起的名字。
                # Choice —— 这个是 TypeSafe 指定的。
                # 它是一个"问题类型"。
                # 意思是：这道题是选择题。
                'topic': Choice(
                    instructions="从候选主题中选出用户希望研究的一个主要主题。",  # 指令
                    criteria=choices  # 候选项(字典)
                )
            }
        )

    try:
        # response.choices 是响应里的"选择结果"部分
        # response.choices['topic'] 是取出里面叫 'topic' 的那一项。
        # 注意：这个 'topic' 就是你刚才在 questions 里起的那个键名
        # .choice 是再往里拿一层，拿出具体选中的那一个(键来的)
        selected = response.choices['topic'].choice

        # jev 提取的是键
        return choices[selected]
    # 因为写得太宽会掩盖真正的 bug。
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Jev 没有返回有效的事件标签") from exc # from exc 我抛出个 ValueError，但它是 exc 引起的(因为raise 之后，原来的 exc 会被丢掉)


if __name__ == '__main__':
    async def main_test():
        topics = await list_topic_keys()
        print(f"两个平台现有主题:{topics}")
        query = '高考'
        selected_topic = await select_topic(query,topics)
        print(selected_topic)

    asyncio.run(main_test())


