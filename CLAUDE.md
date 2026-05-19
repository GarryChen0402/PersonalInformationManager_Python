# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal Information Manager (PIM) — a Python Tkinter GUI application for managing personal information. This is a Python learning project. Zero external dependencies beyond Python stdlib.

## Architecture

4-layer architecture: **View → Service → Model → Storage**

- **`main.py`** — Entry point. Calls `ensure_directories()` then launches Tkinter `App`.
- **`Core/`** — Infrastructure: `Config.py` (path constants, `ensure_directories()`), `Storage.py` (JSONFileStorage base class with atomic writes), `Exceptions.py` (PIMException hierarchy).
- **`Models/`** — Python `@dataclass` classes with `from_dict()`/`to_dict()` methods. Re-exported via `__init__.py`.
- **`Services/`** — Business logic managers. Each references paths via `Config.SKILL_PATH` (module reference, not captured at import). Re-exported via `__init__.py`.
- **`Views/`** — Tkinter GUI pages. `App.py` (main window + status bar), `NavFrame.py` (left nav 150px), per-module pages, `Widgets.py` (shared controls).
- **`Data/`** — Auto-created data directories: `books/`, `backups/`, plus per-module JSON files.
- **`Tests/`** — Unit and integration tests (100 tests, zero dependencies).

## Key Patterns

- **Zero dependencies** — stdlib only. No pip install required.
- **JSON persistence** — `JSONFileStorage` base class provides CRUD, search, query. Atomic writes via tmp file + `os.replace()`. Auto UUID ids and timestamps.
- **Path references** — All service managers import `Core.Config` as a module and reference `Config.SKILL_PATH` etc. dynamically (NOT captured at import time via `from Core.Config import SKILL_PATH`). This allows tests to redirect data paths by modifying `Config` attributes.
- **Profile is singleton** — Stored as JSON object (not list). ProfileManager has its own `_load`/`_save` methods.
- **Password encoding** — base64 encode/decode (not encryption, just obfuscation).
- **PDF handling** — Header validation (`b"%PDF"` check), copied to `Data/books/` with UUID filename, opened via `os.startfile`/`subprocess`.
- **Same-day status** — Adding a status record for an existing date auto-updates the existing record.
- **GUI pattern** — Pages receive `set_status` callable (not raw Label). Page switching via `pack_forget()`/`pack()`. DashboardPage also receives `navigate` callback.
- **Views/Widgets.py** — Shared widgets: SearchBar, FormDialog (Toplevel modal), ConfirmDialog, DateRangePicker, StatsBar, KeywordEntry (tag chips).
- **Knowledge Model** — Single `KnowledgeItem` with `item_type` field ("note"/"ebook"). Unified category/keyword system.
- **Backup** — Full JSON backup with per-module selective restore. BackupManager uses `_module_paths()` function (not module-level dict) to resolve paths dynamically.
- **Tests** — Use temp directories. Redirect `Config.*` paths in `setUpClass`/`tearDownClass`. Call `os.remove()` in `setUp` for clean state.
- **No setup.py, requirements.txt, or virtual environment** — run directly with `python main.py`.
