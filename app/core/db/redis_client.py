"""
app/core/db/redis_client.py

Async Redis client for pub/sub messaging and background task coordination.

Uses the official redis-py async API. The module exposes a lifespan-managed
connection and helper methods for pub/sub and caching.
"""

from __future__ import annotations

from typing import Any, AsyncGenerator

import redis.asyncio as aioredis

from config import settings


class RedisClient:
    """
    Thin async wrapper around the redis-py async client.

    Usage:
        client = RedisClient()
        await client.connect()
        await client.publish("alerts", "{ ... }")
        await client.close()

    Prefer using the module-level `redis_client` singleton.
    """

    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    async def connect(self) -> None:
        """
        Initialise the Redis connection pool.

        # TODO: Configure connection pool size and socket timeouts.
        # TODO: Add retry logic for connection failures at startup.
        """
        self._client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _ensure_connected(self) -> aioredis.Redis:
        if self._client is None:
            raise RuntimeError("RedisClient is not connected. Call connect() first.")
        return self._client

    # ── Pub/Sub ───────────────────────────────────────────────────────────────

    async def publish(self, channel: str, message: str) -> int:
        """
        Publish a message to a Redis channel.

        Returns the number of subscribers that received the message.

        # TODO: Serialise complex payloads to JSON before publishing.
        """
        return await self._ensure_connected().publish(channel, message)

    async def subscribe(self, channel: str) -> AsyncGenerator[str, None]:
        """
        Async generator that yields messages from a Redis pub/sub channel.

        # TODO: Add error handling and auto-reconnect logic.
        """
        client = self._ensure_connected()
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield message["data"]
        finally:
            await pubsub.unsubscribe(channel)

    # ── Caching ───────────────────────────────────────────────────────────────

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        """
        Set a string key in Redis with an optional TTL.

        # TODO: Wrap complex values in JSON serialisation.
        """
        client = self._ensure_connected()
        if ttl_seconds:
            await client.setex(key, ttl_seconds, value)
        else:
            await client.set(key, value)

    async def get(self, key: str) -> str | None:
        """Get a string value from Redis by key."""
        return await self._ensure_connected().get(key)

    async def delete(self, key: str) -> int:
        """Delete a key from Redis."""
        return await self._ensure_connected().delete(key)


# Module-level singleton
redis_client = RedisClient()
