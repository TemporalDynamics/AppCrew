# AppCrew Security

AppCrew is a public framework. The following rules govern what may and may not be committed to this repo.

---

## What MUST NOT appear in this repo

- `.env` files of any kind (real)
- API keys, tokens, passwords, secrets of any kind
- Real client names (unless explicitly approved for public use)
- Real candidate names, profiles, or recruiting data
- Real company-internal strategies or pricing
- Database dumps or SQLite files with real data
- Log files with real operational data
- Local filesystem paths (e.g. `/home/username/dev/...`)
- Patent drafts or provisional filing content
- Private chat logs or internal strategy documents
- Per-repo `.crew/` profiles from private repos (EcoSign, WITH, Global Executive, etc.)

---

## What IS allowed

- Framework code (generic, no real data)
- Skill definitions (generic protocols, no real commands for private repos)
- Templates with placeholder values
- Fake/fictional example data clearly labeled as such
- Adapter code without hardcoded credentials (use env vars, never hardcode)
- Public documentation

---

## Before any push to the public remote

Run this audit:

```bash
# Check for secrets patterns
grep -r "sk-" . --include="*.py" --include="*.ts" --include="*.yaml" --include="*.md" | grep -v ".gitignore"
grep -r "bot_token\|TELEGRAM_TOKEN\|OPENROUTER_KEY\|SUPABASE" . --include="*.py" --include="*.yaml" | grep -v ".env.example"

# Check for real names / paths
grep -r "/home/manu" . --include="*.py" --include="*.md" --include="*.yaml"
grep -rE "(EcoSign|ecosign|WITH internal|Global Executive real|Rodri|candidatos reales)" . --include="*.md"

# Check for database files
find . -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3"
```

All results must be empty before pushing.

---

## .env convention

Every adapter that needs credentials uses environment variables. The pattern:

```bash
# .env (never committed)
TELEGRAM_BOT_TOKEN=real_token_here

# .env.example (committed, safe)
TELEGRAM_BOT_TOKEN=your_token_here
```

Never hardcode credentials. Never commit `.env`.

---

## Private crew profiles

Each private repo has its own `.crew/` directory. Those profiles live inside the private repo — not in AppCrew.

AppCrew only ships the **template** (in `templates/crew-profile/`). The private profile is never migrated here.

---

## Reporting security issues

Open a GitHub issue with the label `security`. Do not include sensitive data in the issue.
