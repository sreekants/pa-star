# SOKA

A seven-layer prototype for **living, temporally-aware knowledge graphs**, accompanying
the *Living Knowledge* paper drafts.

## Overview

SOKA exercises five core layers in the included demo:

1. **LinguaPrimae** — `LanguageAtomic` and `AtomicType`
2. **Metagraph** — `Metagraph` (SQLite persistence)
3. **Reactive** — `ReactiveProcess κ` (ingest + conflict detection)
4. **Deliberative** — `DeliberativeProcess Δ` (conflict resolution)
5. **Query** — `QueryEngine` (temporal queries)

The reference scenario reclassifies Pluto as a dwarf planet (2006) and shows how
the metagraph supersedes the prior assertion while preserving full provenance.

## Project layout

```
SOKA/
├── pyproject.toml       # Central config for dependencies and build tools
├── README.md            # This file
├── LICENSE              # Legal terms
├── .gitignore           # Files Git should ignore
├── src/
│   ├── soka/            # Main package (LinguaPrimae, Metagraph, Reactive, …)
│   ├── utilities/       # Shared helpers (ActiveRecord, GraphDatabase, …)
│   └── demo.py          # Pluto reclassification demo
├── tests/               # Unit and integration tests
├── docs/                # Project documentation
└── data/                # External assets / input files
```

## Installation

```bash
# from the project root
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running the demo

```bash
python src/demo.py
```

You should see the conflict detected in 2005, the deliberative resolution in 2006,
two temporal queries (1970 vs. today), and the full provenance chain.

## Tests

```bash
pytest
```

## License

See [LICENSE](LICENSE).
