# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal-use FastAPI + server-rendered (Jinja2) web app for tracking a trading-card
inventory/investment business: purchases, grading submissions (PSA/CGC/BGS), sales, and
profit/loss in both USD and JPY. Single-user, local-only (SQLite), no auth.

## Commands

The venv lives in `env/` (already created via `python -m venv env`).

```bash
# install deps
pip install -r requirements.txt

# run the app (prod db at db/prod.db), opens browser at 127.0.0.1:8000
python main.py

# run in dev mode (uses db/dev.db instead, enables uvicorn --reload)
python main.py -d   # or --dev

# tests
pytest                                    # full suite
pytest tests/crud_test.py                 # one file
pytest tests/crud_test.py::test_name -v   # one test

# lint / format (ruff selects "ALL" rules, see pyproject.toml for the ignore list)
ruff check .
ruff format .

# type check (strict: disallow_untyped_defs, disallow_any_generics, etc.)
mypy .
```

`.pre-commit-config.yaml` runs `ruff-check`, `ruff-format`, `mypy .`, and `pytest` on every
commit — a commit will fail if any of these fail, so run them locally before committing.

Style notes from the ruff config: single quotes, 99-char line length, `py312` target.

## Architecture

Layered, roughly in dependency order:

- **`item_enums.py`** — plain `Enum` definitions (`Category`, `Language`, `Status`, `Intent`,
  `Qualifier`, `GradingCompany`, `ListingType`, `ObjectVariant`) plus two custom SQLAlchemy
  `TypeDecorator`s (`EnumInt`, `EnumList`) that (de)serialize enums to/from `Integer`/JSON-text
  columns. `Status` and `Intent` carry business rules as properties (`required_fields`,
  `required_to_be_null`, `allowed_statuses`) that drive both Pydantic validation and
  `validators.py` checks.
- **`database.py`** — engine/session setup. `get_engine()` reads the `DEV_MODE` env var (set by
  `main.py`) to pick between `db/dev.db` and `db/prod.db`; both are gitignored. `Base` adds a
  generic `__repr__`. `get_db()` is the FastAPI dependency that yields a `Session`.
- **`models.py`** — three SQLAlchemy models: `Item`, `Submission`, `GradingRecord` (the join
  table between an item and a submission — one `GradingRecord` per item per submission, so an
  item resubmitted after being cracked out has multiple records). Financial/derived fields
  (`total_cost`, `grade`, `cert`, `grading_company`, `return_jpy`, `net_percent`, etc.) are
  `hybrid_property`s: each has a plain-Python implementation *and* a `.expression`
  SQL-generating twin so the same property works both on a loaded instance and inside a SQLAlchemy
  query/filter. When changing one of these, update both halves and keep them equivalent — many
  fall back to raw `purchase_*` fields when there are no submissions yet, or to `RAW`/`None` when
  the item was cracked out of a holder (`cracked_from_purchase`) or the latest grading record
  `is_cracked`.
- **`orm_events.py`** — SQLite `PRAGMA foreign_keys=ON` on connect, and a `before_flush` listener
  that auto-deletes a `Submission` once its last `GradingRecord` is removed (so submissions never
  exist empty). Imported for side effects only (`main.py` does `import src.orm_events  # noqa: F401`).
- **`schemas.py`** — Pydantic models per entity in a `*Base` / `*Create` / `*Update` pattern
  (`extra='forbid'`). `*Base` model-level validators enforce the `Status`/`Intent` state machine
  (e.g. `Status.LISTED` requires `list_price`/`list_type`/`list_date` and forbids sale fields;
  date ordering like list-before-sale). Alongside these are plain `@dataclass` `*Form` /
  `*SearchForm` classes with `as_form`/`as_query` classmethods — these are the FastAPI
  `Depends(...)` targets that receive raw form/query strings, and each has a `to_item_create()` /
  `to_item_update()` / `to_item_search()` method that parses those strings (via `parsers.py`) into
  the typed Pydantic schema. This two-stage split exists because HTML forms only send strings.
- **`parsers.py`** — string → typed value helpers (`parse_nullable`, `parse_nullable_enum`,
  `parse_nullable_date`, `parse_to_qualifiers_list`, ...) used exclusively by the `*Form` classes
  in `schemas.py`.
- **`validators.py`** — cross-field/business-rule checks used by `crud.py` that need DB state
  (current `Item`/`GradingRecord`) rather than just the incoming payload, e.g. verifying an
  item's current `intent`/`status` before allowing a submission, or blocking status edits while
  `SUBMITTED`.
- **`crud.py`** — all DB access. Search (`search_for_items`) builds SQL filters from
  `ItemSearch` field names by convention: `_min`/`_max` suffixes become range filters on the
  matching column, everything else is exact-match; `qualifiers` and `grading_company` can't be
  expressed as simple column filters so they're applied as Python post-filters after the SQL
  query runs. `SubmissionNotFoundError`/`SubmissionNumberConflictError` are raised here and
  translated to HTTP responses in `routers.py`.
- **`routers.py`** — all HTTP endpoints (FastAPI `APIRouter`) and Jinja2 template rendering.
  Registers custom Jinja filters (`dollar`, `yen`, `decimal_yen`, `percent`, `enum`,
  `grading_company_enum_format`) used throughout `templates/`. Pagination is manual (`skip`/
  `show_limit` query params + `generate_page_urls`/`slice_items` helpers), not a library.
- **`main.py`** — app entrypoint. Sets `DEV_MODE` from the `-d`/`--dev` CLI flag *before*
  anything touches `database.py` (import order matters), creates tables on startup via
  `lifespan`, and opens a browser tab automatically.

### Request flow for a mutation (e.g. editing an item)

`templates/edit_item.html` form → `POST /edit/{item_id}` in `routers.py` →
`ItemUpdateForm.as_form` (raw strings) → `ItemUpdateForm.to_item_update()` (parses strings via
`parsers.py`, builds `ItemUpdate` Pydantic schema, which runs its `model_validator`s) →
`crud.edit_item()` (loads the `Item`, runs `validators.check_valid_intent_or_status_update`,
applies via `perform_item_update`, commits) → redirect.

### Tests

`tests/conftest.py` defines a session-scoped in-memory SQLite `engine` and a per-test
`db_session` fixture that wraps each test in a transaction it rolls back afterward, plus factory
fixtures (`item_factory`, `item_base_factory`, `item_create_factory`, `submission_factory`,
`grading_record_factory`, `item_with_submissions_factory`) for building model/schema instances
with sensible defaults. `client` gives a `TestClient` with `get_db` overridden to the test
session. Test files mirror `src/` modules 1:1 (`crud_test.py`, `models_test.py`,
`parsers_test.py`, `schemas_test.py`, `validators_test.py`).

## Preferences

  - Don't add comments explaining obvious code. Comments should only be used for non-standard
  approaches or subtle parts that could be confusing when looked at later on.
  - Don't write comments that only make sense in the context of a particular commit. Things
  such as 'now that ~~~' should not be written as they can be confusing later on.