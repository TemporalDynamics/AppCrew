# AppCrew

A portable agent crew for getting apps running, fixed, and verified.

---

## What it is

AppCrew is an operational harness that brings a structured agent crew to any repository.

The crew doesn't work loose. It works from a **brief** — a written scope with objective, context, constraints, and evidence required before closing a task. Every action is logged to a verifiable ledger. Every decision requires human approval to proceed.

## The formula

```
AppCrew (global)   = executes
.crew/ (per repo)  = instructs
verifiable-memory-mcp = corroborates
```

- **AppCrew** is the framework: harness, skills, adapters, templates.
- **`.crew/`** is the local profile inside each private repo: who the crew is, what they're allowed to do, what the acceptance criteria are.
- **verifiable-memory-mcp** is the ledger: append-only, hash-chained, tamper-detectable.

## Core concepts

- [Mission Capsule](HARNESS.md#mission-capsule) — minimum unit of crew work
- [Brief Protocol](HARNESS.md#brief-protocol) — the brief is more important than the agent
- [Crew S.O.S.](skills/sos.md) — emergency diagnostic, 3 options, wait for human input
- [Crew Lab](lab/README.md) — benchmark framework: which model works for which role
- [Operational Self-Description](HARNESS.md#operational-self-description) — how the crew answers "what were you thinking?"

## Structure

```
appcrew/
  core/          mission, brief, runner, evidence, sos, ledger
  skills/        sos, repo-diagnosis, demo-readiness, model-benchmark, ...
  adapters/      telegram, github, verifiable_memory_mcp
  templates/     crew-profile template (copy into .crew/ per repo)
  lab/           Crew Lab — model benchmarks and scoring
  verticals/     recruit/ — domain-specific crew extension
  examples/      fake-webapp — end-to-end example without real data
```

## Quickstart

```bash
# Copy the crew profile template into your repo
cp -r templates/crew-profile /your-repo/.crew

# Fill in .crew/START.md, RULES.md, COMMANDS.md, ACCEPTANCE.md

# Run a mission
python core/runner.py --brief .crew/brief.yaml
```

## What AppCrew is NOT

- Not a chatbot wrapper
- Not a code-execution sandbox
- Not an autonomous agent that acts without human approval
- Not a place for secrets, tokens, keys, or real client data

## Verticals

- [Recruit](verticals/recruit/README.md) — executive talent sourcing crew

## License

MIT
