# AppCrew — Roadmap

## Phase 1 — Framework (current)

- [x] Core harness (HARNESS.md, AGENTS.md)
- [x] Skills: S.O.S., Demo Readiness, Model Benchmark
- [x] Templates: crew-profile (START, RULES, ACCEPTANCE, HANDOFF)
- [x] Crew Lab: scoring rubric, 6-role benchmarks, symbolic intelligence tests
- [x] Security policy (SECURITY.md)
- [x] Vertical: Recruit (fictional demo)
- [ ] core/mission.py — Mission Capsule data class
- [ ] core/brief.py — Brief builder and validator
- [ ] core/sos.py — S.O.S. diagnostic runner
- [ ] core/ledger.py — Ledger adapter (wraps verifiable-memory-mcp)
- [ ] core/runner.py — Mission runner

## Phase 2 — Adapters

- [ ] adapters/telegram/ — Telegram notifier (env-var based, no hardcoded tokens)
- [ ] adapters/github/ — GitHub PR/issue adapter
- [ ] adapters/verifiable_memory_mcp/ — MCP ledger client

## Phase 3 — Lab automation

- [ ] lab/runner.py — automated benchmark runner (calls model APIs, scores output)
- [ ] lab/runs/recommendations.yaml — cumulative role→model recommendations
- [ ] CI job to run symbolic intelligence tests on each model release

## Phase 4 — Verticals

- [ ] verticals/recruit/ — complete fake demo, fake golden candidates, fake talent mission
- [ ] verticals/devops/ — deployment crew (diagnose, fix, verify)

## Not planned

- AppCrew will not ship with real client data
- AppCrew will not ship with hardcoded credentials
- AppCrew will not be an autonomous agent that acts without human approval
