"""
backend/mcp_server/tools/write_tools.py
MCP Write Tool – append_causal_link
Used ONLY by the Synthesis Agent to permanently write newly discovered
market connections back to Neo4j AuraDB.
"""
import logging
import re

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

# Allowlist of valid relationship types to prevent Cypher injection
ALLOWED_RELATIONSHIPS = {
    "CAUSES", "IMPACTS", "DISRUPTS", "DELAYS", "RIPPLES",
    "SUPPLY_CHAIN_RISK", "POSITIVELY_IMPACTS", "NEGATIVELY_IMPACTS",
    "CORRELATED_WITH", "COMPETES_WITH",
}


def _validate_identifier(val: str, field: str) -> str:
    """Validate that a node name is safe to embed in Cypher."""
    if not re.match(r'^[\w\s\-\.&]+$', val):
        raise ValueError(f"Invalid characters in {field}: {val!r}")
    return val.strip()


async def append_causal_link(source: str, relationship: str, target: str) -> dict:
    """
    Synthesis Agent uses this to write a newly discovered market connection
    to Neo4j AuraDB via a MERGE Cypher query.
    MCP Tool: append_causal_link (Write)

    Args:
        source:       Source node name (e.g., "Transport Strike")
        relationship: Edge type (must be in ALLOWED_RELATIONSHIPS)
        target:       Target node name (e.g., "ADANIPORTS")
    """
    # Validate inputs
    try:
        source = _validate_identifier(source, "source")
        target = _validate_identifier(target, "target")
    except ValueError as e:
        return {"tool": "append_causal_link", "success": False, "error": str(e)}

    rel_upper = relationship.upper().replace(" ", "_")
    if rel_upper not in ALLOWED_RELATIONSHIPS:
        return {
            "tool": "append_causal_link",
            "success": False,
            "error": f"Relationship '{rel_upper}' not in allowlist. Allowed: {sorted(ALLOWED_RELATIONSHIPS)}",
        }

    settings = get_settings()

    if not settings.neo4j_uri:
        # Mock mode – log and return success without writing
        logger.info(f"[MCP-MOCK] Would write: ({source})-[:{rel_upper}]->({target})")
        return {
            "tool": "append_causal_link",
            "success": True,
            "mode": "mock",
            "message": f"Graph learning recorded (mock): ({source})-[:{rel_upper}]->({target})",
            "source": source,
            "relationship": rel_upper,
            "target": target,
        }

    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
        cypher = """
        MERGE (s:Entity {name: $source})
        MERGE (t:Entity {name: $target})
        MERGE (s)-[r:CAUSAL_LINK {type: $rel}]->(t)
        ON CREATE SET r.created_at = datetime(), r.source = 'fillado_synthesis'
        ON MATCH  SET r.updated_at = datetime(), r.confirmed_count = coalesce(r.confirmed_count, 0) + 1
        RETURN s.name AS src, type(r) AS relationship, t.name AS tgt
        """
        with driver.session() as session:
            record = session.run(cypher, source=source, target=target, rel=rel_upper).single()
        driver.close()
        return {
            "tool": "append_causal_link",
            "success": True,
            "mode": "live",
            "message": f"Neo4j updated: ({source})-[:{rel_upper}]->({target})",
            "source": source,
            "relationship": rel_upper,
            "target": target,
        }
    except Exception as exc:
        logger.error(f"[append_causal_link] Neo4j write failed: {exc}")
        return {
            "tool": "append_causal_link",
            "success": False,
            "error": str(exc),
        }
