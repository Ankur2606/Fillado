## Fillado: The Reality-Anchored Market Intelligence Layer

#### An agentic, cross-lingual market causality engine. Fillado ingests real-time vernacular news, verifies events autonomously using LangGraph, and maps supply-chain disruptions to NSE stock tickers via a Neo4j Knowledge Graph to surface low-latency trading signals. Built for the ET GenAI Hackathon.

---
# HLD

<img width="1440" height="3008" alt="image" src="https://github.com/user-attachments/assets/22d343d2-225f-4e9f-8750-9da4d55c05a5" />


---

Fillado/
├── backend/
│   ├── main.py                   # FastAPI app entrypoint (WebSockets, REST)
│   ├── requirements.txt
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── trading_floor.py      # LangGraph multi-agent debate graph
│   │   └── synthesis_agent.py    # Synthesis + graph writer agent
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── thought_policeman.py  # Semantic drift detector (Groq 8B)
│   ├── graph/
│   │   ├── __init__.py
│   │   └── graphrag.py           # GraphRAGTransformer (Neo4j + Groq 8B)
│   └── core/
│       ├── __init__.py
│       └── config.py             # Pydantic settings from .env
├── mcp_server/
│   ├── __init__.py
│   ├── server.py                 # FastAPI MCP sub-app (tool definitions)
│   └── tools/
│       ├── __init__.py
│       ├── read_tools.py         # fetch_et_news_mock, get_nse_price_mock, etc.
│       └── write_tools.py        # append_causal_link (Neo4j Cypher write)
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── components/
│       │   ├── Dashboard.jsx          # Alert radar / feed
│       │   ├── TradingFloor.jsx       # Rotating triangle + debate stream
│       │   ├── AgentNode.jsx          # Circular PFP node
│       │   ├── SpeechBubble.jsx       # Streaming text bubble
│       │   ├── HallucinationBadge.jsx # Red "Context Corrected" badge
│       │   ├── GraphViz.jsx           # Causal chain visualization
│       │   └── TradingSignal.jsx      # Final synthesized signal
│       └── hooks/
│           └── useWebSocket.js        # WS hook for streaming
├── .env.example
├── docker-compose.yml
└── README.md (existing)

# Product Requirements Document (PRD)


### 1. The Core Vision: What Are We Solving?
We are merging the "AI for the Indian Investor" track with the "Patch the Reality" theme to build a system that finds hidden market opportunities while actively preventing AI hallucinations.

* **The Investor Problem:** Retail investors react to mainstream English news *after* institutional players have already moved the market. They miss the hidden supply-chain ripples caused by local events.
* **The AI Problem:** When AI agents analyze complex market dynamics, they often spiral into hallucinated agreements, inventing fake economic impacts and burning API tokens. Furthermore, most market AI is static—it only knows the rules it was programmed with.

**The Solution:** Fillado is an agentic intelligence layer that catches vernacular supply-chain disruptions (e.g., a Hindi news report of a factory strike) before the English market reacts. We drop this event into a "Trading Floor" where distinct AI personas debate its impact. Crucially, a **"Thought Policeman" Middleware** monitors this debate for hallucinations, forcing the agents to use hard data via an MCP server if they drift. Finally, a **Synthesis Agent** monitors the concluded debate, extracts newly discovered market connections, and dynamically updates our Neo4j Knowledge Graph.

### 2. Unique Selling Propositions (USPs)
* **Latency Arbitrage:** We turn regional noise into institutional alpha by mapping vernacular news to NSE tickers before mainstream adoption.
* **Synthetic Market Sentiment Simulator:** Users watch distinct AI personas (The Retail Trader, The Whale, The Contrarian) debate the news in real-time, making the AI's reasoning 100% transparent.
* **Reality-Anchored Middleware (Zero Hallucinations):** Custom middleware calculates semantic drift mid-generation. If agents hallucinate, the system interrupts them and forces them to pull real-world ET Market data.
* **The Self-Learning Graph:** The system dynamically learns new supply chain connections from the agent debates and appends them to its own database.
* **Ultra-Low Latency Delivery:** Alerts are pushed instantly to the Vite frontend via WebSockets.

---

### 3. Feature Detailing (Simple Words for the Team)

**Feature A: The Vernacular Scout & Base Graph**
* **How it works:** A Python script scrapes local news (Hindi, Tamil, Telugu). It extracts the event and location, then queries our base Neo4j Graph Database. 
* **The Output:** The graph connects the initial dots: *Strike $\rightarrow$ Hosur $\rightarrow$ Ashok Leyland Factory*.

**Feature B: The Agentic Trading Floor (The Debate)**
* **How it works:** The mapped event is dropped into a virtual chatroom. Three AI agents with different system prompts debate the broader market impact for exactly 3 turns. 
* **The Output:** They simulate how real market narratives form, exploring secondary and tertiary impacts (e.g., "Ashok Leyland slowing down means their tire supplier, MRF, will also take a hit").


**Feature C: The "Thought Policeman" Middleware (Context-Correction)**
* **How it works:** A FastAPI proxy sits between our reasoning agents and the LLM provider. Instead of using heavy local embedding models to calculate vector drift, we leverage the blistering inference speed of the Groq API. As the heavy 70B model streams tokens, the middleware routes the last 3 generated sentences and the original objective to the ultra-fast `llama-3.1-8b-instant` model. It asks a strict binary question: *"Is this agent hallucinating or off-topic? YES or NO."*
* **The Output:** If the 8B model flags a "YES", the middleware instantly acts as a circuit breaker and kills the connection to save tokens. It injects a hard system override: *"Stop. Context drift detected. You must use the MCP server to fetch real ET Market or NSE data to ground your reasoning."*

**Feature D: The Dynamic Graph Updater (Self-Learning)**
* **How it works:** A final "Synthesis Agent" reads the completed, hallucination-free debate transcript. If the agents logically concluded a new relationship (e.g., *Ashok Leyland Strike $\rightarrow$ negatively impacts $\rightarrow$ MRF Tires*), this agent generates a Cypher query.
* **The Output:** The new `[:CAUSES]` or `[:IMPACTS]` relationship is permanently written to the Neo4j database. The next time a similar event occurs, Fillado already knows the ripple effect.

---

### 4. The MCP Server & Tools
Model Context Protocol (MCP) lets our AI models securely access external tools. When the Middleware interrupts a hallucinating agent, the agent uses these tools to patch its reality with facts.

**Read Tools:**
* `fetch_et_news(query, timeframe)`: Pulls verified articles from the Economic Times archive.
* `get_nse_price(ticker)`: Fetches real-time price, volume, and bulk/block deal data.
* `run_backtest(pattern, ticker)`: Looks up historical success rates for chart patterns.

**Write Tools (For the Synthesis Agent):**
* `append_causal_link(source_node, relationship, target_node)`: Executes the Cypher query to add new knowledge to the Neo4j graph, making the AI permanently smarter.

---

### 5. User Flow & UI Flow

**Step 1: The Dashboard (The Radar)**
* The user logs into the web app. They see a live feed of "Opportunity Alerts" streaming in via WebSockets.

**Step 2: The Event Trigger**
* A new alert pops up: *"🚨 High Confidence: Transport Strike in Gujarat."* The user clicks the alert.

**Step 3: The Trading Floor (The Debate)**
* A chat interface opens. The text streams in real-time as the Retail, Institutional, and Contrarian AIs debate.
* *UI Polish:* If the middleware detects a hallucination, the UI flashes a red "Context Corrected" badge, showing exactly when the AI was forced to pull real data.

**Step 4: The Graph Update (The "Aha!" Moment)**
* The debate concludes. The UI displays a notification: *"🧠 Fillado has learned a new market connection: Transport Strike $\rightarrow$ Logistics Sector Drop."* A visual node-link diagram animates to show the new connection being formed.

**Step 5: The Action**
* The user is presented with the final trade signal and a back-tested chart pattern overlay to execute their strategy.

---

### 6. High-Level Architecture
1. **Ingestion Layer:** Scrapes regional vernacular feeds and APIs.
2. **Middleware Proxy (The Circuit Breaker):** A FastAPI layer that intercepts LangGraph LLM requests. It uses the Groq `llama-3.1-8b-instant` small model to constantly check streaming text for semantic drift or looping, completely replacing the need for local sentence transformers.
3. **Reasoning Layer (LangGraph):** Orchestrates the multi-agent debate (using the larger Groq `llama-3.3-70b-versatile`) and runs the Synthesis Agent to summarize the consensus.
4. **Knowledge Core (Neo4j AuraDB & MCP Server):** Neo4j AuraDB (cloud tier) holds the evolving supply chain relationships, which are queried dynamically via our `GraphRAGTransformer`. The isolated MCP Server holds the executable tools.
5. **Delivery Layer (FastAPI + WebSockets):** Pushes the real-time event trigger, the live debate token stream, and the new graph updates directly to the React frontend.

---

### 7. APIs, Validation, and Fallbacks
* **External APIs:** We will integrate open-source Python libraries (`jugaad-data` or `nsetools`) to fetch real OHLCV data to simulate the ET Market feeds.
* **Validation:** A signal is only passed to the user if the "Verification Agent" can cross-reference the vernacular news with at least one independent web source. The Graph Update tool validates Cypher syntax before executing writes to prevent database corruption.
* **Fallbacks:** If the primary LLM provider is rate-limited, the middleware automatically routes to a fallback model. If the live NSE data source fails, the MCP server falls back to vector database embeddings of historical pricing.
