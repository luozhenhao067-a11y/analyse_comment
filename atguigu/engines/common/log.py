"""
自定义日志处理器(记录到日志文件中[日志格式：时间日期、日志级别、模块、内容])
insight---->insight.log
media--->media.log
loguru完成
"""
from contextlib import contextmanager

from loguru import logger
from pathlib import Path
from atguigu.engines.contract.config import PROJECT_ROOT


'''
@contextmanager 是把一个函数变成"上下文管理器"。

上下文管理器 = 能用 with 的东西。
'''

@contextmanager
def execute_logger(role:str):
    log_dir = PROJECT_ROOT / 'VAR'
    # 先有地址 再makedir
    log_dir.mkdir(parents=True, exist_ok=True)
    '''
    contextualize 是 loguru 日志库的一个方法，
    作用是：给接下来的一段代码，临时绑定一些额外信息，让这段代码里打的所有日志都自动带上这些信息
    '''
    with logger.contextualize(role=role):
        # logger.add 是 loguru 日志库的方法，作用是注册一个日志输出目标（sink）。
        # logger.add() 每注册一个输出目标，就会返回一个编号，这个编号就是 handler_id。
        try:
            handler_id = logger.add(
                str(Path(log_dir) / f'{role}.log'),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | 【{extra[role]}】 {name} - {message}",
                level='INFO',
                encoding='utf-8',
                # rotation='1 MB' 是 loguru 日志库里的参数，用来控制日志文件自动切割（轮转）。
                # 含义
                # 当日志文件大小达到 1 MB 时，就会自动：
                # 把当前的日志文件重命名（通常加上时间戳或序号）
                # 新建一个空的日志文件继续写入
                # 这样可以防止单个日志文件无限变大。
                rotation='1 MB',  # 是 loguru 日志库里的参数，用来控制日志文件自动切割（轮转)
                # loguru 每条日志都有一个 extra 字典，用来存放你通过 logger.contextualize() 或 logger.bind() 绑定的额外信息。
                filter = lambda record: record["extra"].get("role") == role
            )
            yield
        finally:
            logger.remove(handler_id)  # 把刚才注册的日志处理器删掉。

if __name__ == '__main__':
    with execute_logger(role='insight'):
        logger.info('hello3')