"""
app/core/graph/schema.py

Neo4j node and relationship schema definitions for the Fillado
causal knowledge graph.

These constants and Cypher templates are used by the neo4j_client
to initialise constraints/indexes and by agents to build queries.
"""

from __future__ import annotations

# ── Node labels ───────────────────────────────────────────────────────────────

LABEL_COMPANY = "Company"
LABEL_EVENT = "Event"
LABEL_LOCATION = "Location"
LABEL_SUPPLIER = "Supplier"
LABEL_SECTOR = "Sector"

# ── Relationship types ────────────────────────────────────────────────────────

REL_AFFECTS = "AFFECTS"
REL_SUPPLIES = "SUPPLIES"
REL_COMPETES_WITH = "COMPETES_WITH"
REL_LOCATED_IN = "LOCATED_IN"
REL_CAUSED_BY = "CAUSED_BY"
REL_BELONGS_TO = "BELONGS_TO"

# ── Constraint / index creation Cypher ───────────────────────────────────────

SCHEMA_CONSTRAINTS: list[str] = [
    # Unique constraints
    f"CREATE CONSTRAINT company_symbol IF NOT EXISTS "
    f"FOR (c:{LABEL_COMPANY}) REQUIRE c.symbol IS UNIQUE",
    f"CREATE CONSTRAINT event_id IF NOT EXISTS "
    f"FOR (e:{LABEL_EVENT}) REQUIRE e.event_id IS UNIQUE",
    f"CREATE CONSTRAINT location_name IF NOT EXISTS "
    f"FOR (l:{LABEL_LOCATION}) REQUIRE l.name IS UNIQUE",
]

SCHEMA_INDEXES: list[str] = [
    # Full-text indexes for search
    f"CREATE FULLTEXT INDEX company_name_ft IF NOT EXISTS "
    f"FOR (c:{LABEL_COMPANY}) ON EACH [c.name]",
    f"CREATE FULLTEXT INDEX event_headline_ft IF NOT EXISTS "
    f"FOR (e:{LABEL_EVENT}) ON EACH [e.headline]",
]


async def apply_schema(client: "Neo4jClient") -> None:  # noqa: F821
    """
    Apply all constraints and indexes to the Neo4j database.

    Call this once at application startup (e.g. from a lifespan handler).

    # TODO: Wrap in a try/except to handle constraint-already-exists errors
    #       gracefully on repeated startups.
    """
    for statement in SCHEMA_CONSTRAINTS + SCHEMA_INDEXES:
        await client.run_query(statement)
