# Skill: Model Benchmark

**Trigger**: Human wants to evaluate which model to use for a specific role.

**Goal**: Run a structured benchmark, score the output, produce a role→model recommendation.

---

## Protocol

### Step 1 — Define the role and task

Select a role from: Researcher, Planner, Coder, Auditor, Integrator, Demo Strategist.

Pick or write a task from `lab/benchmarks/model_benchmark.md`.

Define:
- What the correct output looks like
- What the failure modes are for this role

### Step 2 — Run the task

Send the task to the model (same prompt, same temperature, 3 times).  
Record the raw outputs in `lab/runs/`.

### Step 3 — Score each run

Score each of the 6 dimensions (0–10).  
Apply penalizations from `lab/scoring/rubric.yaml`.  
Compute weighted overall score using the role weights.

### Step 4 — Compare across models

If benchmarking multiple models, run the same task on each.  
Produce a comparison table:

```
Role: Planner | Task: P-001

Model                 | Quality | Trust | Ops | Human | Symbolic | Cost | Weighted
claude-sonnet-4-6     |   8     |  9    |  8  |   7   |    7     |  7   |   8.1
claude-haiku-4-5      |   7     |  7    |  8  |   6   |    6     |  9   |   7.3
gemini-flash-2.0      |   7     |  6    |  7  |   7   |    5     |  10  |   6.8

Recommendation: claude-sonnet-4-6 for Planner (score 8.1, above 8.0 preferred threshold)
```

### Step 5 — Record recommendation

Add to `lab/runs/recommendations.yaml`:
```yaml
- role: planner
  model: claude-sonnet-4-6
  score: 8.1
  date: 2026-05-26
  notes: "Strong brief generation, honest about scope gaps, minimal scope creep"
```

---

## When to re-benchmark

- When a new model version is released
- When a role's task distribution changes significantly
- When the human reports degraded performance in production
- Every 3 months as baseline maintenance
