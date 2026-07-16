# SkillDiff

**Compare AI skill versions. Detect behavioral changes. Assess security risk.**

SkillDiff is an open-source CLI tool for AI Platform and Security Engineers. It compares two versions of an AI skill definition and reports *what changed behaviorally*, not just what text differed.

```
skilldiff compare examples/old_skill.yaml examples/new_skill.yaml
```

---

## Why SkillDiff?

Traditional `git diff` shows you what text changed.

SkillDiff tells you:
- The AI can now **send emails** (new tool added)
- The AI gained **filesystem write** permission (Critical severity)
- The **model changed** from `gpt-4o-mini` to `gpt-4o`
- **Risk score: 72/100 — High**

No LLM required. No cloud. Fully deterministic.

---

## Architecture

```
CLI (cli.py)
 └─► Loader (loader.py)          — reads YAML / JSON
      └─► Normalizer (normalizer.py)    — converts to SkillModel
           └─► Semantic Engine (semantic_engine.py) — detects changes
                └─► Risk Engine (risk_engine.py)    — scores via YAML rules
                     └─► Report (report.py)          — CLI / JSON / HTML
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full internals documentation.

---

## Installation

```bash
pip install skilldiff
```

Or from source:

```bash
git clone https://github.com/Irtaqa007/skill-diff
cd skill-diff
pip install -e .
```

---

## Quick Start

```bash
# Compare two skill versions
skilldiff compare examples/old_skill.yaml examples/new_skill.yaml

# Get JSON output
skilldiff compare old.yaml new.yaml --json

# Generate HTML report
skilldiff compare old.yaml new.yaml --html report.html

# Use custom risk rules
skilldiff compare old.yaml new.yaml --rules my_rules.yaml
```

---

## Commands

| Command | Description |
|---------|-------------|
| `skilldiff compare old.yaml new.yaml` | Compare and print CLI report |
| `skilldiff report old.yaml new.yaml` | Generate HTML report |
| `skilldiff --version` | Show version |
| `skilldiff --help` | Show help |

---

## Risk Levels

| Level | Score | Meaning |
|-------|-------|---------|
| Critical | 80-100 | Immediate review required before deploy |
| High | 50-79 | Security team sign-off required |
| Medium | 20-49 | Engineering review recommended |
| Low | 1-19 | Minor changes, low risk |
| None | 0 | No behavioral changes detected |

---

## Custom Rules

Create a `rules.yaml` to override default severity:

```yaml
permissions:
  shell.execute:
    severity: Critical
    recommendation: "Requires CISO approval."
  filesystem.write:
    severity: Critical
tools:
  send_email:
    severity: High
```

---

## Roadmap

- [ ] Git integration (`skilldiff git HEAD~1 HEAD skill.yaml`)
- [ ] CI/CD pipeline integration (GitHub Actions)
- [ ] Policy-as-code (OPA/Rego rules)
- [ ] Diff history tracking
- [ ] Multi-skill batch comparison
- [ ] Auto-fetch comps from Attom/Zillow

---

## Contributing

1. Fork the repo
2. Create a feature branch
3. Write tests — `pytest tests/ -v`
4. Submit a PR

---

## License

MIT — see [LICENSE](LICENSE)
