from typing import Annotated
from fastapi import Depends

from atguigu.app.services.system import SystemConfigService

def get_system_config_service() -> SystemConfigService:
    return SystemConfigService()

# 就是一个需要时才获取的对象
SystemConfigServiceDep = Annotated[SystemConfigService,Depends(get_system_config_service)]


