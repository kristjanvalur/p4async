Workflows docs for p4async

This folder contains GitHub Actions workflows for the p4async project.

Release workflow (Release)
- File: `.github/workflows/release.yml`
- Triggers:
  - push on tags matching `v*` (real releases) and `t*` (test releases)
  - manual `workflow_dispatch` with inputs `publish_target`, `dry_run`, and `no_publish`
   - manual `workflow_dispatch` with inputs `publish_target` and `dry_run` (manual runs default to dry-run)

Inputs (for manual runs):
- publish_target (choice): `testpypi` (default) or `pypi`.
- dry_run (boolean): If `true`, the workflow runs tests and build but skips publishing; useful to validate the workflow without publishing.
 - dry_run (boolean): If `true`, the workflow runs tests and build but skips publishing; useful to validate the workflow without publishing. Manual dispatch defaults to `dry_run=true` for safety.

Behavior
- The workflow runs `test` -> `build` -> `publish-test`/`publish`.
- `publish-test` runs for `t*` tags or when manual dispatch selects `testpypi`.
- `publish` runs for `v*` tags or when manual dispatch selects `pypi`.
 - For manual dispatches, the workflow defaults to dry-run mode. Set `dry_run=false` to actually publish when using manual runs.

Examples
- Manually run a test publish without publishing (from Actions UI):
  - Actions → Release → Run workflow → set `publish_target=testpypi`, `dry_run=true` → Run workflow

- Trigger from gh CLI (example):
  - gh workflow run Release --ref main --field publish_target=testpypi --field dry_run=true

Notes
- CI (tests for PRs/pushes) is still handled by the `CI` workflow in `.github/workflows/ci.yml`.
- Release workflow runs tests inside the same workflow to ensure deterministic behavior and avoid cross-workflow coordination.

Developer formatting
--------------------

We use Ruff for formatting in CI. Before pushing changes, please run the formatter locally to avoid CI failures:

  uvx ruff format
