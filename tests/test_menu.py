import os
import subprocess
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MENU_CMD = os.path.join(REPO_ROOT, "menu.cmd")
CONF_FILE = os.path.join(REPO_ROOT, "env", "dist", "etc", "modules", "playerbots.conf")

if os.name == "nt":
    LAUNCHER_CMD = ["cmd.exe", "/c", os.path.join(REPO_ROOT, "menu.cmd")]
else:
    LAUNCHER_CMD = ["bash", os.path.join(REPO_ROOT, "menu.sh")]


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

def run_menu_with_inputs(inputs, timeout=15):
    """
    Runs menu.cmd on Windows or menu.sh on Linux passing exact sequence of inputs.
    Appends exit command ('0') to ensure process completes cleanly.
    Returns (stdout, stderr, returncode).
    """
    full_inputs = list(inputs)
    if not full_inputs or full_inputs[-1] != "0":
        full_inputs.append("0")
    
    env = dict(os.environ, SKIRMISHCORE_TEST_MODE="1")
    input_str = "\n".join(full_inputs) + "\n"
    proc = subprocess.Popen(
        LAUNCHER_CMD,
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
    """Verify that selecting option 0 exits cleanly with returncode 0 without crashing."""
    stdout, stderr, code = run_menu_with_inputs(["0"])
    assert code == 0
    assert "SKIRMISHCORE CONTROL HUB" in stdout

def test_invalid_input_handling():
    """Verify invalid options display warning and return to main menu without terminating shell."""
    stdout, stderr, code = run_menu_with_inputs(["invalid_choice", "0"])
    assert code == 0
    assert "Invalid choice. Please try again." in stdout

def test_server_controls_menu_back():
    """Verify navigation into Server Controls and returning via 0."""
    stdout, stderr, code = run_menu_with_inputs(["1", "0", "0"])
    assert code == 0
    assert "SERVER CONTROLS & ADMIN" in stdout

def test_skirmish_menu_back():
    """Verify navigation into Skirmish menu and returning via 0."""
    stdout, stderr, code = run_menu_with_inputs(["2", "0", "0"])
    assert code == 0
    assert "SKIRMISH MODE SETUP" in stdout

def test_expansion_menu_back():
    """Verify navigation into Expansion Setup menu and returning via 0."""
    stdout, stderr, code = run_menu_with_inputs(["3", "0", "0"])
    assert code == 0
    assert "EXPANSION PROGRESSION CONTROL" in stdout

def test_bot_management_menu_back():
    """Verify navigation into Bot Management & Population menu and returning via 0."""
    stdout, stderr, code = run_menu_with_inputs(["4", "0", "0"])
    assert code == 0
    assert "BOT MANAGEMENT & POPULATION" in stdout

def test_bot_population_submenu_back():
    """Verify navigation into Bot Population Density setup and returning to bot menu and then main menu."""
    stdout, stderr, code = run_menu_with_inputs(["4", "1", "0", "0", "0"])
    assert code == 0
    assert "BOT POPULATION DENSITY SETUP" in stdout

def test_bot_population_presets_config_mutation():
    """Verify Low, Medium, High bot population choices write correct Min/Max values to playerbots.conf."""
    conf_path = CONF_FILE
    
    # Test Low Preset [100-300]
    stdout, stderr, code = run_menu_with_inputs(["4", "1", "1", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Bot population set to Low [100-300]" in stdout
    with open(conf_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.MinRandomBots = 100" in content
        assert "AiPlayerbot.MaxRandomBots = 300" in content

    # Test High Preset [1000-2000]
    stdout, stderr, code = run_menu_with_inputs(["4", "1", "3", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Bot population set to High [1000-2000]" in stdout
    with open(conf_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.MinRandomBots = 1000" in content
        assert "AiPlayerbot.MaxRandomBots = 2000" in content

    # Reset to Medium Preset [500-1000]
    stdout, stderr, code = run_menu_with_inputs(["4", "1", "2", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Bot population set to Medium [500-1000]" in stdout
    with open(conf_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.MinRandomBots = 500" in content
        assert "AiPlayerbot.MaxRandomBots = 1000" in content


def test_rpg_weight_preset_config_mutation():
    """Verify Open World RPG presets update RpgStatusProbWeight values in playerbots.conf."""
    conf_path = CONF_FILE
    stdout, stderr, code = run_menu_with_inputs(["4", "2", "4", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Open World RPG Activity set to 'World PvP Skirmishers'" in stdout
    with open(conf_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.RpgStatusProbWeight.OutdoorPvp = 80" in content
        assert "AiPlayerbot.RpgStatusProbWeight.WanderRandom = 35" in content

def test_expansion_mode_config_mutation():
    """Verify Expansion Setup options update playerbots.conf RandomBotMaxLevel and RandomBotMaps."""
    conf_path = CONF_FILE

    # Test Classic Mode [Max level 60, Maps 0,1] (Choice 3 -> Choice 1 -> Pause -> Choice 0 [exp] -> Choice 0 [main])
    stdout, stderr, code = run_menu_with_inputs(["3", "1", "", "0", "0", "0"])
    assert code == 0
    assert "Configuring Classic Mode" in stdout
    with open(conf_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.RandomBotMaxLevel = 60" in content
        assert "AiPlayerbot.RandomBotMaps = 0,1" in content

def test_skirmish_bracket_config_mutation():
    """Verify Skirmish Mode sets correct Min/Max level ranges and maps in playerbots.conf."""
    conf_path = CONF_FILE

    # Test Twink 19 Bracket (Min 10, Max 19) (Choice 2 -> Choice 1 -> Purge Prompt n -> Pause -> Choice 0 [skirmish] -> Choice 0 [main])
    stdout, stderr, code = run_menu_with_inputs(["2", "1", "n", "", "0", "0", "0"])
    assert code == 0
    assert "SKIRMISH MODE ACTIVE" in stdout
    with open(conf_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.RandomBotMinLevel = 10" in content
        assert "AiPlayerbot.RandomBotMaxLevel = 19" in content

def test_skirmish_custom_range_validation():
    """Verify custom skirmish level range validation catches Min > Max errors."""
    stdout, stderr, code = run_menu_with_inputs(["2", "9", "50", "20", "", "0", "0"])
    assert code == 0
    assert "Invalid input: Minimum level cannot be greater than maximum level." in stdout


def test_custom_population_input_validation():
    """Verify custom bot population density validates non-integers and Min > Max bounds."""
    conf_path = CONF_FILE

    # Invalid integer
    stdout, stderr, code = run_menu_with_inputs(["4", "1", "4", "abc", "200", "", "0", "0", "0"])
    assert code == 0
    assert "Invalid input: Bot count must be a positive integer." in stdout

    # Min > Max
    stdout, stderr, code = run_menu_with_inputs(["4", "1", "4", "1500", "500", "", "0", "0", "0"])
    assert code == 0
    assert "Invalid input: Minimum bot count cannot be greater than maximum bot count." in stdout

    # Valid custom population [450-850]
    stdout, stderr, code = run_menu_with_inputs(["4", "1", "4", "450", "850", "", "0", "0", "0"])
    assert code == 0
    assert "SUCCESS: Bot population set to Custom [450-850]" in stdout
    with open(conf_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "AiPlayerbot.MinRandomBots = 450" in content
        assert "AiPlayerbot.MaxRandomBots = 850" in content



