# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal Information Manager — a Python CLI application for managing user records. This is a Python learning project. The codebase was cleared in November 2024 and may be restarted.

## Previous Architecture (from git history)

The original codebase followed this structure:

- **`main.py`** — Entry point. Calls `CMDViewer.start_simulate_gui(username)`.
- **`DataClass/`** — User model hierarchy: `Userbase` (base class) → `Admin` (permission_level=0) and `CommonUser` (permission_level=2). Users have uid, username, age, password, emails list.
- **`Utils/`** — `Configuration.py` (path constants for data storage), `Initialization.py` (creates data directories), `UserData.py` (save/load users as pipe-delimited text files, user registration).
- **`Views/`** — `CMDViewer.py` — Terminal-based menu loop (display users, register user, exit). Clears screen between views.
- **`DataFiles/Users/user_data.txt`** — Plain text persistence for user records.
- **`Tests/`** — Test directory (was empty).

## Key Patterns from Previous Implementation

- No external dependencies beyond Python stdlib (the old code had a stray `sqlalchemy` import in `UserData.py` which was unused).
- Text-file persistence: users serialized as `uid\tusername\tpassword\tpermission_level\tage\temails` — one record per line, emails stored as Python list literals parsed with `eval()`.
- Module-level imports in `__init__.py` files to re-export classes (e.g., `from .UserBase import Userbase`).
- No setup.py, requirements.txt, or virtual environment — run directly with `python main.py`.
