import asyncio
import time

from fastapi import Request
from fastapi.responses import JSONResponse

from app.utils import BUCKET_CLEANUP_FREQ, setup_logger


logger = setup_logger(__name__)


class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        logger.info(
            f"Token Bucket Initialized with capacity: {capacity} | refill_rate: {refill_rate}",
            "MAGENTA",
        )

    def consume(self, tokens: int = 1) -> bool:

        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity, self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now


class RateLimitMiddleware:
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.buckets: dict[str, TokenBucket] = {}
        self.cleanup_task = None

    async def __call__(self, request: Request, call_next):
        if "_private" in str(request.url.path):
            # Whitelisting _private endpoints.
            # Otherwise even the request to reset them will be rate limited
            logger.info(f"Whitelisting: {request.url}", "CYAN")

            response = await call_next(request)
            return response

        client_ip = self._get_client_ip(request)

        if client_ip not in self.buckets:

            capacity = self.requests_per_minute
            refill_rate = self.requests_per_minute / 60.0
            self.buckets[client_ip] = TokenBucket(capacity, refill_rate)

        bucket = self.buckets[client_ip]

        if not bucket.consume():
            logger.warning("Rate limit exceeded!!")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later."
                },
            )

        self._schedule_cleanup()

        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get(
            "X-Forwarded-For", request.client.host
        )
        logger.info(f"Request from IP: {forwarded_for}")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "UNK"

    def _schedule_cleanup(self):
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_old_buckets())

    async def _cleanup_old_buckets(self):
        await asyncio.sleep(BUCKET_CLEANUP_FREQ)
        current_time = time.time()
        expired_ips = []

        for ip, bucket in self.buckets.items():
            if current_time - bucket.last_refill > BUCKET_CLEANUP_FREQ:
                expired_ips.append(ip)

        for ip in expired_ips:
            del self.buckets[ip]

    def reset_rate_limits(self, ip: str):
        if ip in self.buckets:
            capacity = self.requests_per_minute
            refill_rate = self.requests_per_minute / 60.0
            self.buckets[ip] = TokenBucket(capacity, refill_rate)
            logger.info(f"Rate limit reset for IP: {ip}", "BLUE")
