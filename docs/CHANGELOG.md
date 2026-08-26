# Changelog

All notable changes to this project will be documented in this file.

## [1.1.1] - 2026-08-26

### Auction House Bot Setup Hardening
- **Character GUID Validation**: Added `verify_character_guid` in `skirmish/menu.py` to validate character existence and prevent server crashes caused by assigning playerbot characters (`rndbot*` prefixes).
- **Bot Filtering in Character List**: Updated database selection query in `show_database_characters_menu` to join character and account tables, filtering out bot accounts matching the configured prefix.
- **Enablement Safeguard**: Blocked enabling the Auction House Bot when no valid character GUID is configured (GUID set to `0` or empty).
- **Unit Tests**: Added test cases for verifying bot character rejection, missing character validation, and blocked enablement in `tests/test_menu_py.py`.

## [1.1.0] - 2026-08-26

### Skirmish Mode PvP Brackets & Scheduler Guards
- **Dynamic Fixed Level Bracket Span**: Updated skirmish presets to calculate `RandomBotFixedLevel` using a span limit check (`max_lvl - min_lvl <= 20`), resolving issues with custom wide ranges (e.g. `10-60`) locking bot XP, while keeping narrow low-level brackets (like `1-20`) locked.
- **Level Brackets Scheduler Bypass**: Guarded `RandomBotLevelMgr::Update` in the `mod-playerbots` C++ module to prevent the background Level Brackets distributor scheduler and level resets from overriding fixed level PvP brackets when `randomBotFixedLevel` is enabled.
- **Player Level Sync Restore**: Implemented backup and restoration of `AiPlayerbot.SyncLevelWithPlayers` using `AiPlayerbot.SyncLevelWithPlayers.Backup` to preserve user preferences when switching modes.
- **Unit Tests**: Added coverage for fixed level span configurations and SyncLevelWithPlayers preferences.

## [1.0.9] - 2026-08-26

### Expansion Setup & Configuration Integration
- Fixed a conflict with the **Level Brackets Subsystem**: When selecting Classic Mode (Level 60) or TBC Mode (Level 70), the distributor scheduler is now dynamically disabled (`AiPlayerbot.LevelBrackets.Enabled = 0`) to prevent it from redistributing bots into level ranges 61–80. Choosing WotLK Mode (Level 80) re-enables it (`1`).
- Resolved the **Level Reset Subsystem Misalignment**: Preset actions now dynamically configure `AiPlayerbot.ResetBotLevel.MaxLevel` to match the exact max level cap of the selected mode, ensuring reset triggers fire properly for capped bots.
- Fixed **Stale Bot Level Persistence (Without Purge)**: Implemented `delete_bots_outside_range(min_lvl, max_lvl)` to cleanly delete over-leveled and out-of-range bots and their orphaned database records when a user declines the full bot purge prompt on expansion preset swaps or skirmish setups.
- Resolved **Forced Level 1 Spawns Persistence**: Switching to expansion presets now resets `AiPlayerbot.DisableRandomLevels` to `0` to prevent bots from remaining stuck at Level 1 in starting zones.
- Updated the unit tests in `tests/test_menu_py.py` to assert correct setting changes across the new presets.


## [1.0.8] - 2026-08-26

### Skirmish PvP Bracket & Fixed Level Alignment
- Configured dynamic `AiPlayerbot.RandomBotFixedLevel` rules in `skirmish/menu.py`:
  - **Full Expansion Progression (1-60 Classic, 1-70 TBC, 1-80 WotLK)**: `AiPlayerbot.RandomBotFixedLevel = 0` (bots gain experience and level up naturally through questing and combat).
  - **Skirmish PvP Brackets (e.g. 10-20, 20-30, 30-40, 40-50, 50-60, 60-70, 70-80)**: `AiPlayerbot.RandomBotFixedLevel = 1` (bots remain locked within their bracket level range without gaining XP).
- Updated Skirmish Mode Setup sub-menu choices in `skirmish/menu.py` to present 10-level differential PvP brackets: `Bracket 10-20`, `Bracket 20-30`, `Bracket 30-40`, `Bracket 40-50`, `Bracket 50-60`, `Bracket 60-70`, `Bracket 70-80`, and `Custom Level Range`.
- Ensured expansion setup and skirmish presets synchronize map unlocks (`0,1` for <=60, `0,1,530` for 61-70, `0,1,530,571` for 71-80) and Individual Progression settings (`StartingProgression`, `ProgressionLimit`, `BotAccountsMaxLevel`).
- Expanded unit tests in `tests/test_menu_py.py` and `tests/test_menu.py` covering 10-level brackets, level 1 natural leveling (`RandomBotFixedLevel = 0`), and locked bracket leveling (`RandomBotFixedLevel = 1`).


## [1.0.7] - 2026-08-26

### Menu Hierarchy & Terminology Refinement
- Reorganized `skirmish/menu.py` menu hierarchy: moved **Skirmish Mode [Quick PvP]** into **Bot Management & Population** as a sub-menu option (Option 2).
- Updated menu titles, option descriptions, and console logs to emphasize **PvP activity** instead of RPG activity:
  - Renamed "Open World RPG Activity Presets" to **"Open World PvP & World Activity Presets"**.
  - Updated preset Option 1 to **"Balanced PvP & World Activity (Default)"**.
  - Updated `rpg_weight_preset_action` print messages to display `"Open World PvP & World Activity"`.
- Re-indexed main menu and sub-menu option numbers in `skirmish/menu.py`, `README.md`, `docs/CONFIGURATION.md`, and unit tests (`tests/test_menu_py.py` and `tests/test_menu.py`).


## [1.0.6] - 2026-08-26

### Skirmish Mode & Individual Progression Alignment
- Synchronized Individual Progression (`env/dist/etc/modules/individualProgression.conf`) settings with Skirmish Mode PvP brackets, Expansion presets, and Custom level ranges in `skirmish/menu.py`.
- Dynamic alignment configures maps, starting progression stage, progression limit, and bot level caps according to chosen level range:
  - **Classic (<= 60)**: Maps `0,1`, `StartingProgression = 0` (Vanilla phase), `ProgressionLimit = 7` (Level 60 cap).
  - **TBC (61-70)**: Maps `0,1,530`, `StartingProgression = 8` (Dark Portal & Outland unlocked), `ProgressionLimit = 13` (Level 70 cap).
  - **WotLK / Custom Wide Ranges (71-80, e.g. 70-80, 1-80, 20-79)**: Maps `0,1,530,571`, `StartingProgression = 13` (Northrend & WotLK unlocked), `ProgressionLimit = 0` (WotLK level 80 cap).
- Updated `DockerService.reload_worldserver_config()` in `skirmish/menu.py` to touch both `playerbots.conf` and `individualProgression.conf` for live hot-reloading in the worldserver.
- Added explicit user notifications and optional instant bot purge prompts to Bot Starting Level Mode (`Option 4 -> 3`), Expansion Setup (`Option 3`), Bot Population Density (`Option 4 -> 1`), and Skirmish Brackets (`Option 2`), ensuring users are informed when database bot records require a purge to take full effect.
- Expanded test suite in `tests/test_menu_py.py` with `individualProgression.conf` isolation and assertions across expansion and skirmish bracket presets.

### Module Defaults & Config Fixes
- Fixed hardcoded dev character GUID (`55`) and dev-session settings (`EnableSeller = true`, `Buyer.Enabled = true`) in `env/dist/etc/modules/mod_ahbot.conf`, restoring clean release defaults (`GUIDs = 0`, `EnableSeller = false`, `Buyer.Enabled = false`).
- Corrected duplicate example comment lines in `mod_ahbot.conf`.
- Fixed leftover dev skirmish level cap (`BotAccountsMaxLevel = 45`) in `env/dist/etc/modules/individualProgression.conf`, restoring Classic 1-60 defaults (`BotAccountsMaxLevel = 60`, `ProgressionLimit = 7`).
- Updated `expansion_preset_action` in `skirmish/menu.py` to set `AiPlayerbot.RandomBotMinLevel = 1` and synchronize `IndividualProgression.BotAccountsMaxLevel` alongside map unlocks and progression limits when switching expansion modes.
- Extended test suite in `tests/test_menu_py.py` to assert `AiPlayerbot.RandomBotMinLevel = 1` across all expansion preset tests.


## [1.0.5] - 2026-08-26

### Control Hub & Build Validation
- Added `DockerService.are_images_built()` to `skirmish/menu.py` to inspect local Docker image presence (`acore/ac-wotlk-worldserver:skirmish`, `acore/ac-wotlk-db-import:skirmish`, `acore/ac-wotlk-authserver:skirmish`).
- Centralized image build execution: `DockerService.start_stack()` now prompts to invoke `DockerService.build_images()` (which auto-heals git submodules and runs `docker compose build`) if images are unbuilt, guaranteeing consistent Docker Compose build execution regardless of which flow triggers server startup (Start Server, Account Wizard, Admin Console, LAN Setup, Bot Purge, AH Bot Setup).
- Integrated Docker image presence verification into Health Check / System Doctor (Option 1 -> 7).
- Added unit tests in `tests/test_menu_py.py` verifying image validation logic and seamless build prompt handling.


## [1.0.4] - 2026-08-26

### Control Hub & Server Management
- Updated `skirmish/menu.py` Server Stop action to execute `docker compose down` directly without prematurely aborting on container status checks.
- Added **Wipe Server Setup** option to `skirmish/menu.py` (Option 8 in Server Controls & Admin) to remove containers, database volumes (`-v`), networks, and built images (`--rmi all`), requiring explicit `"delete"` confirmation before execution.
- Added **Automated Account Creation Wizard** to `skirmish/menu.py` (Option 4 in Server Controls & Admin) supporting custom username, password, and GM rank selection (Player, Moderator, GameMaster, Admin).
- Implemented native Python **SRP6 Salt & Verifier Generator** (`generate_srp6_verifier`) matching AzerothCore WotLK authentication algorithms in `skirmish/menu.py`, enabling direct MySQL account provisioning that supports immediate WoW client login.
- Configured `AiPlayerbot.AutoTeleportForLevel = 1` as default in `env/dist/etc/modules/playerbots.conf` so high-level bots automatically teleport to level-appropriate zones upon spawn/login.
- Added **Bot Starting Level Mode** option (Option 3 in Bot Management & Population) in `skirmish/menu.py`, enabling users to toggle forced Level 1 starter spawns (`DisableRandomLevels = 1`) with optional instant bot account purge & repopulation.
- Streamlined **AH Bot Setup** in `skirmish/menu.py` with an **Interactive Setup Wizard**, real-time status banners, automatic MySQL character GUID detection, step-by-step creation guides (suggesting character name `Auctioneer`), and warnings against entering the game world on bot characters.
- Updated `docs/MODULES.md` with streamlined `mod-ah-bot` configuration & character setup steps.
- Expanded Pytest suite (`tests/test_menu_py.py`) to cover Account Creation Wizard, SRP6 verifier generation, Bot Starting Level Mode, AH Bot Setup, and Wipe Server confirmation safeguards.


## [1.0.3] - 2026-08-26

### Submodule Resolution & Auto-Healing
- Resolved dangling submodule pointer by publishing `mod-acore-mall` to [Of-Arte/Acore_Mall](https://github.com/Of-Arte/Acore_Mall) and updating `.gitmodules`.
- Added automatic submodule detection and initialization (`DockerService.ensure_submodules()`) to `skirmish/menu.py` before Docker image builds.
- Integrated submodule auto-healing checks into the Control Hub System Doctor / Health Checker.
- Updated `README.md` installation instructions with `--recurse-submodules` cloning guidance.

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


