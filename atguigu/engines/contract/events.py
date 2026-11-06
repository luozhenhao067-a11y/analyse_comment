from enum import Enum
from typing import Any, Callable, Literal, Mapping

from loguru import logger
from pydantic import BaseModel

from atguigu.engines.contract.judgement import SectionJudgement
from atguigu.engines.contract.role import RoleId, get_role_display_name

'''
Python 支持多继承，str 和 Enum 都是父类。
str → 让它本质是字符串
Enum → 让它成为枚举（值固定、不能乱加）
'''
class EventType(str, Enum):
    """把"有哪些事件类型"固定下来，防止拼错、方便引用"""

    INTERNAL_SECTION_READY = "internal_section_ready" # 内部_章节就绪
    EXTERNAL_HOST_DISCUSSION_MESSAGE = "external_host_discussion_message" # 外部_主持人讨论消息
    EXTERNAL_RESEARCH_AGENT_PROGRESS = "external_research_agent_progress" # 外部_研究代理进度
    EXTERNAL_RESEARCH_AGENT_RESULT = "external_research_agent_result" # 外部_研究代理结果


class SectionReadyEvent(BaseModel):  # 自动校验
    '''这是"章节就绪事件"的数据结构——某章写完时，发的通知长啥样'''
    task_id: str      # 哪个任务
    source: str       # insight/media
    section_key: str  # 哪一章
    body: str         # 正文内容


class HostDiscussionMessageEvent(BaseModel):
    '''这是"Host 讨论消息"事件——Host 对外发的一条讨论消息长啥样'''
    task_id: str
    source: Literal["insight", "media", "host"]
    content: str
    section_key: str
    judgement: SectionJudgement | None = None  # 研判结果

# [EventType, dict[str, Any]] → 收两个参数：事件类型、数据字典
# None → 不返回值
# 回调函数的本质:把"函数"当"参数"传给别人，让别人在合适的时候调它
EventCallback = Callable[[EventType, dict[str, Any]], None]
# {
#     事件类型1: {回调A, 回调B},
#     事件类型2: {回调C},
# }
_subscribers: dict[EventType, set[EventCallback]] = {}


# 订阅的本质是把函数放容器里 需要时调用
def subscribe(event_type:EventType,callback:EventCallback):
    '''把回调函数登记到"这个事件类型"的订阅名单里'''
    # 此处用集合 因为要去重——同一个函数别订阅两次。
    # setdefault 是字典（dict）自带的方法 取某个键的值；键不存在，就先塞个默认值进去，再返回
    _subscribers.setdefault(event_type,set()).add(callback)

def publish(event_type:EventType,data:dict[str,Any]): # 发布任何事件
    '''向订阅者发布数据(发布的本质就是执行那个回调函数)'''
    for callback in _subscribers.get(event_type,set()):
        try:
            callback(event_type,data)
        except Exception as exc:
            logger.error(f"事件订阅者执行失败：{exc}")


def unsubscribe(callback:EventCallback):
    '''从订阅名单里把回调函数移除'''
    # 因为"不是每个组里都有它"，用 discard 才不会报错。
    # discard → 有就删，没有就算了，不报错
    # remove → 有就删，没有就抛异常
    for subscribers in _subscribers.values():
        subscribers.discard(callback)


def publish_section_ready(      # 发章节就绪事件专用
        section: Mapping[str,Any],
        role:RoleId,
        task_id:str
):
    '''
    造事件：用 section、role、task_id 拼成 SectionReadyEvent
    发布：publish(...) 发出去，通知订阅者
    记日志：打印"哪章就绪了"
    '''
    agent_name = get_role_display_name(role)
    event = SectionReadyEvent(
        task_id=task_id,
        source=role,
        section_key=section["section_key"],
        body=section["body"]
    )

    # model_dump 是 Pydantic 的 BaseModel 自带的方法。 作用：把对象转成字典。
    publish(EventType.INTERNAL_SECTION_READY, event.model_dump())
    logger.info(f"【章节就绪 · {agent_name}】章节={event.section_key} 内容={event.body[:20]}...")


def publish_host_discussion_message(event:HostDiscussionMessageEvent):
    '''发布主持人讨论消息事件'''
    publish(EventType.EXTERNAL_HOST_DISCUSSION_MESSAGE,event.model_dump())
    speaker = get_role_display_name(event.source)
    logger.info(f"【讨论区 · {speaker}】章节={event.section_key} 内容={event.content[:20]}...")
