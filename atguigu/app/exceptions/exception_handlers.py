from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

# exception 异常,例外
def register_exception_handlers(app: FastAPI):

    # Request 是 FastAPI 的请求对象，包含了前端发来的所有信息（URL、请求头、参数等）。
    # LookupError 找不到
    # JSONResponse 给前端发回一个 JSON 格式的响应
    # 这是在 app 上"登记"一条规则——以后遇到 LookupError，就调用下面那个函数来处理。
    @app.exception_handler(LookupError) # 以后有任何lookup问题就找他
    async def handle_lookup_error(_request: Request,exc:LookupError) -> JSONResponse:
        return JSONResponse(status_code=404,content={'detail': str(exc)})

    @app.exception_handler(ValueError)
    async def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400,content={'detail': str(exc)})

    @app.exception_handler(RuntimeError)
    async def handle_runtime_error(request: Request, exc: RuntimeError) -> JSONResponse:
        return JSONResponse(status_code=409,content={'detail': str(exc)})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f'出现未知异常 : {exc}')
        return JSONResponse(status_code=500,content={'detail': str(exc)})

