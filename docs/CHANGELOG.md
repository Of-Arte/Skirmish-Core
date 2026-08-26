# Changelog

All notable changes to this project will be documented in this file.

## [1.0.2] - 2026-08-25

### Module Auto-Import & Fixes
- Added `include.sh` and `conf/conf.sh.dist` for `mod-acore-mall` to enable automatic native database imports for GM Island vendors on fresh builds.
- Updated `cs_individualProgression.cpp` command security to `SEC_PLAYER` for player-facing `.ip` subcommands (`.ip get`, `.ip setbot`, `.ip setrep`, `.ip pvp`, `.ip attune`).
- Enabled `AiPlayerbot.LevelBrackets.Enabled = 1` and `AiPlayerbot.ResetBotLevel.Enabled = 0` in `playerbots.conf` to prevent high-level bots from demoting to starter zones.

### Control Hub & Diagnostics
- Added host/WSL system RAM diagnostics with low-memory warnings and Smart Scale recommendations in `skirmish/menu.py`.
- Added real-time loading indicators (`flush=True`) across Docker CLI, container, and database diagnostic checks in `HealthChecker`.

## [1.0.1] - 2026-08-25

### Skirmish Control Hub & Compatibility
- Added Linux/macOS cross-platform fallbacks for console attachment (`docker attach`) and live log streaming (`docker compose logs -f`) in `skirmish/menu.py`.
- Created `menu.sh` shell launcher script for Linux/macOS environments.
- Added Option 6 ("Build Fresh Layer" `--no-cache`) to the interactive launcher menu.
- Extended Pytest test suite (`tests/test_menu_py.py`) with cross-platform OS tests.

### Configuration & Docker
- Added volume mounts for host `./data` and `./modules` into `ac-db-import` service container in `docker-compose.yml`.
- Tracked default `docker-compose.override.yml` in repository for zero-config Docker startup.
- Expanded module distribution configuration templates (`env/dist/etc/mod_ahbot.conf`, `env/dist/etc/individualProgression.conf`, and `env/dist/etc/modules/`) to silence missing property initialization warnings.

### Documentation & Submodules
- Consolidated root documentation into `docs/` and removed duplicate `CHANGES_FROM_UPSTREAM.md`.
- Aligned submodule paths (`modules/mod-ah-bot` & `modules/mod-acore-mall`) with upstream CMake script loader naming conventions.

## [1.0.0] - 2026-08-24

### Root
- Created parent-level project documentation, issue templates, and module inventory (`README.md`, `MODULES.md`, `NOTICE.md`, `CHANGELOG.md`).
- Created a Python interactive control hub (`skirmish/menu.py`) providing a user-friendly CLI interface for server management.
- Created comprehensive Pytest test suite (`tests/test_menu_py.py`).


