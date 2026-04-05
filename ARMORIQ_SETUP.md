# ArmorIQ + Fillado MCP — Setup Guide

## What is this?

[ArmorIQ](https://platform.armoriq.ai) is an AI governance layer that adds
plan-capture, intent-token validation, and audited delegation to your existing
tool calls. Fillado exposes its NSE data + knowledge-graph tools as an MCP
server so ArmorIQ can call them with full observability.

---

## Prerequisites

- Fillado backend running (`uvicorn backend.main:app --port 8000`)
- [ngrok](https://ngrok.com) installed (`choco install ngrok` on Windows)
- An [ArmorIQ account](https://platform.armoriq.ai)
- `armoriq-sdk` installed (see Step 1)

---

## Step-by-step Setup

### Step 1 — Install armoriq-sdk

```bash
pip install armoriq-sdk
```

### Step 2 — Start ngrok

Open a **separate terminal** and run:

```bash
ngrok http 8000
```

Copy the **Forwarding HTTPS URL** — it looks like:

```
https://abc123def456.ngrok-free.app
```

### Step 3 — Configure .env

Add these lines to your `.env` file:

```env
# ArmorIQ credentials (get from platform.armoriq.ai → Settings → API Keys)
ARMORIQ_API_KEY=your_armoriq_api_key_here
ARMORIQ_USER_ID=your_armoriq_user_id_here
ARMORIQ_AGENT_ID=your_armoriq_agent_id_here

# ngrok public URL (update every time you restart ngrok)
NGROK_PUBLIC_URL=https://abc123def456.ngrok-free.app
```

### Step 4 — Restart the backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

You should see on startup:

```
[MCP HTTP] Endpoint live at /mcp
[ArmorIQ] ✅ Client initialized (agent_id=...)
```

### Step 5 — Verify MCP endpoints are publicly reachable

```bash
curl https://abc123def456.ngrok-free.app/mcp/health
# → {"status":"ok","tools":["get_nse_price","fetch_et_news",...]}

curl https://abc123def456.ngrok-free.app/mcp/manifest
# → {"name":"fillado-mcp","version":"1.0.0","tools":[...]}
```

### Step 6 — Register on ArmorIQ platform

1. Go to [platform.armoriq.ai](https://platform.armoriq.ai) → **MCP Directory**
2. Click **Register MCP Server**
3. Set **Name** = `fillado-mcp`
4. Set **Manifest URL** = `https://abc123def456.ngrok-free.app/mcp/manifest`
5. ArmorIQ will auto-read the tool schemas from your manifest
6. Save — your tools are now available to the ArmorIQ agent runtime

> Reference: [ArmorIQ MCP Directory docs](https://docs.armoriq.ai/docs/mcp-directory)

### Step 7 — Run the integration test

```bash
python -m scripts.test_armoriq
```

Expected output:

```
[1] Client init: ✅ configured
[2] MCP health: ✅ {"status": "ok", "tools": [...]}
[3] MCP manifest: ✅ 5 tools: [...]
[4] MCP dispatch (mock): ✅ status=200
[5] ArmorIQ flow: ✅
```

---

## Using the ArmorIQ endpoint

Instead of the standard debate endpoint:

```bash
POST /api/trigger-event
```

Use the ArmorIQ-enhanced endpoint which **runs both concurrently**:

```bash
POST /api/trigger-event-armoriq
Content-Type: application/json

{ "event": "SEBI tightens F&O margin rules" }
```

The response includes both the LangGraph debate result **and** the ArmorIQ
plan/delegation audit trail. A `armoriq_plan` WebSocket event is also broadcast
to the frontend.

---

## Architecture

```
Frontend (React)
     │
     ├─ POST /api/trigger-event-armoriq
     │        │
     │        ├─ asyncio.gather(
     │        │     trigger_via_armoriq()   ← ArmorIQ plan → token → delegate
     │        │     run_trading_floor()     ← existing LangGraph debate (unchanged)
     │        │  )
     │        │
     │        └─ broadcast armoriq_plan via WebSocket
     │
     └─ GET  /mcp/manifest   ← ArmorIQ reads tool schemas here
        POST /mcp            ← ArmorIQ calls tools here (via ngrok tunnel)
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `[ArmorIQ] ⚠️ Credentials not configured` | Add `ARMORIQ_API_KEY`, `ARMORIQ_USER_ID`, `ARMORIQ_AGENT_ID` to `.env` |
| `[ArmorIQ] ⚠️ armoriq-sdk not installed` | Run `pip install armoriq-sdk` |
| MCP health returns 404 | Check that backend restarted after the latest code changes |
| ngrok tunnel expired | Restart `ngrok http 8000` and update `NGROK_PUBLIC_URL` in `.env` |
| ArmorIQ can't reach `/mcp` | Make sure you're using the **HTTPS** ngrok URL, not HTTP |
