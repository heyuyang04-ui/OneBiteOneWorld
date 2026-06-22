from fastapi.responses import JSONResponse


ERROR_STATUS = {
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
}


def error_response(message: str, code: str = "BAD_REQUEST", status_code: int | None = None):
    return JSONResponse(
        status_code=status_code or ERROR_STATUS.get(code, 400),
        content={"success": False, "error": {"code": code, "message": message}},
    )
