# Code Style

Conventions for this Bria **ComfyUI custom-node** package: **Python** nodes in `nodes/` calling
BRIA's API, front-end assets in `web/`.

## Formatting

- **Ruff** is the formatter/linter (`ruff format`, `ruff check`). Format with `ruff format <files>`
  before committing; do not hand-format.
- Format the files **you touch** — do not reformat the whole tree in a feature PR. The existing tree
  predates the formatter and has drift; a repo-wide reformat belongs in its own change. The CI
  format check is advisory for this reason (see `AGENTS.md`).
- There is no committed Ruff config yet; defaults apply. Introduce a `[tool.ruff]` config in its own
  change if wanted, not in a feature PR.

## ComfyUI nodes

- Each node is a class exposing the ComfyUI contract (`INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`,
  `CATEGORY`). Register it in **both** `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS` in
  `__init__.py`.
- **No network or heavy work at import time** — the package is imported on every ComfyUI startup.
  Keep BRIA API calls inside the node's execute method.
- `torch`/`comfy`/`folder_paths` etc. are host-provided by the ComfyUI runtime — import them, do not
  add them as install dependencies in `pyproject.toml`.
- Never hardcode a BRIA API token; it is a runtime node input.

## Versioning

- The version of record is `pyproject.toml` `[project].version`; it is bumped by release-please and
  read by the Comfy Registry. Never bump it by hand — releases are cut from Conventional Commits.

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/). Allowed types: `feat`, `fix`,
`docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`. PR titles are
enforced by the `pr-title` workflow (`amannn/action-semantic-pull-request`), and these types drive
release-please's version bumps.

```
feat: add FIBO edit node with structured instruction
fix: guard empty selection in Bria Multi Image Select
```

## Before You Commit

Install the hooks once (`pre-commit install`) so `.pre-commit-config.yaml` runs on every commit:
generic file hygiene plus Ruff on the files you touch. The build check
(`python -m compileall` + pyproject validation) runs in CI (`.github/workflows/ci.yml`).
