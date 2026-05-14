from typing import Any
from datetime import datetime, date
from fastapi.responses import JSONResponse
from pydantic import BaseModel

def _serialize(data: Any) -> Any:
    """递归将 Pydantic 模型转为可 JSON 序列化的字典。"""
    if isinstance(data, BaseModel):
        return data.model_dump(mode="json")
    if isinstance(data, dict):
        return {k: _serialize(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [_serialize(item) for item in data]
    if isinstance(data, (datetime, date)):
        return data.isoformat()
    return data

def success(data: Any = None, message: str = "ok") -> JSONResponse:
    """统一成功响应"""
    return JSONResponse(content={"code": 0, "message": message, "data": _serialize(data)})

def error(code: int = 400, message: str = "请求失败", data: Any = None) -> JSONResponse:
    """统一错误响应"""
    return JSONResponse(status_code=code, content={"code": code, "message": message, "data": _serialize(data)})

def paginated(items: list, total: int, page: int, page_size: int) -> JSONResponse:
    """统一分页响应"""
    return JSONResponse(content={
        "code": 0,
        "message": "ok",
        "data": {
            "items": _serialize(items),
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    })
