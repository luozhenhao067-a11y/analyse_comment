import asyncio
from typing import Any

from loguru import logger

from atguigu.engines.agent.host.graph import build_graph
from atguigu.engines.agent.host.section.pair_store import SectionPairStore
from atguigu.engines.agent.host.state import HostState
from atguigu.engines.common.task import task_manager
from atguigu.engines.contract.events import (
    EventType,
    publish_host_discussion_message,
    subscribe,
    unsubscribe
)

class SectionReadyListener:
    '''
    核心：监听"章节就绪"事件，排队消费，驱动 Host 图，播报讨论消息。
    '''

    def __init__(self):
        '''
        图 = "把流程画成一张图，节点是步骤，边是走向。"
        节点（node） = 一个步骤（干一件事）
        边（edge） = 下一步去哪
        状态（state） = 在各节点间传的数据
        '''
        self._graph = build_graph()
        self._host_states:dict[str,HostState] = {}
        '''
        "异步"体现在哪
        队列空的时候，await 会"挂着等"——不占 CPU、不空转，等有数据了自动醒来取。
        如果是普通队列：空了就得自己写循环去轮询（"有没有？没有？有没有？"），又蠢又费。
        '''
        self._event_queue:asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    def start(self):
        '''核心：开机——订阅事件 + 起个后台任务去消费'''
        subscribe(EventType.INTERNAL_SECTION_READY, self._enqueue_event)
        task_manager.create_background_task(self._process_events())

        logger.info("SectionReadyListener: 已启动 Host 章节研判")


    def stop(self):
        '''核心：关机——取消订阅事件并释放运行状态'''
        unsubscribe(self._enqueue_event)
        # 字典对象天生就有 clear() 方法，作用是清空字典里的所有键值对，让它变成空字典 {}。
        self._host_states.clear()

        logger.info("SectionReadyListener: 已停止 Host 章节研判")


    def _enqueue_event(self, _event_type:EventType,event_payload:dict[str, Any]):
        '''把事件数据塞进异步队列，但不等待(异步的作用主要是作用在get端的)'''
        # .put_nowait() 的意思是：立刻放进去，如果放不进去就报错，绝不等待
        # 1. await queue.put(item) —— 会等待
        # 如果队列没满，直接放进去，不等待。
        # 如果队列满了，当前协程会挂起，等别人从队列里取走一个，腾出空位，再把它放进去。
        # 这个“等待”是异步的：挂起期间，事件循环可以去跑别的协程，不会卡死整个程序。
        #
        # 2. queue.put_nowait(item) —— 不等待
        # 不管队列满没满，立刻尝试放。
        # 如果满了，直接抛 asyncio.QueueFull 异常。
        # 它不会挂起，不会等。
        self._event_queue.put_nowait(event_payload)


    async def _process_events(self):
        '''
        它是一个常驻的“后台工人”，
        不断从队列里取出“章节就绪”事件，
        用 LangGraph 跑一遍 Host 状态更新，
        然后把产生的讨论消息推出去。
        '''

        while True:
            # =================获取到数据=======================
            event_payload = await self._event_queue.get()

            # ==================内部用=====================
            task_id = event_payload["task_id"]
            host_state = self._host_states.setdefault(  # 这其实是get的功能
                task_id, # setdefault 返回的是字典里那个键对应的值，不是键本身。
                {
                    'task_id':task_id,
                    # 章节配对：在这个 AI 多智能体系统里，
                    # Insight 和 Media 两个 Agent 会分别写同一章的正文。
                    # Host 需要把这两份同章正文配对起来，才能进行研判。
                    'section_pair_store':SectionPairStore(),
                    'judgements':[]  # 这是一个空列表，用来存 Host 的研判结果
                }
            )

            updated_state:HostState = await self._graph.ainvoke(
                {
                    **host_state,
                    'event_payload':event_payload
                }
            )
            host_state['judgements'] = updated_state['judgements']
            discussion_events = updated_state['discussion_events']

            # ===========外部讨论区要展示【内部产生】=============
            for discussion_event in discussion_events:
                publish_host_discussion_message(discussion_event)


section_ready_listener = SectionReadyListener()








