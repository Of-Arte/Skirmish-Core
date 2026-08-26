import os
import sys
import subprocess
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

MENU_PY = os.path.join(REPO_ROOT, "skirmish", "menu.py")
CONF_FILE = os.path.join(REPO_ROOT, "env", "dist", "etc", "modules", "playerbots.conf")
AHBOT_CONF_FILE = os.path.join(REPO_ROOT, "env", "dist", "etc", "modules", "mod_ahbot.conf")
IP_CONF_FILE = os.path.join(REPO_ROOT, "env", "dist", "etc", "modules", "individualProgression.conf")



@pytest.fixture(autouse=True)
def isolate_config():
    """Backup playerbots.conf, mod_ahbot.conf, and individualProgression.conf before test execution and restore them afterwards."""
    original_pb = None
    if os.path.exists(CONF_FILE):
        with open(CONF_FILE, "r", encoding="utf-8") as f:
            original_pb = f.read()

    original_ah = None
    if os.path.exists(AHBOT_CONF_FILE):
        with open(AHBOT_CONF_FILE, "r", encoding="utf-8") as f:
            original_ah = f.read()

    original_ip = None
    if os.path.exists(IP_CONF_FILE):
        with open(IP_CONF_FILE, "r", encoding="utf-8") as f:
            original_ip = f.read()

    yield

    if original_pb is not None:
        with open(CONF_FILE, "w", encoding="utf-8") as f:
            f.write(original_pb)

    if original_ah is not None:
        with open(AHBOT_CONF_FILE, "w", encoding="utf-8") as f:
            f.write(original_ah)

    if original_ip is not None:
        with open(IP_CONF_FILE, "w", encoding="utf-8") as f:
            f.write(original_ip)



def run_menu_py_with_inputs(inputs, timeout=15):
    """
    Runs src/menu.py passing exact sequence of inputs.
    Appends exit command ('0') to ensure process completes cleanly.
    Returns (stdout, stderr, returncode).
    """
    full_inputs = list(inputs)
    if not full_inputs or full_inputs[-1] != "0":
        full_inputs.append("0")

    env = dict(os.environ, SKIRMISHCORE_TEST_MODE="1")
    input_str = "\n".join(full_inputs) + "\n"
    proc = subprocess.Popen(
        [sys.executable, MENU_PY],
        cwd=REPO_ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env
    )
    try:
        stdout, stderr = proc.communicate(input=input_str, timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        return stdout, stderr, -1
    return stdout, stderr, proc.returncode


def test_main_menu_exit():
    """Verify selecting option 0 exits cleanly with returncode 0."""
    stdout, stderr, code = run_menu_py_with_inputs(["0"])
    assert code == 0
    assert "SKIRMISHCORE CONTROL HUB" in stdout


def test_invalid_input_handling():
    """Verify invalid option displays warning message."""
    stdout, stderr, code = run_menu_py_with_inputs(["invalid_choice", "0"])
    assert code == 0
    assert "Invalid choice. Please try again." in stdout


def test_server_controls_menu_back():
    """Verify navigation into Server Controls and returning via 0."""
    stdout, stderr, code = run_menu_py_with_inputs(["1", "0", "0"])
    assert code == 0
    assert "SERVER CONTROLS & ADMIN" in stdout


def test_create_account_action_offline_error():
    """Verify Automated Account Creation Wizard reports error when server stack is offline."""
    stdout, stderr, code = run_menu_py_with_inputs(["1", "4", "testgm", "pass123", "3", "n", "", "0", "0"])
    assert code == 0
    assert "AUTOMATED ACCOUNT CREATION WIZARD" in stdout
    assert "ERROR: Account 'testgm' could not be created!" in stdout
    assert "Server stack and database containers are OFFLINE" in stdout


def test_build_server_option():
    """Verify Option 1 -> Option 3 executes DockerService.build_images()."""
    stdout, stderr, code = run_menu_py_with_inputs(["1", "3", "", "0", "0"])
    assert code == 0
    assert "Building SkirmishCore Docker images..." in stdout


def test_create_account_action_online_mock(monkeypatch):
    """Verify Automated Account Creation Wizard creates account and applies GM status when container is online."""
    import skirmish.menu as menu_mod
    monkeypatch.setattr(menu_mod.DockerService, "get_container_status", lambda svc: "ONLINE")

    calls = []
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        class DummyCompleted:
            returncode = 0
            stdout = "Created account testgm\n1"
            stderr = ""
        return DummyCompleted()

    monkeypatch.setattr(menu_mod.subprocess, "run", fake_run)

    inputs = iter(["testgm", "pass123", "3"])
    monkeypatch.setattr(menu_mod, "safe_input", lambda prompt="": next(inputs, ""))

    menu_mod.create_account_action({})
    assert len(calls) >= 1


def test_health_check_option():
    """Verify Option 1 -> Option 7 executes HealthChecker diagnostics."""
    stdout, stderr, code = run_menu_py_with_inputs(["1", "7", "0", "0"])
    assert code == 0
    assert "SKIRMISHCORE COMPREHENSIVE HEALTH CHECK" in stdout
    assert "System & Python Environment" in stdout
    assert "HEALTH CHECK RESULT" in stdout


def test_wipe_server_action_cancel():
    """Verify entering anything other than 'delete' cancels wiping the server."""
    stdout, stderr, code = run_menu_py_with_inputs(["1", "8", "no", "", "0", "0"])
    assert code == 0
    assert "WARNING: WIPE & DELETE SERVER SETUP" in stdout
    assert "Wipe canceled. Confirmation did not match 'delete'." in stdout


def test_wipe_server_action_confirm():
    """Verify typing 'delete' triggers DockerService.wipe_stack()."""
    stdout, stderr, code = run_menu_py_with_inputs(["1", "8", "delete", "", "0", "0"])
    assert code == 0
    assert "WARNING: WIPE & DELETE SERVER SETUP" in stdout
    assert "Wiping SkirmishCore Docker stack, volumes, and images..." in stdout


def test_start_and_stop_server_actions_cancel():
    """Verify start and stop server actions prompt for confirmation and cancel when 'n' is entered."""
    stdout, stderr, code = run_menu_py_with_inputs(["1", "1", "n", "", "0", "0"])
    assert code == 0
    assert "Start canceled." in stdout

    stdout, stderr, code = run_menu_py_with_inputs(["1", "2", "n", "", "0", "0"])
    assert code == 0
    assert "Stop canceled." in stdout


def test_start_server_action_rejects_flow_when_images_unbuilt(monkeypatch):
    """Verify start server flow prompts to build images when Docker images have not been built."""
    import skirmish.menu as menu_mod
    monkeypatch.setattr(menu_mod.DockerService, "are_images_built", lambda: False)

    # When user enters 'n' to build prompt
    inputs = iter(["y", "n"])
    monkeypatch.setattr(menu_mod, "safe_input", lambda prompt="": next(inputs, ""))

    captured_out = []
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: captured_out.append(" ".join(map(str, args))))

    menu_mod.start_server_action({})
    out_str = "\n".join(captured_out)
    assert "WARNING: SkirmishCore Docker images have not been built yet." in out_str
    assert "Start canceled: Docker images must be built before starting the server." in out_str

    # When user enters 'y' to build prompt, verify DockerService.build_images is called
    build_called = []
    def fake_run(cmd, **kwargs):
        class DummyCompleted:
            returncode = 0
            stdout = ""
            stderr = ""
        return DummyCompleted()

    monkeypatch.setattr(menu_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(menu_mod.DockerService, "build_images", lambda: build_called.append(True) or True)
    inputs2 = iter(["y", "y", "n"])
    monkeypatch.setattr(menu_mod, "safe_input", lambda prompt="": next(inputs2, ""))

    menu_mod.start_server_action({})
    assert len(build_called) == 1


def test_docker_service_are_images_built_check(monkeypatch):
    """Verify DockerService.are_images_built checks image presence using docker image inspect."""
    import skirmish.menu as menu_mod
    monkeypatch.delenv("SKIRMISHCORE_TEST_MODE", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    calls = []
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        class Dummy:
            returncode = 0
        return Dummy()

    monkeypatch.setattr(menu_mod.subprocess, "run", fake_run)
    assert menu_mod.DockerService.are_images_built() is True
    assert len(calls) == 3

    # If inspect returns non-zero exit code
    def fake_run_fail(cmd, **kwargs):
        class DummyFail:
            returncode = 1
        return DummyFail()

    monkeypatch.setattr(menu_mod.subprocess, "run", fake_run_fail)
    assert menu_mod.DockerService.are_images_built() is False


def test_skirmish_menu_back():
    """Verify navigation into Skirmish menu and returning via 0."""
    stdout, stderr, code = run_menu_py_with_inputs(["3", "2", "0", "0", "0"])
    assert code == 0
    assert "SKIRMISH MODE SETUP" in stdout


def test_expansion_menu_back():
    """Verify navigation into Expansion Setup menu and returning via 0."""
    stdout, stderr, code = run_menu_py_with_inputs(["2", "0", "0"])
    assert code == 0
    assert "EXPANSION PROGRESSION CONTROL" in stdout


def test_bot_management_menu_back():
    """Verify navigation into Bot Management menu and returning via 0."""
    stdout, stderr, code = run_menu_py_with_inputs(["3", "0", "0"])
    assert code == 0
    assert "BOT MANAGEMENT & POPULATION" in stdout


def test_bot_population_submenu_back():
    """Verify navigation into Bot Population Density setup and returning."""
    stdout, stderr, code = run_menu_py_with_inputs(["3", "1", "0", "0", "0"])
    assert code == 0
    assert "BOT POPULATION DENSITY SETUP" in stdout


def test_bot_population_presets_config_mutation():
    """Verify Low, Medium, High bot population choices write correct Min/Max values to playerbots.conf."""
    # Test Low Preset [100-300]
    stdout, stderr, code = run_menu_py_with_inputs(["3", "1", "1", "n", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Bot population set to Low [100-300]" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.MinRandomBots = 100" in content
        assert "AiPlayerbot.MaxRandomBots = 300" in content

    # Test High Preset [1000-2000]
    stdout, stderr, code = run_menu_py_with_inputs(["3", "1", "3", "n", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Bot population set to High [1000-2000]" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.MinRandomBots = 1000" in content
        assert "AiPlayerbot.MaxRandomBots = 2000" in content

    # Reset to Medium Preset [500-1000]
    stdout, stderr, code = run_menu_py_with_inputs(["3", "1", "2", "n", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Bot population set to Medium [500-1000]" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.MinRandomBots = 500" in content
        assert "AiPlayerbot.MaxRandomBots = 1000" in content


def test_rpg_weight_preset_config_mutation():
    """Verify Open World PvP & World Activity presets update RpgStatusProbWeight values in playerbots.conf."""
    # Test World PvP Skirmishers
    stdout, stderr, code = run_menu_py_with_inputs(["3", "3", "4", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Open World PvP & World Activity set to 'World PvP Skirmishers'" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.RpgStatusProbWeight.OutdoorPvp = 80" in content

    # Test Balanced World Activity
    stdout, stderr, code = run_menu_py_with_inputs(["3", "3", "1", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Open World PvP & World Activity set to 'Balanced World Activity'" in stdout

    # Test Town Idlers
    stdout, stderr, code = run_menu_py_with_inputs(["3", "3", "5", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Open World PvP & World Activity set to 'Town Idlers'" in stdout


def test_expansion_mode_config_mutation():
    """Verify Expansion Setup options update playerbots.conf and individualProgression.conf."""
    # Classic Mode
    stdout, stderr, code = run_menu_py_with_inputs(["2", "1", "n", "", "0", "0", "0"])
    assert code == 0
    assert "Configuring Classic Mode" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.RandomBotMinLevel = 1" in content
        assert "AiPlayerbot.RandomBotMaxLevel = 60" in content
        assert "AiPlayerbot.RandomBotMaps = 0,1" in content
        assert "AiPlayerbot.RandomBotFixedLevel = 0" in content
    with open(IP_CONF_FILE, "r", encoding="utf-8") as f:
        ip_content = f.read()
        assert "IndividualProgression.StartingProgression = 0" in ip_content
        assert "IndividualProgression.ProgressionLimit = 7" in ip_content
        assert "IndividualProgression.BotAccountsMaxLevel = 60" in ip_content

    # TBC Mode
    stdout, stderr, code = run_menu_py_with_inputs(["2", "2", "n", "", "0", "0", "0"])
    assert code == 0
    assert "Configuring TBC Mode" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.RandomBotMinLevel = 1" in content
        assert "AiPlayerbot.RandomBotMaxLevel = 70" in content
        assert "AiPlayerbot.RandomBotMaps = 0,1,530" in content
        assert "AiPlayerbot.RandomBotFixedLevel = 0" in content
    with open(IP_CONF_FILE, "r", encoding="utf-8") as f:
        ip_content = f.read()
        assert "IndividualProgression.StartingProgression = 8" in ip_content
        assert "IndividualProgression.ProgressionLimit = 13" in ip_content
        assert "IndividualProgression.BotAccountsMaxLevel = 70" in ip_content

    # WotLK Mode
    stdout, stderr, code = run_menu_py_with_inputs(["2", "3", "n", "", "0", "0", "0"])
    assert code == 0
    assert "Configuring WotLK Mode" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.RandomBotMinLevel = 1" in content
        assert "AiPlayerbot.RandomBotMaxLevel = 80" in content
        assert "AiPlayerbot.RandomBotMaps = 0,1,530,571" in content
        assert "AiPlayerbot.RandomBotFixedLevel = 0" in content
    with open(IP_CONF_FILE, "r", encoding="utf-8") as f:
        ip_content = f.read()
        assert "IndividualProgression.StartingProgression = 13" in ip_content
        assert "IndividualProgression.ProgressionLimit = 0" in ip_content
        assert "IndividualProgression.BotAccountsMaxLevel = 80" in ip_content


def test_skirmish_bracket_config_mutation():
    """Verify Skirmish Mode sets correct Min/Max level ranges and maps in playerbots.conf and individualProgression.conf."""
    stdout, stderr, code = run_menu_py_with_inputs(["3", "2", "1", "n", "", "0", "0", "0"])
    assert code == 0
    assert "SKIRMISH MODE ACTIVE" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.RandomBotMinLevel = 10" in content
        assert "AiPlayerbot.RandomBotMaxLevel = 20" in content
        assert "AiPlayerbot.RandomBotFixedLevel = 1" in content
    with open(IP_CONF_FILE, "r", encoding="utf-8") as f:
        ip_content = f.read()
        assert "IndividualProgression.StartingProgression = 0" in ip_content
        assert "IndividualProgression.ProgressionLimit = 7" in ip_content
        assert "IndividualProgression.BotAccountsMaxLevel = 20" in ip_content


def test_custom_skirmish_action_executes_preset():
    """Verify custom skirmish level range invokes skirmish_preset_action and updates config."""
    stdout, stderr, code = run_menu_py_with_inputs(["3", "2", "8", "35", "45", "n", "", "0", "0", "0"])
    assert code == 0
    assert "Applying Skirmish Config: Level Range [35 - 45]" in stdout
    assert "SKIRMISH MODE ACTIVE: Level 35-45 PvP Battles" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.RandomBotMinLevel = 35" in content
        assert "AiPlayerbot.RandomBotMaxLevel = 45" in content
        assert "AiPlayerbot.RandomBotFixedLevel = 1" in content
    with open(IP_CONF_FILE, "r", encoding="utf-8") as f:
        ip_content = f.read()
        assert "IndividualProgression.StartingProgression = 0" in ip_content
        assert "IndividualProgression.ProgressionLimit = 7" in ip_content
        assert "IndividualProgression.BotAccountsMaxLevel = 45" in ip_content


def test_custom_skirmish_action_level_1_sets_fixed_level_zero():
    """Verify custom range starting at Level 1 sets RandomBotFixedLevel = 0 for natural leveling."""
    stdout, stderr, code = run_menu_py_with_inputs(["3", "2", "8", "1", "60", "n", "", "0", "0", "0"])
    assert code == 0
    assert "Applying Skirmish Config: Level Range [1 - 60]" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.RandomBotMinLevel = 1" in content
        assert "AiPlayerbot.RandomBotMaxLevel = 60" in content
        assert "AiPlayerbot.RandomBotFixedLevel = 0" in content


def test_skirmish_custom_range_validation():
    """Verify custom skirmish level range validation catches Min > Max errors."""
    stdout, stderr, code = run_menu_py_with_inputs(["3", "2", "8", "50", "20", "", "0", "0", "0"])
    assert code == 0
    assert "Invalid input: Minimum level cannot be greater than maximum level." in stdout


def test_custom_population_input_validation():
    """Verify custom bot population density validates non-integers and Min > Max bounds."""
    # Invalid integer
    stdout, stderr, code = run_menu_py_with_inputs(["3", "1", "4", "abc", "200", "", "0", "0", "0"])
    assert code == 0
    assert "Invalid input: Bot count must be a positive integer." in stdout

    # Min > Max
    stdout, stderr, code = run_menu_py_with_inputs(["3", "1", "4", "1500", "500", "", "0", "0", "0"])
    assert code == 0
    assert "Invalid input: Minimum bot count cannot be greater than maximum bot count." in stdout

    # Valid custom population [450-850]
    stdout, stderr, code = run_menu_py_with_inputs(["3", "1", "4", "450", "850", "n", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Bot population set to Custom [450-850]" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.MinRandomBots = 450" in content
        assert "AiPlayerbot.MaxRandomBots = 850" in content


def test_coop_action_handling():
    """Verify Multi-Player Setup handles cancel, invalid format, and offline prompts."""
    # Cancel input 'c'
    stdout, stderr, code = run_menu_py_with_inputs(["4", "c", "0"])
    assert code == 0
    assert "Address update canceled." in stdout

    # Invalid address format
    stdout, stderr, code = run_menu_py_with_inputs(["4", "invalid ip address!", "", "0"])
    assert code == 0
    assert "Invalid input: Address must be a valid IP address or hostname." in stdout

    # Valid IP format while offline (user declines starting server)
    stdout, stderr, code = run_menu_py_with_inputs(["4", "192.168.1.100", "n", "", "0"])
    assert code == 0
    assert "Database container is currently OFFLINE" in stdout
    assert "Address update canceled." in stdout


def test_config_manager_comment_handling(tmp_path):
    """Verify ConfigManager ignores commented lines and creates/updates active uncommented lines."""
    import skirmish.menu as menu_mod

    test_conf = os.path.join(tmp_path, "test.conf")
    with open(test_conf, "w", encoding="utf-8") as f:
        f.write("# AiPlayerbot.MinRandomBots = 50\n")

    # get_conf_value should ignore commented line and return default
    val = menu_mod.ConfigManager.get_conf_value("AiPlayerbot.MinRandomBots", default="def", conf_path=test_conf)
    assert val == "def"

    # update_conf_values should append active setting without changing comment
    menu_mod.ConfigManager.update_conf_values({"AiPlayerbot.MinRandomBots": "200"}, conf_path=test_conf)
    with open(test_conf, "r", encoding="utf-8") as f:
        content = f.read()
        assert "# AiPlayerbot.MinRandomBots = 50" in content
        assert "AiPlayerbot.MinRandomBots = 200" in content

    # Calling get_conf_value should now return '200'
    val2 = menu_mod.ConfigManager.get_conf_value("AiPlayerbot.MinRandomBots", default="def", conf_path=test_conf)
    assert val2 == "200"


def test_linux_admin_console_and_logs_compatibility(monkeypatch):
    """Verify admin_console_action and logs_action behave gracefully when os.name != 'nt' (Linux/macOS)."""
    import os
    import skirmish.menu as menu_mod

    monkeypatch.setattr(os, "name", "posix")

    calls = []
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        class DummyCompleted:
            returncode = 0
            stdout = ""
            stderr = ""
        return DummyCompleted()

    monkeypatch.setattr(menu_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(menu_mod.DockerService, "get_container_status", lambda svc: "ONLINE")
    monkeypatch.setattr(menu_mod, "safe_input", lambda prompt="": "1")

    menu_mod.admin_console_action({})
    assert len(calls) == 1
    assert calls[0] == ["docker", "attach", "ac-worldserver"]

    calls.clear()
    menu_mod.logs_action({})
    assert len(calls) == 1
    assert calls[0] == ["docker", "compose", "logs", "-f", "ac-worldserver"]


def test_bot_starting_level_mode_config_mutation():
    """Verify Bot Starting Level Mode toggles DisableRandomLevels in playerbots.conf."""
    stdout, stderr, code = run_menu_py_with_inputs(["3", "4", "1", "n", "", "0", "0"])
    assert code == 0
    assert "SUCCESS: Forced Level 1 Bot Spawns Enabled!" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.DisableRandomLevels = 1" in content
        assert "AiPlayerbot.RandombotStartingLevel = 1" in content

    stdout, stderr, code = run_menu_py_with_inputs(["3", "4", "2", "n", "", "0", "0"])
    assert code == 0
    assert "SUCCESS: Random Level Bot Spawns Enabled!" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.DisableRandomLevels = 0" in content


def test_ahbot_setup_menu():
    """Verify AH Bot interactive wizard, status options, and GUID validation."""
    ahbot_conf = os.path.join(REPO_ROOT, "env", "dist", "etc", "modules", "mod_ahbot.conf")
    import skirmish.menu as menu_mod

    # Reset GUIDs to 0 to ensure prompt is triggered
    menu_mod.ConfigManager.update_conf_values({"AuctionHouseBot.GUIDs": "0"}, conf_path=ahbot_conf)

    # Test wizard prompt when server stack is offline
    stdout, stderr, code = run_menu_py_with_inputs(["3", "6", "1", "n", "0", "0"])
    assert code == 0
    assert "INTERACTIVE AH BOT SETUP WIZARD" in stdout
    assert "SkirmishCore server stack is currently OFFLINE" in stdout

    # Reset GUIDs to 0 again
    menu_mod.ConfigManager.update_conf_values({"AuctionHouseBot.GUIDs": "0"}, conf_path=ahbot_conf)

    # Test option 2 with invalid non-numeric GUID
    stdout, stderr, code = run_menu_py_with_inputs(["3", "6", "2", "y", "invalid_guid", "", "0", "0"])
    assert code == 0
    assert "Invalid input: GUID must be a positive integer." in stdout

    # Reset GUIDs to 0 again
    menu_mod.ConfigManager.update_conf_values({"AuctionHouseBot.GUIDs": "0"}, conf_path=ahbot_conf)

    # Test option 2 (Enable AH Bot with manual GUID 55)
    stdout, stderr, code = run_menu_py_with_inputs(["3", "6", "2", "y", "55", "", "0", "0"])
    assert code == 0
    assert "SUCCESS: AH Bot Enabled! (Character GUID: 55)" in stdout

    with open(ahbot_conf, "r", encoding="utf-8") as f:
        assert "AuctionHouseBot.GUIDs = 55" in f.read()

    # Test option 3 (Disable AH Bot)
    stdout, stderr, code = run_menu_py_with_inputs(["3", "6", "3", "", "0", "0"])
    assert code == 0
    assert "SUCCESS: AH Bot Disabled!" in stdout

    # Test option 4 (View Characters when offline)
    stdout, stderr, code = run_menu_py_with_inputs(["3", "6", "4", "", "0", "0"])
    assert code == 0
    assert "No characters found in database" in stdout


def test_server_offline_annotations_shown_when_server_down():
    """Verify [SERVER OFFLINE] annotation appears on online-required options when server is down (test mode = OFFLINE)."""
    stdout, stderr, code = run_menu_py_with_inputs(["1", "0", "0"])
    assert code == 0
    # Stop Server and Admin Console require online; server is OFFLINE in test mode
    assert "Stop Server [SERVER OFFLINE]" in stdout
    assert "Admin Console [SERVER OFFLINE]" in stdout
    # Start Server requires offline; server IS offline, so no annotation expected
    assert "Start Server [SERVER ONLINE]" not in stdout


def test_server_online_annotations_shown_when_server_running(monkeypatch):
    """Verify [SERVER ONLINE] annotation appears on offline-required options when server is running."""
    import skirmish.menu as menu_mod

    monkeypatch.setattr(menu_mod.DockerService, "get_container_status", lambda svc: "ONLINE")

    rendered_lines = []
    original_print = __builtins__["print"] if isinstance(__builtins__, dict) else print

    import builtins
    original_print = builtins.print
    monkeypatch.setattr(builtins, "print", lambda *args, **kwargs: rendered_lines.append(" ".join(map(str, args))))

    menu = menu_mod.create_application_menus()
    # Navigate into server menu (index 0 = server_menu sub-option)
    server_option = menu.options[0]
    server_menu = server_option.sub_menu
    try:
        server_menu.render({})
    except Exception:
        pass

    out = "\n".join(rendered_lines)
    assert "Start Server [SERVER ONLINE]" in out
    # Stop Server and Admin Console require online; server IS online, so no annotation
    assert "Stop Server [SERVER OFFLINE]" not in out
    assert "Admin Console [SERVER OFFLINE]" not in out


def test_purge_bots_annotation_shown_when_server_down():
    """Verify Reset & Purge Playerbots shows [SERVER OFFLINE] in Bot Management menu when server is offline."""
    stdout, stderr, code = run_menu_py_with_inputs(["3", "0", "0"])
    assert code == 0
    assert "Reset & Purge Playerbots [SERVER OFFLINE]" in stdout


def test_requires_server_attribute_on_options():
    """Verify requires_server attribute is set correctly on option objects."""
    import skirmish.menu as menu_mod
    menu = menu_mod.create_application_menus()

    server_menu = menu.options[0].sub_menu
    start_opt = next(o for o in server_menu.options if o.key == "1")
    stop_opt = next(o for o in server_menu.options if o.key == "2")
    console_opt = next(o for o in server_menu.options if o.key == "5")
    build_opt = next(o for o in server_menu.options if o.key == "3")

    assert start_opt.requires_server == "offline", "Start Server should require server offline"
    assert stop_opt.requires_server == "online", "Stop Server should require server online"
    assert console_opt.requires_server == "online", "Admin Console should require server online"
    assert build_opt.requires_server is None, "Build Server should have no server requirement"

    bot_menu = menu.options[2].sub_menu
    purge_opt = next(o for o in bot_menu.options if o.key == "5")
    assert purge_opt.requires_server == "online", "Reset & Purge Playerbots should require server online"


def test_generate_srp6_verifier():
    """Verify generate_srp6_verifier produces valid 32-byte hex salt and verifier."""
    import skirmish.menu as menu_mod
    salt_hex, verifier_hex = menu_mod.generate_srp6_verifier("ahbot", "password")
    assert len(salt_hex) == 64
    assert len(verifier_hex) == 64
    assert all(c in "0123456789abcdefABCDEF" for c in salt_hex)
    assert all(c in "0123456789abcdefABCDEF" for c in verifier_hex)





