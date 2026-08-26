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

### Recommended Setup: Interactive Setup Wizard
Launch `menu.cmd` -> Select **4. Bot Management & Population** -> **5. Auction House Bot Setup** -> **1. Interactive AH-Bot Setup Wizard**.

The wizard automates the full setup flow:
1. Automatically creates the AH bot account (`ahbot` / `password`).
2. Guides you to log into WoW and create your bot character (suggested name: `Auctioneer`).
   * **IMPORTANT**: Do **NOT** enter the game world with this bot character! Simply create it at character selection screen and exit.
3. Auto-queries the database for your character, extracts its GUID, enables seller/buyer in `mod_ahbot.conf`, and reloads the server configuration!

### Manual Setup (Alternative)
1. Create account in worldserver console: `.account create ahbot password`
2. Log into WoW, create character `Auctioneer` (do NOT enter game world).
3. Find GUID via MySQL: `docker compose exec ac-database mysql -uroot -proot acore_characters -e "SELECT guid, name FROM characters WHERE name = 'Auctioneer';"`
4. Open `env/dist/etc/modules/mod_ahbot.conf` and set:
   ```ini
   AuctionHouseBot.EnableSeller = true
   AuctionHouseBot.Buyer.Enabled = true
   AuctionHouseBot.GUIDs = <CHARACTER_GUID>
   ```
5. Apply changes in server console: `.ahbot reload`
