"""SSE 实时事件流服务"""

import asyncio
import json

from loguru import logger

from atguigu.engines.contract.events import EventType, subscribe, unsubscribe

# 外部事件就是需要推送给前端的事件
class EventStream:
    """订阅外部事件，并通过 SSE 实时推送给在线客户端"""

    # 另外一个是内部的 无需推送前端
    FORWARDED_EVENT_TYPES = (
        EventType.EXTERNAL_RESEARCH_AGENT_PROGRESS,
        EventType.EXTERNAL_RESEARCH_AGENT_RESULT,
        EventType.EXTERNAL_HOST_DISCUSSION_MESSAGE
    )
    _event_queue:asyncio.Queue[str] = asyncio.Queue()

    def start(self):
        """向全局事件总线注册外部事件监听"""
        for i in self.FORWARDED_EVENT_TYPES:
            # 订阅就是把函数塞容器里
            subscribe(i,self._on_event)

        logger.info("EventStream：已启动SSE三种实时事件推送")

    def stop(self):
        '''注销事件监听'''
        unsubscribe(self._on_event)


    def _on_event(
            self,
            event_type: EventType,
            data: dict
    ):
        """将事件总线中的外部事件放入 SSE 队列"""
        payload = json.dumps({'event':event_type,'data':data} , ensure_ascii=False)
        # 发消息的人不能等
        # 如果放不了 马上会抛异常
        self._event_queue.put_nowait(payload)

    async def stream_events(self,request):
        """管理 SSE 客户端连接并持续推送实时事件"""
        logger.debug("SSE 客户端已连接")

        # 不写 event 键（默认）：数据直接进入浏览器自带的默认接口 onmessage。
        #
        # 写了 event 键（自定义）：数据进入专门为这个名字定制的接口 addEventListener('名字')
        yield {'event':'connected','data':json.dumps({'status':'connected'})}

        while not await request.is_disconnected():
            # 死循环拿负载
            payload = await self._event_queue.get()
            # 拿到马上发给前端
            yield {'data':payload}

        logger.debug("SSE 客户端已断开")

event_stream = EventStream()
