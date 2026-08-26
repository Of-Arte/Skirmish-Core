# Included Modules

The following inventory reflects the modules integrated as git submodules in the `./modules/` directory.

## Installed Submodules

| Module | Purpose | Upstream URL | Location | Config Path |
|---|---|---|---|---|
| `mod-playerbots` | Adds player-like bots simulating MMO experience | [mod-playerbots/mod-playerbots](https://github.com/mod-playerbots/mod-playerbots) | `modules/mod-playerbots` | `env/dist/etc/modules/playerbots.conf` |
| `mod-ah-bot` | Blizzlike AH bot | [azerothcore/mod-ah-bot](https://github.com/azerothcore/mod-ah-bot) | `modules/mod-ah-bot` | `env/dist/etc/modules/mod_ahbot.conf` |
| `mod-individual-progression` | Simulates progress through expansions/tiers for individual players | [ZhengPeiRu21/mod-individual-progression](https://github.com/ZhengPeiRu21/mod-individual-progression) | `modules/mod-individual-progression` | `env/dist/etc/modules/individualProgression.conf` |
| `mod-acore-mall` | Vendor mall on GM Island | [Of-Arte/Acore_Mall](https://github.com/Of-Arte/Acore_Mall) | `modules/mod-acore-mall` | N/A |



---

## Submodule & Loader Integration

To maintain 100% clean upstream submodule tracking without needing write access to third-party repositories:

1. **Clean Upstream Pinning**: Submodules are tracked strictly against official upstream commit SHAs.
2. **Automated Loader Binding**: Submodule directories are named `mod-ah-bot` and `mod-acore-mall` so AzerothCore's CMake script loader automatically binds `Addmod_ah_botScripts()` and `Addmod_acore_mallScripts()` natively without requiring source modifications in third-party repos.
3. **Customizations via Repack Layer**:
   * **Module Database Updates**: Submodules natively supply update SQL files auto-imported by `ac-db-import`.
   * **Configuration Overrides**: Module configuration templates are maintained in `env/dist/etc/modules/` and `env/dist/etc/`.

---

## AH-Bot Setup (`mod-ah-bot`)

To enable AH-Bot, assign it to a dedicated character and set `AuctionHouseBot.GUIDs` in `env/dist/etc/modules/mod_ahbot.conf`.

### Step 1: Create Account & Character
1. In `ac-worldserver` console (or in-game GM chat), create an account:
   ```
   .account create ahbot password
   ```
2. Log into WoW using account `ahbot` / `password` and create a character named `Ahbot`.

### Step 2: Get Character GUID
Choose one of the following methods to find the character GUID:

* **Option A (WorldServer / GM Command)**:
  In the `worldserver` console or in-game GM chat, run:
  ```
  .pinfo Ahbot
  ```
  Look for `guid: X` (or `GUID: X`) in the output string.

* **Option B (Docker / Database Query)**:
  Run this command in your terminal:
  ```bash
  docker compose exec ac-database mysql -uroot -proot acore_characters -e "SELECT guid, name FROM characters WHERE name = 'Ahbot';"
  ```

### Step 3: Configure `mod_ahbot.conf`
Open `env/dist/etc/modules/mod_ahbot.conf` and set:
```ini
AuctionHouseBot.EnableSeller = true
AuctionHouseBot.GUIDs = <CHARACTER_GUID>
```
*(e.g., `AuctionHouseBot.GUIDs = 12`)*

Apply changes by running `.ahbot reload` in the server console.
