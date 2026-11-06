from pathlib import Path
from typing import Any

from atguigu.engines.common.task import task_manager
from atguigu.engines.common.utils import get_report_dir
from atguigu.engines.contract.role import RoleId
from atguigu.engines.report_engine.models import ReportInput

# 这是一个“查岗名单”（字典），
# 专门用来规定：最终生成报告之前，必须去硬盘里检查哪三个文件存没存好。
_EXPECTED_REPORT_FILES: dict[RoleId, str] = {
    "insight": "report.md",
    "media": "report.md",
    "host": "judgements.json"
}


def _get_expected_files(task_id:str) -> dict[RoleId,Path]:
    return {
        role: Path(get_report_dir(task_id,role)) / filename
        for role,filename in _EXPECTED_REPORT_FILES.items()
    }


def load_report_input(task_id:str) -> ReportInput:
    '''
    这个函数的核心功能就一句话：
    去硬盘上把三个文件里的文字全读出来，外加用户最初问的问题，打包成一个“大礼包”，准备喂给大模型。
    (把碎片拼成一篇完整的文章，排版好给老板看。)
    '''
    files = _get_expected_files(task_id)
    return ReportInput(
        query=task_manager.get_research_task(task_id).query,
        insight_report=files["insight"].read_text(encoding="utf-8"),
        media_report=files["media"].read_text(encoding="utf-8"),
        host_judgements=files["host"].read_text(encoding="utf-8")
    )

def get_report_input_status(task_id:str) -> dict[str, Any]:
    """检查所有必需角色的报告文件是否已就绪"""
    found_files = [
        f'{role}:{path.name}'
        for role,path in _get_expected_files(task_id).items()
        if path.exists()
    ]
    return {
        'task_id':task_id,
        'prepared': len(found_files) == len(_EXPECTED_REPORT_FILES), # 数量一样就算齐了
        'found_files':found_files
    }