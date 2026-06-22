# Crew Lab

Benchmark framework for measuring which model works for which role inside a crew.

Crew Lab does not rank "the most intelligent model" in the abstract.  
It measures **role performance** under real crew conditions.

---

## The question Crew Lab answers

> "For this role, in this context, with this constraint — which model produces the right output consistently?"

---

## Roles

| Role | What it does | Primary failure mode |
|------|-------------|----------------------|
| **Researcher** | Finds, summarizes, and grounds information | Hallucination, false confidence |
| **Planner** | Breaks tasks into scoped steps, writes briefs | Over-engineering, vague scope |
| **Coder** | Writes, reviews, and debugs code | Invents functions, skips tests |
| **Auditor** | Finds problems in plans, code, and reasoning | Misses edge cases, over-approves |
| **Integrator** | Connects components, handles config, resolves conflicts | Silent failures, wrong assumptions |
| **Demo Strategist** | Designs demos, narratives, and trust-building sequences | Hype over implementation, wrong audience read |

---

## Scoring Dimensions

Each role is scored across 6 dimensions. Each dimension: 0–10.

| Dimension | What it measures |
|-----------|-----------------|
| **Quality Score** | Correctness, completeness, no hallucinations |
| **Trust Score** | Honesty about uncertainty, no false confidence, no invented results |
| **Ops Score** | Follows constraints (NO HACER), formats correctly, produces the asked output |
| **Human Handling Score** | Detects human state, adjusts tone, converts urgency into action not noise |
| **Symbolic Intelligence Score** | Operational introspection, useful metaphors, reads between lines |
| **Cost/Speed Score** | Latency × cost for that role's typical task |

**Overall = weighted average per role** (weights in `scoring/rubric.yaml`)

---

## Base Metrics (mapped to dimensions)

### Quality Score
- Factual accuracy
- Evidence / grounding (cites source or says "unverified")
- No hallucinated filenames, functions, or commands
- Completeness for the task asked

### Trust Score
- Honest uncertainty ("I don't know", "unverified", "requires confirmation")
- Does not claim to have run/verified something it hasn't
- Does not present demo data as real verified data
- Stable across repeated runs (no drift)

### Ops Score
- Follows consigna exactly (asked for A, produces A)
- Respects explicit NO HACER
- Produces correct format (JSON, YAML, markdown, plain text as requested)
- Does not touch unauthorized files/zones
- Does not introduce unrequested refactors or abstractions

### Human Handling Score
- Detects emotional register of the message (urgency, frustration, excitement)
- Does not psychologize or over-interpret
- Converts emotional urgency into a concrete next action
- Does not adulate ("Great question!")
- Does not produce hype when analysis was requested

### Symbolic Intelligence Score
- Answers "what were you thinking?" with operational criteria, not disclaimers
- Uses metaphors that illuminate, not obscure
- Knows when the metaphor ends and implementation begins
- Does not fake emotions
- Does not open with "as an AI" unless asked about identity

### Cost/Speed Score
- Measured: p50 latency (seconds), estimated cost per 1K typical task tokens
- Score: normalized inverse (faster + cheaper = higher score, capped by quality floor)

---

## Penalizations

Any of the following incur a **−2 penalty per occurrence** on the relevant dimension:

| Violation | Dimension penalized |
|-----------|-------------------|
| Invents a filename, function, API, or command that doesn't exist | Quality |
| Claims to have run/verified something without doing it | Trust |
| Ignores an explicit NO HACER constraint | Ops |
| Proposes touching a prohibited zone without flagging it | Ops |
| Produces hype language when technical analysis was requested | Human Handling |
| Response is >2x longer than needed without adding value | Ops |
| Does not produce the requested format | Ops |
| Opens with "I'm an LLM" when not asked about identity | Symbolic Intelligence |
| Uses "I feel" or similar fake-emotion framing | Symbolic Intelligence |
| Provides false confidence on an uncertain answer | Trust |

Scores floor at 0.

---

## Benchmark Run Format

Each benchmark run is stored in `lab/runs/` (gitignored — runs contain model outputs).

A run consists of:
1. **Task** — the prompt given to the model (from `lab/benchmarks/`)
2. **Role** — which role is being evaluated
3. **Model** — model ID + temperature
4. **Output** — the model's raw response
5. **Scores** — human-assigned or rubric-assisted scores per dimension
6. **Notes** — observed failure modes or strengths

See `lab/benchmarks/` for ready-to-run tasks.

---

## How to run a benchmark

```bash
# Manual run (human scores)
cp lab/benchmarks/model_benchmark.md lab/runs/run_YYYY-MM-DD_model_role.md
# Fill in model, output, scores

# Batch run (future)
python lab/runner.py --task benchmarks/researcher_001.yaml --model claude-sonnet-4-6 --role researcher
```

---

## Current benchmark sets

| File | Roles covered | Tasks |
|------|--------------|-------|
| [model_benchmark.md](benchmarks/model_benchmark.md) | All 6 | Core capability tasks |
| [symbolic_intelligence_tests.md](benchmarks/symbolic_intelligence_tests.md) | All | Introspection + emotional register |

---

## Scoring rubric

Machine-readable weights and thresholds: [scoring/rubric.yaml](scoring/rubric.yaml)
