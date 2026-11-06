from pathlib import Path

from atguigu.engines.contract.role import RoleId
from atguigu.engines.contract.config import get_config_settings



'''
task_id 是干嘛的:
每次跑一次研究任务，都会有一个 task_id。它通常：

是唯一标识，比如 20261014_abc123

用来隔离不同任务的产物

让两次运行的结果不会互相覆盖
'''


def get_report_dir(task_id:str,role:RoleId) -> str:
    '''
    造存储地址
    '''
    config = get_config_settings()
    log_dir = config.RUNTIME_DIR
    return str(Path(log_dir) / f"{task_id}" / f"{role}" / "report.md")

def save_report(
        output_dir:str | Path,
        file_name:str,
        content:str,
) -> Path:
    """使用明确文件名将报告内容写入指定目录"""
    path = Path(output_dir) / file_name
    # path.parent 就是取这个路径的“上一级目录”，也就是父目录。
    path.parent.mkdir(parents=True, exist_ok=True)
    # .write_text(...)	Path 对象的方法，把文本写进这个文件
    path.write_text(content,encoding="utf-8")
    return path