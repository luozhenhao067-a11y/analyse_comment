import uvicorn
from atguigu.engines.contract.config import get_config_settings

if __name__ == "__main__":
    config = get_config_settings()
    # 当前文件在atguigu这个包下面
    uvicorn.run(app='app.app:app',host=config.HOST,port=config.PORT)