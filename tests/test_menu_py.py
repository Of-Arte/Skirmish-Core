import os
import sys
import subprocess
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

MENU_PY = os.path.join(REPO_ROOT, "skirmish", "menu.py")
CONF_FILE = os.path.join(REPO_ROOT, "env", "dist", "etc", "modules", "playerbots.conf")



@pytest.fixture(autouse=True)
def isolate_config():
    """Backup playerbots.conf before test execution and restore it afterwards."""
    original_content = None
    if os.path.exists(CONF_FILE):
        with open(CONF_FILE, "r", encoding="utf-8") as f:
            original_content = f.read()

    yield

    if original_content is not None:
        with open(CONF_FILE, "w", encoding="utf-8") as f:
            f.write(original_content)


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


def test_health_check_option():
    """Verify Option 1 -> Option 5 executes HealthChecker diagnostics."""
    stdout, stderr, code = run_menu_py_with_inputs(["1", "5", "0", "0"])
    assert code == 0
    assert "SKIRMISHCORE COMPREHENSIVE HEALTH CHECK" in stdout
    assert "System & Python Environment" in stdout
    assert "HEALTH CHECK RESULT" in stdout


def test_skirmish_menu_back():
    """Verify navigation into Skirmish menu and returning via 0."""
    stdout, stderr, code = run_menu_py_with_inputs(["2", "0", "0"])
    assert code == 0
    assert "SKIRMISH MODE SETUP" in stdout


def test_expansion_menu_back():
    """Verify navigation into Expansion Setup menu and returning via 0."""
    stdout, stderr, code = run_menu_py_with_inputs(["3", "0", "0"])
    assert code == 0
    assert "EXPANSION PROGRESSION CONTROL" in stdout


def test_bot_management_menu_back():
    """Verify navigation into Bot Management menu and returning via 0."""
    stdout, stderr, code = run_menu_py_with_inputs(["4", "0", "0"])
    assert code == 0
    assert "BOT MANAGEMENT & POPULATION" in stdout


def test_bot_population_submenu_back():
    """Verify navigation into Bot Population Density setup and returning."""
    stdout, stderr, code = run_menu_py_with_inputs(["4", "1", "0", "0", "0"])
    assert code == 0
    assert "BOT POPULATION DENSITY SETUP" in stdout


def test_bot_population_presets_config_mutation():
    """Verify Low, Medium, High bot population choices write correct Min/Max values to playerbots.conf."""
    # Test Low Preset [100-300]
    stdout, stderr, code = run_menu_py_with_inputs(["4", "1", "1", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Bot population set to Low [100-300]" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.MinRandomBots = 100" in content
        assert "AiPlayerbot.MaxRandomBots = 300" in content

    # Test High Preset [1000-2000]
    stdout, stderr, code = run_menu_py_with_inputs(["4", "1", "3", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Bot population set to High [1000-2000]" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.MinRandomBots = 1000" in content
        assert "AiPlayerbot.MaxRandomBots = 2000" in content

    # Reset to Medium Preset [500-1000]
    stdout, stderr, code = run_menu_py_with_inputs(["4", "1", "2", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Bot population set to Medium [500-1000]" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.MinRandomBots = 500" in content
        assert "AiPlayerbot.MaxRandomBots = 1000" in content


def test_rpg_weight_preset_config_mutation():
    """Verify Open World RPG presets update RpgStatusProbWeight values in playerbots.conf."""
    stdout, stderr, code = run_menu_py_with_inputs(["4", "2", "4", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Open World RPG Activity set to 'World PvP Skirmishers'" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.RpgStatusProbWeight.OutdoorPvp = 80" in content
        assert "AiPlayerbot.RpgStatusProbWeight.WanderRandom = 35" in content


def test_expansion_mode_config_mutation():
    """Verify Expansion Setup options update playerbots.conf RandomBotMaxLevel and RandomBotMaps."""
    stdout, stderr, code = run_menu_py_with_inputs(["3", "1", "", "0", "0", "0"])
    assert code == 0
    assert "Configuring Classic Mode" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.RandomBotMaxLevel = 60" in content
        assert "AiPlayerbot.RandomBotMaps = 0,1" in content


def test_skirmish_bracket_config_mutation():
    """Verify Skirmish Mode sets correct Min/Max level ranges and maps in playerbots.conf."""
    stdout, stderr, code = run_menu_py_with_inputs(["2", "1", "n", "", "0", "0", "0"])
    assert code == 0
    assert "SKIRMISH MODE ACTIVE" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.RandomBotMinLevel = 10" in content
        assert "AiPlayerbot.RandomBotMaxLevel = 19" in content


def test_skirmish_custom_range_validation():
    """Verify custom skirmish level range validation catches Min > Max errors."""
    stdout, stderr, code = run_menu_py_with_inputs(["2", "9", "50", "20", "", "0", "0"])
    assert code == 0
    assert "Invalid input: Minimum level cannot be greater than maximum level." in stdout


def test_custom_population_input_validation():
    """Verify custom bot population density validates non-integers and Min > Max bounds."""
    # Invalid integer
    stdout, stderr, code = run_menu_py_with_inputs(["4", "1", "4", "abc", "200", "", "0", "0", "0"])
    assert code == 0
    assert "Invalid input: Bot count must be a positive integer." in stdout

    # Min > Max
    stdout, stderr, code = run_menu_py_with_inputs(["4", "1", "4", "1500", "500", "", "0", "0", "0"])
    assert code == 0
    assert "Invalid input: Minimum bot count cannot be greater than maximum bot count." in stdout

    # Valid custom population [450-850]
    stdout, stderr, code = run_menu_py_with_inputs(["4", "1", "4", "450", "850", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Bot population set to Custom [450-850]" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.MinRandomBots = 450" in content
        assert "AiPlayerbot.MaxRandomBots = 850" in content


def test_linux_admin_console_and_logs_compatibility(monkeypatch):
    """Verify admin_console_action and logs_action behave gracefully when os.name != 'nt' (Linux/macOS)."""
    import os
    import skirmish.menu as menu_mod

    # Patch os.name to simulate posix / Linux
    monkeypatch.setattr(os, "name", "posix")

    # Mock subprocess.run to verify it calls docker attach / logs directly without start/cmd
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

    # Run admin console action
    menu_mod.admin_console_action({})
    assert len(calls) == 1
    assert calls[0] == ["docker", "attach", "ac-worldserver"]

    # Run logs action
    calls.clear()
    menu_mod.logs_action({})
    assert len(calls) == 1
    assert calls[0] == ["docker", "compose", "logs", "-f", "ac-worldserver"]


def test_bot_starting_level_mode_config_mutation():
    """Verify Bot Starting Level Mode toggles DisableRandomLevels in playerbots.conf."""
    stdout, stderr, code = run_menu_py_with_inputs(["4", "3", "1", "n", "", "0", "0"])
    assert code == 0
    assert "SUCCESS: Forced Level 1 Bot Spawns Enabled!" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.DisableRandomLevels = 1" in content
        assert "AiPlayerbot.RandombotStartingLevel = 1" in content

    stdout, stderr, code = run_menu_py_with_inputs(["4", "3", "2", "", "0", "0"])
    assert code == 0
    assert "SUCCESS: Random Level Bot Spawns Enabled!" in stdout
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.DisableRandomLevels = 0" in content





