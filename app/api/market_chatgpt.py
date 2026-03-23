"""
app/api/market_chatgpt.py

FastAPI router for the Market ChatGPT 2.0 research assistant.

Endpoints:
  POST /market-chatgpt/query — Submit a portfolio-aware research query.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.services.market_chatgpt.models import QueryRequest, QueryResponse
from app.services.market_chatgpt.workflows import run_market_research

router = APIRouter()


@router.post(
    "/market-chatgpt/query",
    response_model=QueryResponse,
    summary="Submit a portfolio-aware market research query",
    description=(
        "Sends a natural-language research question to the Market ChatGPT 2.0 "
        "multi-step research agent.\n\n"
        "The agent:\n"
        "  1. Retrieves the user's portfolio holdings.\n"
        "  2. Queries the Neo4j causal knowledge graph for related companies "
        "     and events.\n"
        "  3. Performs a semantic search over ET news and NSE filings.\n"
        "  4. Synthesises a grounded answer using the configured LLM.\n\n"
        "Portfolio holdings (if provided) are used to bias retrieval towards "
        "the user's existing positions."
    ),
)
async def market_chatgpt_query(body: QueryRequest) -> QueryResponse:
    """
    Run the Market ChatGPT 2.0 LangGraph workflow and return a grounded answer.

    The response includes:
      - The synthesised answer.
      - The ordered list of reasoning steps taken by the agent.
      - Source references used to ground the answer.
      - A flag indicating whether portfolio context influenced retrieval.

    # TODO: Authenticate the user and resolve user_id to a verified account.
    # TODO: Enforce rate limiting per user_id to prevent abuse.
    # TODO: Stream the response using Server-Sent Events for long-running queries.
    """
    return await run_market_research(body)
