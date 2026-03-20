import json
import pickle
from typing import Any, Optional, Union, List
import redis.asyncio as redis
from datetime import timedelta

from app.config import settings


class RedisClient:
    def __init__(self):
        self.client: redis.Redis = None
    
    async def connect(self):
        """Initialize Redis connection."""
        self.client = redis.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
    
    async def set(
        self, 
        key: str, 
        value: Union[str, dict, Any], 
        expire: Optional[int] = None
    ) -> bool:
        """Set a value in Redis."""
        if not self.client:
            await self.connect()
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        elif not isinstance(value, str):
            value = str(value)
        
        return await self.client.set(key, value, ex=expire)

    async def setex(
        self,
        key: str,
        seconds: int,
        value: Union[str, dict, Any],
    ) -> bool:
        """Set a value with TTL."""
        if not self.client:
            await self.connect()
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        elif not isinstance(value, str):
            value = str(value)
        
        return await self.client.setex(key, seconds, value)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis."""
        if not self.client:
            await self.connect()
        
        value = await self.client.get(key)
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys from Redis."""
        if not self.client:
            await self.connect()
        
        if not keys:
            return 0
        return await self.client.delete(*keys)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self.client:
            await self.connect()
        
        return await self.client.exists(key) > 0

    async def keys(self, pattern: str) -> List[str]:
        """List keys matching a pattern."""
        if not self.client:
            await self.connect()
        return await self.client.keys(pattern)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key."""
        if not self.client:
            await self.connect()
        
        return await self.client.expire(key, seconds)
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a value."""
        if not self.client:
            await self.connect()
        
        return await self.client.incrby(key, amount)
    
    async def set_session(self, session_id: str, user_data: dict, expire_hours: int = 24):
        """Store user session."""
        expire_seconds = expire_hours * 3600
        return await self.set(f"session:{session_id}", user_data, expire_seconds)
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get user session."""
        return await self.get(f"session:{session_id}")
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete user session."""
        return await self.delete(f"session:{session_id}")
    
    async def rate_limit_check(self, user_id: str, endpoint: str, limit: int = 100, window: int = 60) -> bool:
        """Check rate limit for user."""
        key = f"rate_limit:{user_id}:{endpoint}"
        current = await self.incr(key)
        
        if current == 1:
            await self.expire(key, window)
        
        return current <= limit
    
    async def cache_prediction(self, transaction_hash: str, prediction_data: dict, expire_minutes: int = 5):
        """Cache model prediction."""
        expire_seconds = expire_minutes * 60
        return await self.set(f"model_prediction:{transaction_hash}", prediction_data, expire_seconds)
    
    async def get_cached_prediction(self, transaction_hash: str) -> Optional[dict]:
        """Get cached model prediction."""
        return await self.get(f"model_prediction:{transaction_hash}")
    
    async def cache_analytics(self, date: str, metrics: dict, expire_minutes: int = 15):
        """Cache analytics data."""
        expire_seconds = expire_minutes * 60
        return await self.set(f"analytics:dashboard:{date}", metrics, expire_seconds)
    
    async def get_cached_analytics(self, date: str) -> Optional[dict]:
        """Get cached analytics data."""
        return await self.get(f"analytics:dashboard:{date}")


# Global Redis client instance
redis_client = RedisClient()
