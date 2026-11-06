from fastapi import APIRouter

from atguigu.app.dependencies import SystemConfigServiceDep
from atguigu.app.schemas.system import SystemConfigResponse, SystemConfigRequest

router = APIRouter(prefix="/api/config", tags=["系统配置路由"])

@router.get("",response_model=SystemConfigResponse)
async def get_system_config_endpoint(service: SystemConfigServiceDep):
    # 在调用该函数时 service已经从dep变成SystemConfigService了
    config_info = service.get_system_config()
    return SystemConfigResponse(config_info)


# 路径相同（都是 /system/config），但 HTTP 方法不同（GET vs POST），
# FastAPI 视为两个独立接口，分别绑定不同的处理函数。
@router.post("")
async def update_system_config_endpoint(request:SystemConfigRequest,service: SystemConfigServiceDep):
    service.update_system_config(request.root)