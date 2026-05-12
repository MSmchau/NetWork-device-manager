from typing import Any
from fastapi.responses import JSONResponse

def success(data: Any = None, message: str = "ok") -> JSONResponse:
    """统一成功响应"""
    return JSONResponse(content={"code": 0, "message": message, "data": data})

def error(code: int = 400, message: str = "请求失败", data: Any = None) -> JSONResponse:
    """统一错误响应"""
    return JSONResponse(status_code=code, content={"code": code, "message": message, "data": data})

def paginated(items: list, total: int, page: int, page_size: int) -> JSONResponse:
    """统一分页响应"""
    return JSONResponse(content={
        "code": 0,
        "message": "ok",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    })
