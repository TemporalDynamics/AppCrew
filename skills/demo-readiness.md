# Skill: Demo Readiness Check

**Trigger**: Human is preparing a demo and wants to verify it will not fail publicly.

**Goal**: Audit the demo path, find failure points, produce a go/no-go recommendation.

---

## Protocol

### Step 1 — Identify the demo path

Ask (or infer from context):
1. What is the first action in the demo?
2. What is the expected output of each step?
3. What are the P0 moments (the ones where failure is visible)?

### Step 2 — Check each P0 moment

For each P0 moment:
- Is the data that feeds it static or live?
- If static: is it seeded and verified?
- If live: is the API available and responding?
- Is there a fallback if it fails?

### Step 3 — Run the critical path

```bash
# Minimal demo readiness check pattern
[reset script]    → clean state, seed data
[main demo flow]  → run it once, capture output
[verify]          → check integrity (if applicable)
[confirm output]  → does it look exactly like it should in front of an audience?
```

### Step 4 — Go / No-Go

Produce a checklist:

```
DEMO READINESS — [date]

P0 checks:
  [OK/FAIL] Reset script runs without errors
  [OK/FAIL] Seed data loads correctly
  [OK/FAIL] Main demo flow produces expected output
  [OK/FAIL] Notifications fire (or mock fires cleanly)
  [OK/FAIL] Verify / tamper show works

Go/No-Go: GO / NO-GO

Blockers (if NO-GO):
  • [specific thing that must be fixed]

Acceptable gaps (proceed anyway):
  • [things that are mocked or missing but won't be noticed]
```

---

## Rules during demo readiness

- Do not add features
- Do not refactor anything
- Do not fix non-blocking issues
- Only fix what would cause visible failure during the demo path
