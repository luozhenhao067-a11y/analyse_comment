"""
这个脚本定义了两个状态契约，用来告诉 LangGraph：图在跑的过程中，数据长什么样。
"""
from typing import TypedDict, TypeVar, Generic

# Type + Dict = "带类型的字典", 就是给字典规定好类型了
class SectionState(TypedDict,total=False):
    """每一章的样子"""
    section_key: str
    title: str
    body: str

# 这是一个"类型变量"，用来当"占位符"。
# SectionStateT 就是一个"还没定的类型"。SectionState 是一个基础形状
# 加个T 就是类型还不确定的变量
# bound 边界 SectionStateT 可以是 SectionState，也可以是 SectionState 的子类。但不能是别的
SectionStateT = TypeVar("SectionStateT",bound=SectionState)  # TypeVar 的第一个参数是名字，第二个参数是约束。

class ResearchGraphState(TypedDict,Generic[SectionStateT],total=False):
    '''
    TypedDict = 父类。

    Generic[SectionStateT] = 声明这个类里有个类型参数 SectionStateT

    total=False = 给 TypedDict 的参数。(total=True 所有字段必须有)

    Generic 到底干了什么？

    它做了一件事：

    "告诉 Python，这个类里有个类型参数。"

    你写 Generic[T]，Python 就知道：

    "Box 这个类里，有个类型叫 T。"

    T 是占位符，用的时候填。
    '''
    sections:list[SectionStateT]
    cursor:int
    final_report:str

