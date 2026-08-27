<div align="center">

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

    
**SkirmishCore** is an AzerothCore (WOTLK 3.3.5a) repack tailored for players seeking an offline World PvP-like WoW experience. <br>
Powered by intelligent Playerbots, dynamic economy controls, and an individual progression system.



[![Watch Demo](https://img.shields.io/badge/Watch-Video%20Demo-1ab7ea?logo=vimeo&logoColor=white)](https://vimeo.com/1221700236)


---

<p>

![SkirmishCore Gameplay](https://i.imgur.com/moONtxw.gif)

![SkirmishCore Menu](docs/assets/menu.png?raw=true&v=2)

</p>
</div>

## Default Configuration

**SkirmishCore arrives pre-configured out of the box for a progressive, active single-player and small co-op World PvP experience.**<br>
> **Note**: All configuration files are located under the `env/dist/etc/` directory. See the [configuration guide](http://github.com/Of-Arte/Skirmish-Core/blob/Playerbot/docs/CONFIGURATION.md) for details.

**Key features:**

- **Classic Locked**: Max bot level is capped at 60 and limited to Kalimdor and Eastern Kingdoms maps (0,1).
- **Auction House Bot**: A dedicated AH bot character can run in-game economy autonomously; This can be activated through the menu.
- **GM Island Vendor Mall**: A full item vendor mall on GM Island accessible to Admin accounts out of the box.
- **Expansion Gating**: Takes human players through Classic raid tiers before unlocking Outland or Northrend content.
- **High Bot Population Density**: Default bot population is tuned to 1,000–2,000 active bots for a bustling MMO feel.
- **Natural Leveling & Exploration**: Bots level from 1–60 through questing and combat by default.
- **Dynamic Level Brackets**: Bots are distributed across all leveling brackets, populating the open world so the world always feels alive.
> Want a F R E S H launch experience? Select **3. Bot Management → 4. Bot Starting Level → 1. Force Level 1 Spawns**
---

## Installation & Setup

Follow these steps in order to install, configure, and launch your server.

### 1. Clone Repository
```bash
git clone https://github.com/Of-Arte/Skirmish-Core.git
```
*(Submodules are automatically detected and initialized by the SkirmishCore Control Hub menu on launch).*


### 2. Prerequisites & System Requirements
- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**: Container engine used to run the authserver, worldserver, and database services.
- **[Python 3.8+](https://www.python.org/downloads/)**: Runtime required for the SkirmishCore Control Hub menu scripts.
- **[Pytest](https://docs.pytest.org/)** *(optional)*: Test framework for the developer test suite (`pip install -r tests/requirements-test.txt`).

### 3. Launch Control Hub Menu
- **Windows (Primary)**: Double-click or run `menu.cmd` from the root directory:
  ```cmd
  menu.cmd
  ```
- **Linux / macOS**: Execute `skirmish/menu.py` using Python 3 (or `./menu.sh`):
  ```bash
  python3 skirmish/menu.py
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

## Optional

### Auction House Bot Setup
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
- [Included Modules](docs/MODULES.md)
- [Contributing Guidelines](docs/CONTRIBUTING.md)
- [Security Policy](docs/SECURITY.md)
- [Code of Conduct](docs/CODE_OF_CONDUCT.md)
- [Attribution Notice](docs/NOTICE.md)
- [Changelog](docs/CHANGELOG.md)
