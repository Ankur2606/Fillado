"""
app/core/graph/neo4j_client.py

Async Neo4j driver wrapper for the Fillado causal knowledge graph.

Provides a context-managed driver and helper methods for running
Cypher queries from anywhere in the application.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from neo4j import AsyncDriver, AsyncGraphDatabase

from config import settings


class Neo4jClient:
    """
    Thin async wrapper around the official Neo4j Python driver.

    Usage:
        client = Neo4jClient()
        await client.connect()
        results = await client.run_query("MATCH (n:Company) RETURN n LIMIT 5")
        await client.close()

    Prefer using the module-level `neo4j_client` singleton.
    """

    def __init__(self) -> None:
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """
        Initialise the async Neo4j driver.

        # TODO: Add retry logic (via tenacity) to handle transient connection
        #       failures at startup.
        """
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def close(self) -> None:
        """Close the driver and release all connections."""
        if self._driver:
            await self._driver.close()
            self._driver = None

    async def run_query(
        self,
        cypher: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher query and return results as a list of dicts.

        Args:
            cypher: The Cypher query string.
            parameters: Optional query parameters.

        Returns:
            List of result records, each serialised as a plain dict.

        # TODO: Add query timeout configuration.
        # TODO: Log slow queries using structlog.
        """
        if self._driver is None:
            raise RuntimeError("Neo4jClient is not connected. Call connect() first.")

        parameters = parameters or {}
        async with self._driver.session() as session:
            result = await session.run(cypher, parameters)
            records = await result.data()
            return records

    async def upsert_company(self, symbol: str, name: str, **props: Any) -> None:
        """
        Upsert a Company node in the knowledge graph.

        # TODO: Extend with full Company schema fields (sector, ISIN, etc.).
        """
        cypher = (
            "MERGE (c:Company {symbol: $symbol}) "
            "SET c.name = $name, c += $props"
        )
        await self.run_query(cypher, {"symbol": symbol, "name": name, "props": props})

    async def upsert_event(self, event_id: str, event_type: str, headline: str) -> None:
        """
        Upsert an Event node in the knowledge graph.

        # TODO: Add relationships between Event and Company nodes using
        #       MERGE (e)-[:AFFECTS]->(c) patterns.
        """
        cypher = (
            "MERGE (e:Event {event_id: $event_id}) "
            "SET e.event_type = $event_type, e.headline = $headline"
        )
        await self.run_query(
            cypher,
            {"event_id": event_id, "event_type": event_type, "headline": headline},
        )

    @asynccontextmanager
    async def session_context(self) -> AsyncGenerator[Any, None]:
        """Expose a raw Neo4j session for advanced use-cases."""
        if self._driver is None:
            raise RuntimeError("Neo4jClient is not connected.")
        async with self._driver.session() as session:
            yield session


# Module-level singleton
neo4j_client = Neo4jClient()
