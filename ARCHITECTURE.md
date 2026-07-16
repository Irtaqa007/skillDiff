# SkillDiff — Architecture

## Module Responsibilities

| Module | Responsibility | Input | Output |
|--------|---------------|-------|--------|
| `loader.py` | Read YAML/JSON from disk | File path | Raw dict |
| `normalizer.py` | Convert raw dict to SkillModel | Raw dict | SkillModel |
| `semantic_engine.py` | Detect behavioral differences | Two SkillModels | DiffResult |
| `risk_engine.py` | Score changes using YAML rules | DiffResult | DiffResult (scored) |
| `report.py` | Render CLI, JSON, HTML output | DiffResult | str / stdout |
| `cli.py` | CLI entry point | CLI args | Exit code |
| `models.py` | Data classes | — | SkillModel, Change, DiffResult |
| `utils.py` | Full pipeline helper | File paths | DiffResult |

## Data Flow

```
File Path
   │
   ▼
loader.load_skill_file()
   │  Raw dict (YAML/JSON parsed)
   ▼
normalizer.normalize()
   │  SkillModel (normalized)
   ▼
semantic_engine.compare()
   │  DiffResult (changes detected)
   ▼
risk_engine.score()
   │  DiffResult (severities assigned, risk_score computed)
   ▼
report.print_cli_report() / to_json() / to_html()
   │  Output to stdout or file
   ▼
CLI exit code (1 if Critical changes, 0 otherwise)
```

## SkillModel Fields

```python
@dataclass
class SkillModel:
    metadata: dict       # name, version, author
    model: dict          # name, provider, temperature, context_window
    prompt: dict         # system, user, instructions
    tools: list[dict]    # [{name: "web_search"}, ...]
    permissions: list    # ["filesystem.read", "shell.execute"]
    resources: list      # [{type: "file", path: "..."}]
    memory: dict         # memory configuration
    network: dict        # {allowed_domains: [...]}
    environment: dict    # env vars and settings
```

## Risk Scoring

Scores are additive. Each change contributes:

| Severity | Points |
|----------|--------|
| Critical | 40 |
| High | 20 |
| Medium | 10 |
| Low | 2 |
| Info | 0 |

Final score is capped at 100. Risk level thresholds:
- Critical: ≥ 80
- High: ≥ 50
- Medium: ≥ 20
- Low: ≥ 1
- None: 0

## Extension Points

- **Custom rules:** Pass `--rules path/to/rules.yaml` to override severity assignments
- **New categories:** Add a `_compare_X()` function in `semantic_engine.py`
- **New report formats:** Add a function in `report.py`
- **New input formats:** Extend `loader.py` with new suffix handling
