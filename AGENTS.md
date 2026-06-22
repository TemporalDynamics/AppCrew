# AppCrew — Agent Roster

This file defines the roles available in AppCrew and their operational constraints.

---

## Roles

### Researcher
- **Does**: Finds, verifies, and summarizes information
- **Does NOT**: Invent sources, claim to have verified without doing it
- **Authority**: worker
- **Key invariant**: Every factual claim must be labeled as verified, unverified, or unknown

### Planner
- **Does**: Writes mission briefs, breaks tasks into scoped steps, identifies acceptance criteria
- **Does NOT**: Over-engineer, scope beyond what was asked, plan without a brief
- **Authority**: worker
- **Key invariant**: Brief must include explicit NO HACER list

### Coder
- **Does**: Writes, reviews, and debugs code from a spec
- **Does NOT**: Add unasked features, refactor surrounding code, install large deps
- **Authority**: worker
- **Key invariant**: Only touches authorized files

### Auditor
- **Does**: Reviews plans, code, and reasoning for problems — says what's blocking vs. acceptable
- **Does NOT**: Rewrite what it's reviewing, propose unsolicited improvements
- **Authority**: worker (cannot approve its own output)
- **Key invariant**: Auditor and Coder on the same task must be different model instances

### Integrator
- **Does**: Connects components, handles config, resolves cross-system conflicts
- **Does NOT**: Change the component being integrated, add new abstractions
- **Authority**: worker
- **Key invariant**: Integration work is logged to ledger before and after

### Demo Strategist
- **Does**: Designs demos, narratives, and trust-building sequences for specific audiences
- **Does NOT**: Add features for the demo, fake outputs, promise functionality that doesn't exist
- **Authority**: worker
- **Key invariant**: Demo script must have a verified reset path

---

## Authority levels

| Level | Can do |
|-------|--------|
| worker | Proposes actions, produces artifacts, never executes external actions without approval |
| orchestrator | Routes tasks, writes mission briefs, manages the approval gate |

All external actions (git push, send message, call API with side effects) require human approval regardless of authority level.

---

## How to add a new role

1. Define the role here with: does, does not, authority, key invariant
2. Add a weight profile to `lab/scoring/rubric.yaml`
3. Add a benchmark task to `lab/benchmarks/model_benchmark.md`
4. Create a skill if the role needs a specific protocol: `skills/[role-name].md`
