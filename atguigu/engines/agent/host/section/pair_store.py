from atguigu.engines.agent.host.section.output import AgentSectionOutput, AgentSectionPair
from atguigu.engines.contract.section import SECTION_DEFINITIONS

_REQUIRED_SOURCES = ("insight", "media")

class SectionPairStore:
    """管理双数据源的章节输出数据，并筛选出满足研判条件的章节数据对。"""

    def __init__(self):
        '''
        初始化章节输出于研判状态存储
        '''
        # 存储所有收到的 Agent 章节输出数据
        self._outputs_by_section:dict[str,dict[str,AgentSectionOutput]] = {}
        # 专门用来存储已经完成研判的章节 ID
        self._judged_sections:set[str] = set()


    def store_output(self, output: AgentSectionOutput):
        """按章节与来源保存 Agent 输出"""
        self._outputs_by_section.setdefault(output.section_key,{})[output.source] = output


    def get_ready_pair(self) -> AgentSectionPair|None:
        """按固定章节顺序返回首个待研判配对；若暂无则返回 None"""
        for section_key in SECTION_DEFINITIONS:
            if self._is_pair_ready(section_key):
                return self._build_section_pair(section_key)
        return None


    def _is_pair_ready(self, section_key:str) -> bool:
        '''判断指定章节的双 Agent 输出是否齐备且待研判'''
        # 指定章节（section_key）下，已经收到的所有 Agent 交上来的稿子
        outputs = self._outputs_by_section.get(section_key,{})
        # all() 的意思是“全都要是真的”。只要里面有一个是假（False），它就立刻摇头说“不行（False）”；
        # 只有里面全都是真，它才点头说“行（True）”。
        # 还未完成研判 + (两个研究员都交卷了)
        return section_key not in self._judged_sections and all(
            source in outputs for source in _REQUIRED_SOURCES
        )

    def _build_section_pair(self, section_key:str) -> AgentSectionPair:
        """根据指定章节的双 Agent 输出构建章节配对"""

        outputs = self._outputs_by_section[section_key]
        return AgentSectionPair(
            section_key=section_key,
            # section_key 长什么样？
            # 在你发的这个文件里，section_key 就是最左边那五个大写的常量名，它们都是字符串（str）。长这样：
            #
            # "BACKGROUND_OVERVIEW" （事件背景与概览）
            #
            # "HEAT_AND_SPREAD" （舆情热度与传播）
            #
            # "SENTIMENT_AND_OPINION" （公众情感与观点）
            #
            # "PLATFORM_AND_GROUP_DIFF" （平台与群体差异）
            #
            # "DEEP_CAUSES_AND_IMPACT" （深层原因与影响）
            title=SECTION_DEFINITIONS[section_key].title,  # 指出是哪一章节
            insight=outputs["insight"],
            media=outputs["media"]
        )

    def mark_judged(self,section_key:str):
        '''标记指定章节已完成研判'''
        self._judged_sections.add(section_key)


