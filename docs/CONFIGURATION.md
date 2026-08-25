# SkirmishCore Configuration Guide

Welcome to the SkirmishCore configuration guide. This document explains how to customize your server settings.

---

## How Configuration Files Work

All active configuration files are located inside:
`env/dist/etc/`

### Default Repack Setup vs Custom Edits

> [!IMPORTANT]  
> **Always edit the active `.conf` file (e.g. `playerbots.conf`), NOT the `.conf.dist` file!**  
> If the `.conf` file does not exist yet in `env/dist/etc/modules/` or `env/dist/etc/`, **copy the `.conf.dist` template and rename the copy to `.conf`** before making edits. The server only reads your custom changes from the active `.conf` file.

* **`.conf.dist` files (Repack Distribution Templates)**:
  Contains the default repack distribution configuration. Do not edit these files directly, as clean builds or core updates will overwrite them.

* **`.conf` files (YOUR Custom Active Configuration)**:
  Created by copying the corresponding `.conf.dist` template (e.g. `cp playerbots.conf.dist playerbots.conf`). The server engine reads your active `.conf` files upon startup.

---

## Customizing Playerbots (`playerbots.conf`)

Configuration path: `env/dist/etc/modules/playerbots.conf`

### 1. Expansion Progression & Menu Selection

You can easily switch expansion modes using **Option 3 (Expansion Setup)** in `python menu.py` (or `menu.cmd`) or manually updating `AiPlayerbot.RandomBotMaxLevel` and `AiPlayerbot.RandomBotMaps` in `playerbots.conf`:

* **Classic Mode (Option 3 -> 1)**: Max Level 60 | Kalimdor & Eastern Kingdoms (`0,1`).
  ```ini
  AiPlayerbot.RandomBotMaxLevel = 60
  AiPlayerbot.RandomBotMaps = 0,1
  ```
* **The Burning Crusade (Option 3 -> 2)**: Max Level 70 | Unlocks Outland (`0,1,530`).
  ```ini
  AiPlayerbot.RandomBotMaxLevel = 70
  AiPlayerbot.RandomBotMaps = 0,1,530
  ```
* **Wrath of the Lich King (Option 3 -> 3)**: Max Level 80 | Unlocks Northrend (`0,1,530,571`).
  ```ini
  AiPlayerbot.RandomBotMaxLevel = 80
  AiPlayerbot.RandomBotMaps = 0,1,530,571
  ```

> [!IMPORTANT]
> **Individual Progression (`mod-individual-progression`) Note:**
> Enabling TBC or WotLK mode in `playerbots.conf` allows **bots** to level up and access expansion zones. However, human players are still gated by the **Individual Progression** system.
> - **Legit Progression**: Players must complete required attunements/raids to unlock expansion content.
> - **GM Commands (Bypass)**: To manually advance or level up your progression rank, use:
>   - `.ip help` — View all progression commands
>   - `.ip set level <level>` — Set your player progression tier level (e.g. 60 or 70)
>   - `.ip complete` — Complete current expansion tier requirements automatically

## 1–60 Progression & Bot Distribution System

SkirmishCore is configured out-of-the-box for a **1–60 progressive single-player and co-op playthrough**.

### 1. Bot Level Range & Level Brackets Rebalancing
In `playerbots.conf`, randombot parameters are configured as:
```ini
AiPlayerbot.RandomBotMinLevel = 1
AiPlayerbot.RandomBotMaxLevel = 60
AiPlayerbot.SyncLevelWithPlayers = 0
AiPlayerbot.LevelBrackets.Enabled = 1
```

* **Dynamic Distribution (`LevelBrackets.Enabled = 1`)**: Rather than all bots staying at Level 1 or immediately jumping to 60, the server continuously rebalances online bots across 1–60 level brackets (1–9, 10–19, 20–29, 30–39, 40–49, 50–59, 60).
* **`SyncLevelWithPlayers = 0`**: Ensures that even on a fresh server or new level 1 character, the world contains bots of all level brackets across leveling zones, dungeons, and PvP areas.

---

### 2. Bot Spawn & Travel Zones (`ZoneBracket`)
Bots automatically travel, flight-master, and teleport to level-appropriate zones based on their current level:
* **Levels 1–12 (Starting Zones)**: Durotar, Elwynn Forest, Dun Morogh, Tirisfal Glades, Teldrassil, Mulgore, Eversong Woods, Azuremyst Isle.
* **Levels 10–25 (Contested Lowie Zones)**: Westfall, Loch Modan, Darkshore, Barrens, Silverpine Forest.
* **Levels 20–45 (World PvP & Questing Hotspots)**: Ashenvale (Astranaar / Splintertree), Hillsbrad Foothills (Southshore / Tarren Mill), Redridge Mountains (Lakeshire), Stonetalon Mountains, Arathi Highlands (Refuge Pointe / Hammerfall), Stranglethorn Vale (Nesingwary Camp / Booty Bay).
* **Levels 45–60 (High-Level Zones & Capital Duels)**: Tanaris, Feralas, Searing Gorge, Burning Steppes, Eastern/Western Plaguelands, Stormwind & Orgrimmar Gates.

---

## Common Bot Adjustments & Troubleshooting

### Setting Up a Strict "Level 1" Bot Start
If you prefer a **fresh playthrough where ALL bots start at Level 1** (disabling random spawn level variance):

1. Open `env/dist/etc/modules/playerbots.conf` (or your override `.conf`).
2. Set the following settings:

```ini
# Turn off level groups so max-level bots don't spawn automatically
AiPlayerbot.LevelBrackets.Enabled = 0

# Force all new bots to start strictly at Level 1
AiPlayerbot.DisableRandomLevels = 1
AiPlayerbot.RandombotStartingLevel = 1
```

---

### Resetting & Refreshing Bot Characters

#### When to Reset Bots:
* You altered bot starting levels or bracket configurations.
* High-level bots remain in starter areas from previous server sessions.
* You started a new character and want a clean world population.

#### How to Reset Bots via Interactive Menu:

##### Automated Clean Slate (Wipe & Regenerate All Bots)
1. Run `python menu.py` -> **Option 4 (Bot Management & Population)**.
2. Select **Option 2 (Reset & Purge Playerbots)**.
3. The menu system will automatically handle setting `DeleteRandomBotAccounts = 1`, restarting the server, performing cleanup, and returning `DeleteRandomBotAccounts = 0`.

