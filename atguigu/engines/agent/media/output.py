from pydantic import BaseModel, Field

from atguigu.engines.agent.media.tools.catalog import SearchTool



class MediaSearchPlanItem(BaseModel):
    """
    规定 LLM 在"搜索规划"这一步必须返回什么格式的结果
    """

    # Field(...) 就是用来写这些填写要求/备注的。
    search_tool:SearchTool = Field(
        description=(
            "从提供的可用搜索工具中为当前索引章节选择一个工具"
            "根据章节 title、section_guidance 和工具描述进行匹配,不得假设工具具备描述之外的能力。"
        )
    )

    search_keywords:list[str] = Field(
        min_length=1,
        max_length=3,
        description=(
            "字符串数组,包含当前索引章节使用的 1-3 个中文补充查询短语,每个查询短语只表达一个明确检索侧重点,供后续形成一次独立搜索。"
            "不要使用同义重复、宽泛空词、完整问句"
        )
    )


class MediaSearchPlanOutput(BaseModel):
    '''
    这是给 AI 定的一张"答题卡模板"——规定 AI 最后必须交出一份"正好 5 章、顺序不变、每章一份搜索计划"的答案
    '''

    sections:list[MediaSearchPlanItem] = Field(
        min_length=5,
        max_length=5,
        description=(
            "按用户提供的章节职责列表原始顺序生成的 5 项搜索计划;"
            "每项与索引章节一一对应,不得增删或重排。"
        )
    )