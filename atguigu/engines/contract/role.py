from dataclasses import dataclass

from typing import Literal

RoleId = Literal['insight','media','host','report']

@dataclass(slots=True) # 固定卡槽了
class RoleMetadata:
    """
        定义不同角色Agent的元信息
    """
    # role = "media" → display_name = "媒体分析"
    llm_config_prefix:str
    display_name: str  # 中文展示名  给人类看的



ROLE_METADATA:dict[RoleId,RoleMetadata] = {
    "insight": RoleMetadata(llm_config_prefix="INSIGHT_AGENT", display_name="洞察"),
    "media": RoleMetadata(llm_config_prefix="MEDIA_AGENT", display_name="媒体"),
    "host": RoleMetadata(llm_config_prefix="HOST_AGENT", display_name="主持人"),
    "report": RoleMetadata(llm_config_prefix="REPORT_ENGINE", display_name="报告")
}

def get_role_display_name(role_id:RoleId) -> str: # 这里的role就是不同ai
    """返回角色的中文展示名"""
    return ROLE_METADATA[role_id].display_name