from fastapi import Header, HTTPException

async def get_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """
    Dependency to get and validate API key from headers
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="X-API-Key header is required"
        )
    return x_api_key