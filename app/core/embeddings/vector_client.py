"""
app/core/embeddings/vector_client.py

Provider-agnostic vector database client.

Supports Pinecone and Milvus backends, selected via the
VECTOR_DB_BACKEND environment variable ('pinecone' | 'milvus').
"""

from __future__ import annotations

from typing import Any

from config import settings


class VectorClient:
    """
    Thin abstraction layer over Pinecone / Milvus vector databases.

    Usage:
        client = VectorClient()
        await client.connect()
        await client.upsert(id="doc-1", vector=[0.1, ...], metadata={})
        results = await client.similarity_search([0.1, ...], top_k=5)
        await client.close()

    Prefer using the module-level `vector_client` singleton.
    """

    def __init__(self) -> None:
        self._backend = settings.vector_db_backend
        self._client: Any = None

    async def connect(self) -> None:
        """
        Initialise the vector DB connection based on the configured backend.

        Pinecone: synchronous SDK, wrapped in async context.
        Milvus: PyMilvus async API.

        # TODO: Initialise Pinecone via pinecone.init() or the new Pinecone() class.
        # TODO: Initialise Milvus via pymilvus.connections.connect().
        # TODO: Create the index / collection if it does not already exist.
        """
        if self._backend == "pinecone":
            # TODO: from pinecone import Pinecone
            #       self._client = Pinecone(api_key=settings.pinecone_api_key)
            pass
        elif self._backend == "milvus":
            # TODO: from pymilvus import connections
            #       connections.connect(uri=settings.milvus_uri)
            pass
        else:
            raise ValueError(f"Unsupported vector DB backend: {self._backend}")

    async def close(self) -> None:
        """Close the vector DB connection."""
        # TODO: Implement graceful disconnect for each backend.
        pass

    async def upsert(
        self,
        doc_id: str,
        vector: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Upsert a single vector into the configured index / collection.

        Args:
            doc_id: Unique document identifier.
            vector: Dense embedding vector.
            metadata: Optional payload stored alongside the vector.

        # TODO: Pinecone: index.upsert(vectors=[(doc_id, vector, metadata)]).
        # TODO: Milvus: collection.insert([doc_id, vector, metadata]).
        """
        pass  # TODO: implement per-backend

    async def upsert_batch(
        self,
        documents: list[dict[str, Any]],
    ) -> None:
        """
        Batch upsert a list of documents.

        Each document must have keys: 'id', 'vector', and optionally 'metadata'.

        # TODO: Use backend-native batch APIs for efficiency.
        """
        for doc in documents:
            await self.upsert(
                doc_id=doc["id"],
                vector=doc["vector"],
                metadata=doc.get("metadata"),
            )

    async def similarity_search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Find the top-k most similar vectors to the query.

        Args:
            query_vector: Dense query embedding.
            top_k: Number of results to return.
            filter_metadata: Optional metadata filter (backend-specific syntax).

        Returns:
            List of dicts with keys: 'id', 'score', 'metadata'.

        # TODO: Pinecone: index.query(vector=query_vector, top_k=top_k, filter=...).
        # TODO: Milvus: collection.search(data=[query_vector], ...).
        """
        # Stub
        return [{"id": "stub", "score": 0.0, "metadata": {}}]

    async def delete(self, doc_id: str) -> None:
        """
        Delete a vector by its document ID.

        # TODO: Implement per-backend delete.
        """
        pass  # TODO


# Module-level singleton
vector_client = VectorClient()
