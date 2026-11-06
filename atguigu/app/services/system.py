import os
from typing import Any

from dotenv import set_key

from atguigu.engines.contract.config import get_config_settings, ENV_FILE, reload_config_settings

# 只有这些名字的配置才能被改
ALLOWED_CONFIG_KEYS = [
    "DB_HOST", "DB_PORT", "DB_USER", "DB_NAME",
    "INSIGHT_AGENT_API_KEY", "INSIGHT_AGENT_BASE_URL", "INSIGHT_AGENT_MODEL_NAME", "INSIGHT_AGENT_MODEL_PROVIDER",
    "MEDIA_AGENT_API_KEY", "MEDIA_AGENT_BASE_URL", "MEDIA_AGENT_MODEL_NAME", "MEDIA_AGENT_MODEL_PROVIDER",
    "REPORT_ENGINE_API_KEY", "REPORT_ENGINE_BASE_URL", "REPORT_ENGINE_MODEL_NAME", "REPORT_ENGINE_MODEL_PROVIDER",
    "HOST_AGENT_API_KEY", "HOST_AGENT_BASE_URL", "HOST_AGENT_MODEL_NAME", "HOST_AGENT_MODEL_PROVIDER",
    "ANSPIRE_API_KEY", "ANSPIRE_BASE_URL"
]


'''
Router 接收请求，Schema 检查格式，
Service 负责把事情“做对、做好、做完整”，并且把数据按照业务逻辑处理妥当，最后交给 Router 响应给前端。
'''


def market_api_key(value_text:str) -> str:
    if not value_text:
        return value_text
    return f'****{value_text[-4:]}'


class SystemConfigService:

    def get_system_config(self) -> dict[str, Any]:
        '''
        从当前配置对象中，按白名单提取配置项，
        对敏感信息脱敏后，返回一个适合展示给前端的配置字典。
        :return:
        '''

        config_info:dict[str, Any] = {}
        config_settings = get_config_settings()

        for key in ALLOWED_CONFIG_KEYS:
            # 当属性名是变量、字符串、循环出来的，点号写不了，就要用 getattr
            value = getattr(config_settings, key, None)
            # 这里放空字符串是方便前端处理 免得前端还要判断
            value_text = value if value is not None else ""

            if key.endswith("_API_KEY"):  # 如果改的是某个api_key,得挡一下
                value_text = market_api_key(value_text)

            config_info[key] = value_text

        # 提取到白名单内的配置项
        return config_info

    def update_system_config(self, update_config_info:dict[str, Any]):
        '''
        将字典中最新的key对应的value值写入到【ConfigSettings or .env文件中
        接着reload_config_settings】
        :param config_info:
        :return:
        '''
        # 找到所有不在白名单上的keys
        unknown_keys = [key for key in update_config_info if key not in ALLOWED_CONFIG_KEYS]

        if unknown_keys:
            raise ValueError(f'unknown keys: {','.join(unknown_keys)}')

        for key, value in update_config_info.items():
            # quote_mode 写入 .env 文件时，值两边要不要加引号。
            set_key(ENV_FILE,key, value,quote_mode='never')
            # 表示当前 Python 进程的环境变量的对象,用法想字典,所以此处直接字典方法改
            # 因为 Python 里“像字典”不是 dict 的专利。
            # 只要一个对象实现了字典需要的那几个“魔术方法”，它就能用 []、get()、in、del 这些语法。
            os.environ[key] = value

        # 清空缓存 重新实例化一个放进缓存
        reload_config_settings()

