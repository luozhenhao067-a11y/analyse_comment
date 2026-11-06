from dataclasses import dataclass
from typing import Any

'''
因为这是 Host 自己用的“内部草稿”，不是给外人看的“正式文件”。

contract 文件夹：相当于公司的前台公告栏，放在这里的都是要给别的部门（比如报告引擎、前端）看的通用格式。

这两个类：只是 Host 自己在配对稿子时用的临时收纳盒。用完就扔了，别的部门根本不需要看。
'''


@dataclass(slots=True)
class AgentSectionOutput:
    """单个研究 Agent 发布的章节输出"""
    source: str  # 里面装啥：一个字符串，通常是 "insight" 或 "media"。
    section_key: str   # 章节唯一编码
    body: str

    @classmethod
    def from_section_ready_event(
            cls,
            event_payload:dict[str,Any]
    ) -> 'AgentSectionOutput':
        '''
        从章节就绪事件载荷构造 Agent 章节输出

        信封/快递单：上面的收件人、单号、系统类型，这叫头部（Header）。
        信封里面装的真正的东西（手机、衣服、文件）：这就是负载（Payload）。
        '''
        return cls(
            source=event_payload["source"],
            section_key=event_payload["section_key"],
            body=event_payload["body"]
        )


@dataclass(slots=True)
class AgentSectionPair:
    """同一章节的 Insight 与 Media 输出配对"""
    section_key: str
    title: str
    insight: AgentSectionOutput
    media: AgentSectionOutput
