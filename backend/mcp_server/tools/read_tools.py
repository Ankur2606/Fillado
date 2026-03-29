"""
backend/mcp_server/tools/read_tools.py
MCP Read Tools – hardcoded mock data so the demo always works without live APIs.
These are called by agents when the Thought Policeman forces them to ground themselves.
"""
import json
from datetime import datetime, timedelta
import random


# ---------------------------------------------------------------------------
# Tool 1: fetch_et_news_mock
# ---------------------------------------------------------------------------
_ET_NEWS_DB = {
    "transport strike gujarat": [
        {
            "headline": "Gujarat Transport Strike Enters Day 3, Cargo Movement Halted",
            "source": "Economic Times",
            "date": "2024-08-15",
            "url": "https://economictimes.indiatimes.com/mock-1",
            "summary": "Truck operators in Gujarat have called an indefinite strike, disrupting freight movements to ports including Mundra and Pipavav.",
            "tickers_mentioned": ["ADANIPORTS", "GUJGASLTD", "CONCOR"],
        },
        {
            "headline": "Logistics Sector Braces for Impact as Gujarat Strike Continues",
            "source": "ET Markets",
            "date": "2024-08-14",
            "url": "https://economictimes.indiatimes.com/mock-2",
            "summary": "Analysts warn of supply-chain ripple effects on petrochemical and FMCG sectors.",
            "tickers_mentioned": ["MAHLOG", "ADANIPORTS", "RELIANCE"],
        },
    ],
    "factory strike": [
        {
            "headline": "Hosur Factory Workers Call Strike, Ashok Leyland Output Halted",
            "source": "Economic Times",
            "date": "2024-08-12",
            "url": "https://economictimes.indiatimes.com/mock-3",
            "summary": "Production at the Ashok Leyland Hosur plant has been suspended following a wage dispute.",
            "tickers_mentioned": ["ASHOKLEY", "MRF", "APOLLOTYRE"],
        }
    ],
    "default": [
        {
            "headline": "Indian Markets Cautious Amid Regional Disruptions",
            "source": "ET Markets",
            "date": "2024-08-15",
            "url": "https://economictimes.indiatimes.com/mock-4",
            "summary": "Multiple sector-specific disruptions are creating pockets of volatility in mid-cap indices.",
            "tickers_mentioned": ["NIFTY50", "MIDCAP"],
        }
    ],
}


def fetch_et_news_mock(query: str, timeframe: str = "7d") -> dict:
    """
    Returns mock Economic Times articles relevant to the query.
    MCP Tool: fetch_et_news_mock
    """
    q_lower = query.lower()
    articles = _ET_NEWS_DB.get("default")
    for key, val in _ET_NEWS_DB.items():
        if key != "default" and any(word in q_lower for word in key.split()):
            articles = val
            break

    return {
        "tool": "fetch_et_news_mock",
        "query": query,
        "timeframe": timeframe,
        "article_count": len(articles),
        "articles": articles,
        "grounding_summary": f"Found {len(articles)} ET articles about '{query}' in the last {timeframe}.",
    }


# ---------------------------------------------------------------------------
# Tool 2: get_nse_price_mock
# ---------------------------------------------------------------------------
_BASE_PRICES = {
    "ADANIPORTS": 1280.50,
    "GUJGASLTD": 485.75,
    "CONCOR": 890.20,
    "MAHLOG": 412.35,
    "RELIANCE": 2945.60,
    "ASHOKLEY": 198.40,
    "MRF": 148500.00,
    "APOLLOTYRE": 476.80,
    "NIFTY50": 24750.00,
}


def get_nse_price_mock(ticker: str) -> dict:
    """
    Returns hardcoded OHLCV data for a given NSE ticker.
    MCP Tool: get_nse_price_mock
    """
    base = _BASE_PRICES.get(ticker.upper(), 500.00)
    today = datetime.now()

    ohlcv = []
    price = base
    for i in range(5):
        day = today - timedelta(days=4 - i)
        change_pct = random.uniform(-0.03, 0.02)
        open_p = round(price, 2)
        close_p = round(price * (1 + change_pct), 2)
        high_p = round(max(open_p, close_p) * random.uniform(1.001, 1.015), 2)
        low_p = round(min(open_p, close_p) * random.uniform(0.985, 0.999), 2)
        volume = random.randint(500_000, 5_000_000)
        ohlcv.append({
            "date": day.strftime("%Y-%m-%d"),
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": volume,
        })
        price = close_p

    current = ohlcv[-1]
    prev = ohlcv[-2]
    change = round(current["close"] - prev["close"], 2)
    change_pct_val = round((change / prev["close"]) * 100, 2)

    return {
        "tool": "get_nse_price_mock",
        "ticker": ticker.upper(),
        "current_price": current["close"],
        "change": change,
        "change_pct": change_pct_val,
        "52w_high": round(base * 1.28, 2),
        "52w_low": round(base * 0.71, 2),
        "ohlcv_5d": ohlcv,
        "market_cap_cr": round(base * random.randint(50_000_000, 200_000_000) / 1e7, 0),
    }


# ---------------------------------------------------------------------------
# Tool 3: run_pattern_backtest_mock
# ---------------------------------------------------------------------------
_BACKTEST_PATTERNS = {
    "bull flag": {"win_rate": 62, "avg_gain_pct": 14.3, "avg_loss_pct": -5.2, "trades": 147},
    "bear flag": {"win_rate": 58, "avg_gain_pct": 12.1, "avg_loss_pct": -6.8, "trades": 89},
    "head and shoulders": {"win_rate": 71, "avg_gain_pct": 18.7, "avg_loss_pct": -7.1, "trades": 63},
    "double bottom": {"win_rate": 67, "avg_gain_pct": 15.2, "avg_loss_pct": -4.9, "trades": 112},
    "cup and handle": {"win_rate": 74, "avg_gain_pct": 21.4, "avg_loss_pct": -6.3, "trades": 55},
    "default": {"win_rate": 55, "avg_gain_pct": 10.0, "avg_loss_pct": -6.0, "trades": 200},
}


def run_pattern_backtest_mock(pattern: str, ticker: str) -> dict:
    """
    Returns historical backtest statistics for a chart pattern on a ticker.
    MCP Tool: run_pattern_backtest_mock
    """
    pattern_lower = pattern.lower()
    stats = _BACKTEST_PATTERNS.get("default")
    for key, val in _BACKTEST_PATTERNS.items():
        if key != "default" and key in pattern_lower:
            stats = val
            break

    return {
        "tool": "run_pattern_backtest_mock",
        "pattern": pattern,
        "ticker": ticker.upper(),
        "win_rate_pct": stats["win_rate"],
        "avg_gain_pct": stats["avg_gain_pct"],
        "avg_loss_pct": stats["avg_loss_pct"],
        "num_historical_trades": stats["trades"],
        "summary": (
            f"{pattern} on {ticker.upper()} has a {stats['win_rate']}% historical win rate "
            f"over {stats['trades']} trades, avg gain {stats['avg_gain_pct']}%, avg loss {stats['avg_loss_pct']}%."
        ),
    }


# ---------------------------------------------------------------------------
# Tool 4: execute_graphrag_query (delegates to GraphRAGTransformer)
# ---------------------------------------------------------------------------
async def execute_graphrag_query(unstructured_query: str) -> dict:
    """
    Delegates to the GraphRAGTransformer to extract entities and
    return supply-chain sub-graph context from Neo4j AuraDB.
    MCP Tool: execute_graphrag_query
    """
    from backend.graph.graphrag import GraphRAGTransformer
    transformer = GraphRAGTransformer()
    result = await transformer.transform(unstructured_query)
    transformer.close()
    return {
        "tool": "execute_graphrag_query",
        "query": unstructured_query,
        **result,
    }
