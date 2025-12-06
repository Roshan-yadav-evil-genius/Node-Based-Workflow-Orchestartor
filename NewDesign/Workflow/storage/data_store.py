import json
import structlog
from typing import Any, Dict, Optional
import asyncio_redis

logger = structlog.get_logger(__name__)


class DataStore:
    """
    Redis-backed data store for cross-loop communication and state management.
    Handles queues, caching, and other shared data operations.
    
    Singleton pattern: Only one instance exists throughout the application.
    All nodes share the same DataStore instance and Redis connection.
    
    This implementation is process-safe: Redis handles concurrent access from
    multiple processes automatically. All nodes share the same DataStore instance
    and can safely access the same Redis keys/queues.
    
    Design principles:
    - Singleton pattern - only one instance exists
    - Single Redis connection shared by all nodes (created lazily on first use)
    - All operations are async
    - Data is serialized to JSON for storage
    - Queue operations use Redis Lists (LPUSH/BRPOP)
    - Cache operations use Redis Strings with optional TTL
    """
    # _instance = None
    
    # def __new__(cls, host: str = "127.0.0.1", port: int = 6379,
    #             db: int = 0, password: Optional[str] = None,
    #             pool_size: int = 10):
    #     """
    #     Create or return existing singleton instance.
    #     """
    #     if cls._instance is None:
    #         cls._instance = super(DataStore, cls).__new__(cls)
    #     return cls._instance
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        pool_size: int = 10
    ):
        """
        Initialize DataStore with Redis connection parameters.
        Only initializes on first call - subsequent calls are ignored.
        
        Args:
            host: Redis host address
            port: Redis port
            db: Redis database number
            password: Optional Redis password
            pool_size: Connection pool size (for future use with connection pooling)
        """
        # Prevent re-initialization if already initialized
        if hasattr(self, '_initialized'):
            return
        
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._pool_size = pool_size
        self._connection: Optional[asyncio_redis.Connection] = None
        self._prefix = "datastore:"  # Prefix for all keys to avoid conflicts
        self._initialized = True

    async def _ensure_connection(self):
        """
        Ensure Redis connection is established.
        Creates connection lazily on first use.
        """
        if self._connection is None:
            try:
                self._connection = await asyncio_redis.Connection.create(
                    host=self._host,
                    port=self._port,
                    db=self._db,
                    password=self._password
                )
                logger.info(f"Connected to Redis at {self._host}:{self._port}")
            except Exception as e:
                logger.error(
                    f"Failed to connect to Redis: {e}",
                    exc_info=True
                )
                raise
    
    async def close(self):
        """
        Close the Redis connection.
        Should be called when the DataStore is no longer needed.
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.info("Redis connection closed")
    
    def _serialize(self, data: Dict) -> str:
        """Serialize data to JSON string."""
        return json.dumps(data)
    
    def _deserialize(self, data: Optional[str]) -> Dict:
        """Deserialize JSON string to Python object."""
        if data is None:
            return None
        return json.loads(data)
    
    def _queue_key(self, queue_name: str) -> str:
        """Get Redis key for a queue."""
        return f"{self._prefix}queue:{queue_name}"
    
    def _cache_key(self, key: str) -> str:
        """Get Redis key for cache."""
        return f"{self._prefix}cache:{key}"

    # ========== Queue Operations ==========
    
    async def push(self, queue_name: str, data: Dict):
        """
        Push data to a named queue using Redis LPUSH.
        
        This operation is process-safe - multiple processes can push to
        the same queue simultaneously without issues.
        
        Args:
            queue_name: Name of the queue
            data: Data to push to the queue (will be JSON serialized)
        """
        await self._ensure_connection()
        queue_key = self._queue_key(queue_name)
        serialized_data = self._serialize(data)
        
        try:
            logger.info(f"Pushing data to queue",queue_key=queue_key)
            await self._connection.lpush(queue_key, [serialized_data])
            logger.info(f"Pushed to queue",queue_key=queue_key)
        except Exception as e:
            logger.error(
                f"Failed to push to queue '{queue_name}': {e}",
                exc_info=True
            )
            raise

    async def pop(self, queue_name: str, timeout: Optional[float] = None) -> Optional[Any]:
        """
        Pop data from a named queue using Redis BRPOP (blocking right pop).
        
        This operation is process-safe - multiple processes can pop from
        the same queue, and Redis will ensure each message is delivered
        to only one consumer.
        
        Args:
            queue_name: Name of the queue
            timeout: Optional timeout in seconds for blocking pop operation.
                    If None, blocks indefinitely. If 0, returns immediately.
            
        Returns:
            Any: Data popped from the queue (deserialized), or None if timeout occurs
        """
        await self._ensure_connection()
        queue_key = self._queue_key(queue_name)
        logger.info(f"Popping from queue",queue_key=queue_key)
        try:
            # Convert timeout to integer seconds for Redis BRPOP
            # BRPOP timeout of 0 means return immediately, None means block indefinitely
            if timeout is None:
                # Block indefinitely - don't pass timeout parameter
                result = await self._connection.brpop([queue_key])
            elif timeout == 0:
                # Return immediately
                result = await self._connection.brpop([queue_key], timeout=0)
            else:
                # Block for specified seconds
                redis_timeout = int(timeout)
                result = await self._connection.brpop([queue_key], timeout=redis_timeout)
            
            if result is None:
                return None
            
            # BRPOP returns BlockingPopReply object with value attribute
            serialized_data = result.value
            data = self._deserialize(serialized_data)
            logger.info(f"Popped from queue",queue_key=queue_key)
            return data
            
        except Exception as e:
            logger.error(
                f"Failed to pop from queue '{queue_name}': {e}",
                exc_info=True
            )
            raise

    async def queue_length(self, queue_name: str) -> int:
        """
        Get the length of a queue.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            int: Number of items in the queue
        """
        await self._ensure_connection()
        queue_key = self._queue_key(queue_name)
        
        try:
            length = await self._connection.llen(queue_key)
            return length
        except Exception as e:
            logger.error(
                f"Failed to get queue length for '{queue_name}': {e}",
                exc_info=True
            )
            raise

    # ========== Cache Operations ==========
    
    async def set_cache(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set a value in the cache.
        
        This operation is process-safe - multiple processes can write to
        the same key, with the last write winning.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Optional time-to-live in seconds
        """
        await self._ensure_connection()
        cache_key = self._cache_key(key)
        serialized_value = self._serialize(value)
        
        try:
            if ttl is not None:
                await self._connection.setex(cache_key, ttl, serialized_value)
            else:
                await self._connection.set(cache_key, serialized_value)
            logger.debug(f"Set cache key '{key}'")
        except Exception as e:
            logger.error(
                f"Failed to set cache key '{key}': {e}",
                exc_info=True
            )
            raise

    async def get_cache(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        This operation is process-safe - multiple processes can read from
        the same key simultaneously.
        
        Args:
            key: Cache key
            
        Returns:
            Any: Cached value (deserialized), or None if not found
        """
        await self._ensure_connection()
        cache_key = self._cache_key(key)
        
        try:
            serialized_value = await self._connection.get(cache_key)
            if serialized_value is None:
                return None
            return self._deserialize(serialized_value)
        except Exception as e:
            logger.error(
                f"Failed to get cache key '{key}': {e}",
                exc_info=True
            )
            raise

    async def delete_cache(self, key: str):
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key to delete
        """
        await self._ensure_connection()
        cache_key = self._cache_key(key)
        
        try:
            await self._connection.delete([cache_key])
            logger.debug(f"Deleted cache key '{key}'")
        except Exception as e:
            logger.error(
                f"Failed to delete cache key '{key}': {e}",
                exc_info=True
            )
            raise

    async def exists_cache(self, key: str) -> bool:
        """
        Check if a cache key exists.
        
        Args:
            key: Cache key to check
            
        Returns:
            bool: True if key exists, False otherwise
        """
        await self._ensure_connection()
        cache_key = self._cache_key(key)
        
        try:
            exists = await self._connection.exists(cache_key)
            return bool(exists)
        except Exception as e:
            logger.error(
                f"Failed to check existence of cache key '{key}': {e}",
                exc_info=True
            )
            raise
