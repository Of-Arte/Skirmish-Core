```text
   _____ _  _______ _____  __  __ _____  _____ _    _  _____ ____  _____  ______ 
  / ____| |/ /_   _|  __ \|  \/  |_   _|/ ____| |  | |/ ____/ __ \|  __ \|  ____|
 | (___ | ' /  | | | |__) | \  / | | | | (___ | |__| | |   | |  | | |__) | |__   
  \___ \|  <   | | |  _  /| |\/| | | |  \___ \|  __  | |   | |  | |  _  /|  __|  
  ____) | . \ _| |_| | \ \| |  | |_| |_ ____) | |  | | |___| |__| | | \ \| |____ 
 |_____/|_|\_\_____|_|  \_\_|  |_|_____|_____/|_|  |_|\_____\____/|_|  \_\______|
```

[![Docker CI](https://img.shields.io/github/actions/workflow/status/Of-Arte/Skirmish-Core/docker-ci.yml?branch=dev&label=Docker%20CI&logo=docker&logoColor=white)](https://github.com/Of-Arte/Skirmish-Core/actions/workflows/docker-ci.yml)
[![Pytest](https://img.shields.io/github/actions/workflow/status/Of-Arte/Skirmish-Core/test-suite.yml?branch=dev&label=Pytest%20Suite&logo=pytest&logoColor=white)](https://github.com/Of-Arte/Skirmish-Core/actions/workflows/test-suite.yml)
![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat&logo=python&logoColor=white)

**SkirmishCore** is an AzerothCore Wrath of the Lich King 3.3.5a repack tailored for players seeking an offline World PvP-like WoW experience. Powered by intelligent Playerbots, dynamic economy controls, and an individual progression system.

SkirmishCore is built directly on top of the [mod-playerbots/azerothcore-wotlk](https://github.com/mod-playerbots/azerothcore-wotlk) fork of AzerothCore.

> **Disclaimer:** This is an independent repack project and is not officially affiliated with AzerothCore or any module developers. Created by a solo developer for personal use and to share with friends.

---

<p align="center">
  <img src="./docs/assets/menu.png?raw=true" alt="SkirmishCore Interactive Control Hub" width="600" />
</p>

## Default Server Configuration

SkirmishCore arrives pre-configured out of the box for a progressive, active single-player and small co-op World PvP experience. Key defaults include:

- **1–60 Classic Locked Progression**: Max bot level is capped at 60 and limited to Kalimdor and Eastern Kingdoms maps (0,1). Expansion content in TBC and WotLK remains progression-gated.
- **Natural Bot XP & Leveling**: `RandomBotFixedLevel = 0` is set for full expansion progression (1-60, 1-70, 1-80), allowing bots to level up naturally through questing and combat. Specific Skirmish PvP brackets (e.g. 10-20, 20-30, 70-80) automatically set `RandomBotFixedLevel = 1` to keep bots locked within their bracket level range.
- **Dynamic 1–60 Level Brackets**: `LevelBrackets.Enabled = 1` continuously distributes online bots across all leveling brackets 1–9, 10–19, 20–29, 30–39, 40–49, 50–59, and 60 across open world questing hotspots, dungeons, and capitals.
- **Independent Bot Level Scaling**: `SyncLevelWithPlayers = 0` ensures lower-level players encounter a fully populated world of all level ranges rather than scaling the world exclusively around player level.
- **High Bot Population Density**: Default bot population range is tuned to 1,000–2,000 active bots for a bustling MMO feel.
- **Automated Auction House & Economy**: System accounts (`AHSELLER`) and character seeds (`Auctioneer`) are automatically configured to drive an active in-game auction house.
- **Player Expansion Gating**: Includes `mod-individual-progression` so human players progress through classic raid tiers and attunements naturally before unlocking expansion content.

---

## Installation & Setup

Follow these steps in order to install, configure, and launch your server.

### 1. Clone Repository
```bash
git clone https://github.com/Of-Arte/Skirmish-Core.git
```
*(Submodules are automatically detected and initialized by the SkirmishCore Control Hub menu on launch).*


### 2. Prerequisites & System Requirements
- **Docker Desktop**: Host container engine for running authserver, worldserver, and database instances.
- **Python 3.8+**: Required runtime for the object-oriented SkirmishCore Control Hub menu scripts.
- **Pytest**: Optional. Test framework used for developer test suite (`pip install -r tests/requirements-test.txt`).


### 3. Launch Control Hub Menu
- **Windows (Primary)**: Double-click or run `menu.cmd` from the root directory:
  ```cmd
  menu.cmd
  ```
- **Linux / macOS**: Execute `skirmish/menu.py` using Python 3 (or `./menu.sh`):
  ```bash
  python3 skirmish/menu.py
  ```

#### Control Hub Menu Structure
```text
1. Server Controls & Admin
   ├── 1. Start Server
   ├── 2. Stop Server
   ├── 3. Build Server
   ├── 4. Create Game Account Wizard
   ├── 5. Admin Console
   ├── 6. Live Logs
   ├── 7. Health Check
   └── 8. Wipe Server Setup
2. Expansion Setup
   ├── 1. Classic WoW [Level 1-60]
   ├── 2. TBC Mode [Level 1-70]
   └── 3. WotLK Mode [Level 1-80]
3. Bot Management & Population
   ├── 1. Adjust Bot Population Density [Low, Medium, High, Custom]
   ├── 2. Skirmish Mode [Quick PvP] [Brackets 10-20 to 70-80, Custom Range]
   ├── 3. Open World PvP & World Activity Presets [Balanced, Questers, Grinders, PvP, Idlers]
   ├── 4. Bot Starting Level Mode [Force Level 1 vs Random Spawns]
   ├── 5. Reset & Purge Playerbots [Wipe & Respawn]
   └── 6. Auction House Bot Setup [Interactive Setup Wizard]
4. Multi-Player Setup [LAN / Public IP Setup]
```

### 4. Build Server Image
Before running the server for the first time, execute the build step to compile and prepare the containers:

1. Select **1. Server Controls** -> **3. Build Server**.
2. Wait for the compilation and build process to complete.

### 5. Start Server
1. Select **1. Server Controls** -> **1. Start Server**.
2. On first startup, the database assembler will automatically build and seed the AzerothCore database from scratch (including system accounts and auctioneer data).

### 6. Creating Accounts & Setting GM Rank
Once the server is running, create player/admin accounts using the interactive wizard or admin console:

1. Select **1. Server Controls** -> **4. Create Game Account Wizard** (or **5. Admin Console**).
2. Follow the prompt to set username, password, and GM rank level (0 = Player, 3 = Admin).

### 7. Connecting & Troubleshooting

If you experience difficulties logging into the server:
1. **Worldserver Startup Delay**: The worldserver container can take 5–15 minutes on first launch to initialize DBC/maps, load SQL updates, and spawn Playerbots. Check startup progress by selecting **1. Server Controls** -> **6. Live Logs** and wait until you see `World initialized`.
2. **Realmlist Configuration**: Ensure your WoW 3.3.5a client `Data/enUS/realmlist.wtf` or `Data/enGB/realmlist.wtf` is set to:
   ```text
   set realmlist 127.0.0.1
   ```
3. **LAN / Co-Op Access**: If hosting for friends on your local network or VPN, select **4. Multi-Player Setup** and enter your local IP. Connecting players must set their `realmlist.wtf` to that IP address:
   ```text
   set realmlist <YOUR_SERVER_IP>
   ```

---

## Configuration

All server and module configuration override files are located under the `env/dist/etc/` directory.

### Auction House Bot Setup (Optional)
By default, standard playerbots interact with the Auction House naturally. If you wish to enable the dedicated `mod-ah-bot` system to automatically populate or buyout AH listings:
1. Launch `menu.cmd` -> Select **3. Bot Management & Population** -> **6. Auction House Bot Setup**.
2. Select **1. Interactive AH-Bot Setup Wizard (Recommended)**.
3. Follow the 3-step wizard prompts to automatically create the account, log into WoW to create your character (suggested name: `Auctioneer`), and auto-link your character to AH Bot!

For details on generating configuration files, tuning bot progression, configuring Level 1 fresh server starts, and resetting bot accounts, see the dedicated [docs/CONFIGURATION.md](docs/CONFIGURATION.md) guide.


---

## Modules
This repack includes a set of pre-integrated Playerbot and gameplay modules. For a full inventory including exact Git commit hashes and configuration paths, see [docs/MODULES.md](docs/MODULES.md).

### In-Game Commands
Most modules expose in-game `.help` or status commands accessible in chat or via the worldserver console. For standard core GM commands, see the official [AzerothCore GM Commands Wiki](https://www.azerothcore.org/wiki/gm-commands).

| Module | Primary Command / `.help` | Description |
|---|---|---|
| `mod-playerbots` | `.playerbots` | Controls bot spawns, behaviors, and party/account linking |
| `mod-ah-bot` | `.ahbot` | Controls and reloads Auction House bot settings |
| `mod-individual-progression` | `.ip` | Manages player expansion or tier progression |
| `mod-acore-mall` | `.tele gmisland` | GM Island mall vendor spawns |

---

## Documentation
- [Configuration Guide](docs/CONFIGURATION.md)
- [Included Modules Inventory](docs/MODULES.md)
- [Contributing Guidelines](docs/CONTRIBUTING.md)
- [Security Policy](docs/SECURITY.md)
- [Code of Conduct](docs/CODE_OF_CONDUCT.md)
- [Attribution Notice](docs/NOTICE.md)
- [Changelog](docs/CHANGELOG.md)

