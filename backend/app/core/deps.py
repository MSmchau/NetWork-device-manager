from fastapi import Query

def common_pagination(page: int = Query(1, ge=1, description="页码"),
                      page_size: int = Query(20, ge=1, le=200, description="每页条数")):
    """分页查询依赖"""
    return {"page": page, "page_size": page_size, "skip": (page - 1) * page_size}
