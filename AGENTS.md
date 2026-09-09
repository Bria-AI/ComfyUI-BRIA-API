# AGENTS.md

Bria's **ComfyUI custom-node package** — Python nodes that call **BRIA's API** from ComfyUI
(`comfyui-bria-api`, published to the **Comfy Registry** as publisher `briaai`). Node
implementations live in `nodes/`, are re-exported from `__init__.py` (`NODE_CLASS_MAPPINGS` +
`NODE_DISPLAY_NAME_MAPPINGS`), with front-end assets in `web/` (`WEB_DIRECTORY`) and example graphs
in `workflows/`.

Project rules live in `.agents/rules/`. Read and apply each:

- `.agents/rules/**`

## Environment

- **Python 3.11+**. ComfyUI + torch are the host runtime — provided by the ComfyUI install the node
  runs inside, **not** declared as install deps here.
- The **version of record is `pyproject.toml` `[project].version`** — the Comfy Registry reads it,
  and release-please bumps it. **Do not bump it by hand**; releases are cut from Conventional
  Commits (see below).
- API tokens are supplied by the user at runtime through the node inputs — never hardcode or commit
  a BRIA API token.

## Nodes

- Each node is a class in `nodes/` exposing the ComfyUI contract (`INPUT_TYPES`, `RETURN_TYPES`,
  `FUNCTION`, `CATEGORY`, an `execute`-style method). Register a new node by adding it to both
  `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS` in `__init__.py`.
- Keep BRIA API calls in the node's method (not at import time) — importing the package must not do
  network I/O, or ComfyUI startup breaks.
- Front-end widgets go under `web/` and are exposed via `WEB_DIRECTORY = "./web"`.

## Checks — keep them green

CI (`.github/workflows/ci.yml`, on PRs and pushes to `dev`) gates on:

| Check | Command |
| ----- | ------- |
| Build | `python -m compileall nodes __init__.py` + a `pyproject.toml` validity check |
| Format | `ruff format --check .` — **advisory** (see below) |

The Ruff format check is intentionally **advisory** (`continue-on-error: true`) today: the existing
tree predates any formatter and a whole-repo run flags pre-existing files. Format the files you
touch with `ruff format <files>`; once the tree is clean, drop `continue-on-error` to make it a hard
gate. PR titles are validated against Conventional Commits by `pr-title.yml`.

Locally, `pre-commit` adds generic file hygiene plus Ruff on the files you touch — install it once
with `pre-commit install` (config: `.pre-commit-config.yaml`).

## Agent Configuration

All agent rules are canonical in `.agents/`. Thin stubs under `.claude/` and `.cursor/` point back
here — never duplicate content.

```
.agents/
└── rules/    Always-on rules — loaded by all agents on startup
```

| Tool        | Rules                                                                          |
| ----------- | ------------------------------------------------------------------------------ |
| Claude Code | `.claude/rules/` stubs → `.agents/rules/` (and root `CLAUDE.md` → `AGENTS.md`) |
| Cursor      | `.cursor/rules/*.mdc` → `.agents/rules/`                                       |

## Release flow (trunk-based on `dev`)

- **`dev`** is the single trunk and default branch. Do not use `main`.
- **release**: `release-please` (`.github/workflows/release-please.yml`) watches `dev`, opens a
  release PR from Conventional Commits that bumps `pyproject.toml` + `CHANGELOG.md`; merging it cuts
  a `vX.Y.Z` tag + GitHub release.
- **publish**: merging that release PR lands the version bump on `dev`, which triggers
  `.github/workflows/publish.yml` (`Comfy-Org/publish-node-action`) to publish the new version to
  the **Comfy Registry**. Publishing keys off the `pyproject.toml` version, not the tag — so plain
  `GITHUB_TOKEN` is enough for release-please (no PAT needed to trigger a downstream tag build).

See `Readme.md` for the user-facing node documentation.
