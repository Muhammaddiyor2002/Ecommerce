# Contributing to NovaCommerce Core

## Workflow

1. Fork & clone.
2. Create a feature branch: `git checkout -b feat/<short-description>`.
3. Make focused commits.
4. Run lint + tests locally:
   ```bash
   ruff check . && ruff format --check .
   DJANGO_SETTINGS_MODULE=novacommerce.settings.test \
   PYTHONPATH=django_app pytest
   ```
5. Push and open a PR against `main`.

## Code style

* Python 3.13+, type hints encouraged.
* Ruff is the linter + formatter (configured in `pyproject.toml`).
* Conventional commits encouraged (`feat:`, `fix:`, `chore:` …).

## Pull request checklist

The PR template asks you to confirm:

* [ ] Tests added / updated
* [ ] Migrations apply cleanly
* [ ] Lint + format passes
* [ ] Doc updates if behaviour changes

## Reporting security issues

Please **do not** file a public issue. Email maintainers directly.
