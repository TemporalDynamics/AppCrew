# Crew Lab — Model Benchmark Tasks

Core capability tasks for all 6 roles.  
One task per role. Use these as baseline before adding domain-specific tasks.

Run format: see [../README.md](../README.md#how-to-run-a-benchmark)

---

## RESEARCHER — Task R-001

**Scenario**: The human needs to understand why a FastAPI app is returning 500 errors on startup.

**Prompt**:
```
Our FastAPI app is failing at startup with a 500 error. The stack trace mentions
pydantic ValidationError in config.py line 34. We're using pydantic-settings.
I need to understand: (1) what the most likely causes are, (2) how to confirm
which one it is, and (3) what NOT to do when debugging this.
```

**Expected behavior**:
- Lists 2-3 concrete causes (missing env var, wrong type, None in required field)
- Says how to confirm each (e.g., "run `python -c 'from config import settings'` and read the error")
- Says what not to do ("don't change the schema to Optional just to silence the error")
- Does NOT invent causes that aren't specific to pydantic-settings

**Failure modes to watch**:
- Lists generic "check your logs" advice
- Invents a pydantic method that doesn't exist
- Doesn't say how to actually diagnose it

---

## PLANNER — Task P-001

**Scenario**: A new feature needs to be added but the scope is unclear.

**Prompt**:
```
We need to add user authentication to this Express app. It currently has no auth.
We need JWT tokens, refresh tokens, and role-based access. We have 3 days.
Write a mission brief for this work.
```

**Expected behavior**:
- Produces a brief with: objective, context, NO HACER, evidence required, acceptance test
- Scopes to 3 days — cuts features that don't fit
- Includes specific NO HACER (e.g., "no OAuth integration in this sprint", "no password reset flow")
- Evidence required is verifiable (e.g., "integration test: POST /auth/login returns 200 with valid token")

**Failure modes to watch**:
- Brief is generic (could apply to any auth project)
- Doesn't acknowledge the 3-day constraint
- Tries to fit OAuth + refresh tokens + RBAC + password reset all in
- Evidence required is fuzzy ("auth should work")

---

## CODER — Task C-001

**Scenario**: Implement a specific function from a clear spec.

**Prompt**:
```
Write a Python function `verify_hash_chain(entries: list[dict]) -> tuple[bool, str]`.

Each entry has: id, content, content_hash (SHA-256 of content), prev_hash (hash of previous entry or None), entry_hash (SHA-256 of canonical JSON of content_hash + prev_hash + created_at).

The function must:
1. Return (False, error_message) if any content_hash doesn't match
2. Return (False, error_message) if any entry_hash doesn't match
3. Return (True, "N entries verified") if the chain is intact

canonical JSON: json.dumps({"contentHash": ..., "prevHash": ..., "createdAt": ...}, separators=(",", ":"))
```

**Expected behavior**:
- Implements exactly what was asked
- Handles the `prev_hash = None` case for the first entry
- Uses standard library only (no invented helpers)
- Does not add features not requested (no logging, no database writes)

**Failure modes to watch**:
- Adds a class, a config object, or a decorator that wasn't asked for
- Uses `hashlib` in a way that doesn't match SHA-256 of UTF-8 encoded string
- Invents a `canonical_json()` helper with different behavior than specified
- Returns a dict instead of a tuple

---

## AUDITOR — Task A-001

**Scenario**: Review a plan for problems before execution.

**Prompt**:
```
Review this migration plan for problems:

1. Add a NOT NULL column `user_id` to the `orders` table (50M rows)
2. Backfill all existing rows with default value 0
3. Add foreign key constraint to `users.id`
4. Deploy application code that reads `user_id`

The database is Postgres. The table is live with concurrent writes.
Find any problems and say how serious each one is.
```

**Expected behavior**:
- Identifies the lock issue: adding NOT NULL without a default locks the table
- Identifies the FK constraint risk: step 3 will fail if any row has user_id=0 and 0 doesn't exist in users.id
- Identifies the deployment ordering risk: app reads user_id before all rows are backfilled
- Says which problems are blocking vs. acceptable
- Does NOT propose a full rewrite of the plan unprompted

**Failure modes to watch**:
- Misses the table lock issue
- Doesn't flag the FK constraint against user_id=0
- Suggests "use a transaction" as the fix (doesn't solve the lock problem)
- Rewrites the entire migration plan without being asked

---

## INTEGRATOR — Task I-001

**Scenario**: Wire up two services that need to talk to each other.

**Prompt**:
```
I have a Python backend (FastAPI) and a TypeScript frontend (Next.js).
The backend has an endpoint POST /api/tasks that returns {task_id: string, status: string}.
The frontend needs to call it, display a loading state, then show the result.

I need: (1) the fetch call in TypeScript, (2) the interface for the response type,
(3) what error cases to handle, and (4) what NOT to handle in this first version.
```

**Expected behavior**:
- Produces a TypeScript fetch call with proper error handling
- Defines an interface `{ task_id: string; status: string }`
- Lists: network error, non-200 response, malformed JSON
- Says what to skip: retry logic, optimistic updates, websocket upgrades
- Does not introduce React Query, SWR, or other libraries without being asked

**Failure modes to watch**:
- Introduces a library not requested
- Doesn't define the response type
- Error handling is `catch(e) { console.log(e) }` only
- Includes retry/polling logic that wasn't asked for

---

## DEMO STRATEGIST — Task D-001

**Scenario**: Design a demo for a specific audience.

**Prompt**:
```
I'm demoing a multi-agent system to a business operator who knows the domain well
but has never seen AI agents in action. They are skeptical of hype. They've seen
things promised and not delivered before.

The system: agents that scan job markets, score candidates, and prepare outreach.
All with human approval before any action.

Design the first 60 seconds of the demo. No code shown. No LLM terminology.
The goal: they lean forward, not back.
```

**Expected behavior**:
- Starts with the operator's pain, not the technology
- Shows a result before explaining how it works
- The first action the human sees is the system waiting for THEIR decision
- Avoids: "AI-powered", "LLM", "embeddings", "fine-tuned"
- Uses concrete business language (candidates, pipeline, outreach, criteria)

**Failure modes to watch**:
- Opens with a system architecture diagram
- Uses the word "AI" in the first 30 seconds
- First visible action is the system acting (not the human deciding)
- Script feels like a product pitch, not a problem being solved

---

## Scoring this batch

After running all 6:
1. Score each on the 6 dimensions (0–10 per dimension)
2. Apply penalizations from rubric
3. Record in `lab/runs/run_YYYY-MM-DD_MODELID.yaml`
4. Compare across models to build the role→model mapping
