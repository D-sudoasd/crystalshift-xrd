# Contributing

Thank you for improving the Orthorhombic XRD Simulator.

## Before Opening a Pull Request

Run the Python checks from the repository root:

```bash
python -m pytest -q
python -m ruff check .
python -m basedpyright
python -m compileall -q orthoxrd tests app.py
```

For changes to the Live Canvas component, also run:

```bash
cd frontend
bun install
bun test
bun run typecheck
bun run build
```

Keep scientific changes accompanied by regression tests that state the relevant unit, boundary, normalisation, or physical invariant. Do not describe calculated model intensity as experimental absolute intensity.

Please keep generated caches, local exports, Playwright sessions, and QA screenshots out of commits. The repository's `.gitignore` already covers the standard local artifacts.
