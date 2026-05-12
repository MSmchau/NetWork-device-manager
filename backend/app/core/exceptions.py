from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

class BusinessError(Exception):
    """业务异常：可预知的错误，如资源不存在、参数冲突"""
    def __init__(self, code: int = 400, message: str = "业务错误"):
        self.code = code
        self.message = message

def register_exception_handlers(app):
    """注册全局异常处理器"""
    @app.exception_handler(BusinessError)
    async def business_error_handler(request: Request, exc: BusinessError):
        return JSONResponse(
            status_code=exc.code,
            content={"code": exc.code, "message": exc.message, "data": None},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        first = errors[0] if errors else {}
        msg = first.get("msg", "参数校验失败")
        return JSONResponse(
            status_code=422,
            content={"code": 422, "message": msg, "data": {"details": errors}},
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务器内部错误", "data": None},
        )
