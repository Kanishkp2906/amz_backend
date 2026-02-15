import redis
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config import REDIS_URL

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

class RedisRateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, limit=6, window=60):
        super().__init__(app)
        self.limit = limit
        self.window = window

    async def dispatch(self, request: Request, call_next):
        
        if request.method == "OPTIONS":
            return await call_next(request)

        try:
            user_uuid = request.cookies.get("user_session")
            if user_uuid:
                redis_key = f"ratelimiting:{user_uuid}"
                redis_count = redis_client.get(redis_key)

                if redis_count is None:
                    redis_client.setex(redis_key, self.window, 1)
                elif int(redis_count) <= self.limit:
                    redis_client.incr(redis_key)
                else:
                    ttl = redis_client.ttl(redis_key)
                    return JSONResponse(
                        status_code=429,
                        content={
                            "message": f"Rate limit exceeded. Try after {ttl} seconds."
                        },
                    )
            
        except Exception as e:
            # Now this will only print REAL Redis errors
            print(f"Error in rate limiting: {e}")

        return await call_next(request)
