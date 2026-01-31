from fastapi import FastAPI
from routes import router
from database import Base, engine
from middleware.app_cors import add_cors_middleware
from middleware.rate_limiter import RedisRateLimiter

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AMZ Price Tracker")

app.add_middleware(RedisRateLimiter)
add_cors_middleware(app)
app.include_router(router)
