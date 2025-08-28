
from fastapi import Query


def pagination_params(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> tuple[int, int]:
    return limit, offset
