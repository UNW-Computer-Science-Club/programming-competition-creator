# Programming Competition Creator

This program allows you to rapidly build programming competitions for Domjudge.

## Commands

- `progcc init` creates a starter `competition.yaml` and project structure.
- `progcc scaffold` creates missing files under `problems/` for each configured problem.
- `progcc build --output-dir build` builds contest metadata and problem zip archives for DOMjudge import.
- `progcc test --build-dir build` validates built problems with `verifyproblem`.
- `progcc publish --url <DOMJUDGE_URL> --username <USER> --password <PASS>` builds (unless `--skip-build`) and uploads the contest + problems directly through the DOMjudge API.

## Publishing to DOMjudge

The publish flow follows DOMjudge's bulk import order:

1. Create contest (`POST /api/v4/contests`) unless `--contest-id` is supplied.
2. Upload `problems.yaml` (`POST /api/v4/contests/{cid}/problems/add-data`).
3. Upload each problem archive (`POST /api/v4/contests/{cid}/problems` with `problem=<id>`).

Use `--contest-id` to publish into an existing contest instead of creating a new one.

## Problem ID Suffixes

`competition.yaml` supports an optional top-level `problemSuffix` field. When set, it is appended to each problem `shortname` in build output and publish uploads.

Example:

- `shortname: hello-world`
- `problemSuffix: -spring26`
- DOMjudge problem ID used for metadata/uploads: `hello-world-spring26`

This helps avoid collisions when DOMjudge already has problems with the same shortname.
