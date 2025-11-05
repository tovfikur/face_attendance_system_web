"""Redis client and caching service."""

import json
import logging
from typing import Any, Optional

import redis
from redis import ConnectionPool, Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper for caching and session management."""

    _instance: Optional["RedisClient"] = None
    _redis: Optional[Redis] = None

    def __new__(cls) -> "RedisClient":
        """Singleton pattern for Redis client."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            # Parse Redis URL
            pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            self._redis = Redis(connection_pool=pool)

            # Test connection
            self._redis.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None

    @property
    def client(self) -> Optional[Redis]:
        """Get Redis client."""
        if self._redis is None:
            self._initialize()
        return self._redis

    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        try:
            if self.client:
                self.client.ping()
                return True
        except Exception:
            pass
        return False

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if not self.client:
                return None

            value = self.client.get(key)
            if value is None:
                return None

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        try:
            if not self.client:
                return False

            # Serialize value
            if not isinstance(value, str):
                try:
                    serialized = json.dumps(value)
                except (TypeError, ValueError):
                    serialized = str(value)
            else:
                serialized = value

            # Set with TTL
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if not self.client:
                return False

            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if not self.client:
                return False

            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Error checking key {key} in Redis: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            if not self.client:
                return 0

            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.error(f"Error clearing pattern {pattern} from Redis: {e}")
            return 0

    async def get_ttl(self, key: str) -> int:
        """Get remaining TTL for key in seconds."""
        try:
            if not self.client:
                return -2

            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -2

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter value."""
        try:
            if not self.client:
                return None

            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {e}")
            return None

    async def append(self, key: str, value: str) -> bool:
        """Append value to string."""
        try:
            if not self.client:
                return False

            self.client.append(key, value)
            return True
        except Exception as e:
            logger.error(f"Error appending to key {key}: {e}")
            return False

    async def list_push(self, key: str, value: Any) -> bool:
        """Push value to list."""
        try:
            if not self.client:
                return False

            if not isinstance(value, str):
                value = json.dumps(value)

            self.client.rpush(key, value)
            return True
        except Exception as e:
            logger.error(f"Error pushing to list {key}: {e}")
            return False

    async def list_get(self, key: str, start: int = 0, end: int = -1) -> list[Any]:
        """Get values from list."""
        try:
            if not self.client:
                return []

            values = self.client.lrange(key, start, end)
            result = []

            for value in values:
                try:
                    result.append(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    result.append(value)

            return result
        except Exception as e:
            logger.error(f"Error getting list {key}: {e}")
            return []

    async def list_clear(self, key: str) -> bool:
        """Clear a list."""
        try:
            if not self.client:
                return False

            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error clearing list {key}: {e}")
            return False

    async def hash_set(self, key: str, mapping: dict[str, Any]) -> bool:
        """Set hash values."""
        try:
            if not self.client:
                return False

            # Serialize values
            serialized = {}
            for k, v in mapping.items():
                if not isinstance(v, str):
                    try:
                        serialized[k] = json.dumps(v)
                    except (TypeError, ValueError):
                        serialized[k] = str(v)
                else:
                    serialized[k] = v

            self.client.hset(key, mapping=serialized)
            return True
        except Exception as e:
            logger.error(f"Error setting hash {key}: {e}")
            return False

    async def hash_get(self, key: str, field: str) -> Optional[Any]:
        """Get hash field value."""
        try:
            if not self.client:
                return None

            value = self.client.hget(key, field)
            if value is None:
                return None

            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Error getting hash field {key}:{field}: {e}")
            return None

    async def hash_get_all(self, key: str) -> dict[str, Any]:
        """Get all hash values."""
        try:
            if not self.client:
                return {}

            data = self.client.hgetall(key)
            result = {}

            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = v

            return result
        except Exception as e:
            logger.error(f"Error getting all hash {key}: {e}")
            return {}


# Global Redis client instance
redis_client = RedisClient()


class CacheService:
    """High-level caching service with domain-specific methods."""

    # Cache key prefixes
    DETECTION_PREFIX = "detection:"
    CAMERA_PREFIX = "camera:"
    USER_PREFIX = "user:"
    SESSION_PREFIX = "session:"

    # Cache TTLs
    LIVE_DETECTIONS_TTL = 3  # 3 seconds for live data
    CAMERA_STATE_TTL = 60  # 1 minute
    STATISTICS_TTL = 300  # 5 minutes
    SESSION_TTL = 86400  # 24 hours

    def __init__(self):
        """Initialize cache service."""
        self.redis = redis_client

    async def cache_live_detections(self, camera_id: str, detections: list[dict]) -> bool:
        """Cache live detections for a camera."""
        key = f"{self.DETECTION_PREFIX}live:{camera_id}"
        return await self.redis.set(
            key,
            {
                "detections": detections,
                "timestamp": str(__import__("datetime").datetime.utcnow()),
                "count": len(detections),
            },
            ttl=self.LIVE_DETECTIONS_TTL,
        )

    async def get_cached_live_detections(self, camera_id: str) -> Optional[dict]:
        """Get cached live detections for a camera."""
        key = f"{self.DETECTION_PREFIX}live:{camera_id}"
        return await self.redis.get(key)

    async def clear_live_detections(self, camera_id: str) -> bool:
        """Clear live detections cache for a camera."""
        key = f"{self.DETECTION_PREFIX}live:{camera_id}"
        return await self.redis.delete(key)

    async def cache_detection_statistics(self, stats_key: str, stats: dict) -> bool:
        """Cache detection statistics."""
        key = f"{self.DETECTION_PREFIX}stats:{stats_key}"
        return await self.redis.set(key, stats, ttl=self.STATISTICS_TTL)

    async def get_cached_statistics(self, stats_key: str) -> Optional[dict]:
        """Get cached detection statistics."""
        key = f"{self.DETECTION_PREFIX}stats:{stats_key}"
        return await self.redis.get(key)

    async def cache_camera_state(self, camera_id: str, state: dict) -> bool:
        """Cache camera state."""
        key = f"{self.CAMERA_PREFIX}state:{camera_id}"
        return await self.redis.set(key, state, ttl=self.CAMERA_STATE_TTL)

    async def get_cached_camera_state(self, camera_id: str) -> Optional[dict]:
        """Get cached camera state."""
        key = f"{self.CAMERA_PREFIX}state:{camera_id}"
        return await self.redis.get(key)

    async def cache_session(self, session_id: str, session_data: dict) -> bool:
        """Cache user session."""
        key = f"{self.SESSION_PREFIX}{session_id}"
        return await self.redis.set(key, session_data, ttl=self.SESSION_TTL)

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get user session from cache."""
        key = f"{self.SESSION_PREFIX}{session_id}"
        return await self.redis.get(key)

    async def invalidate_all_caches(self) -> int:
        """Clear all application caches."""
        count = 0
        count += await self.redis.clear_pattern(f"{self.DETECTION_PREFIX}*")
        count += await self.redis.clear_pattern(f"{self.CAMERA_PREFIX}*")
        count += await self.redis.clear_pattern(f"{self.USER_PREFIX}*")
        count += await self.redis.clear_pattern(f"{self.SESSION_PREFIX}*")
        logger.info(f"Cleared {count} cache keys")
        return count


# Global cache service instance
cache_service = CacheService()
