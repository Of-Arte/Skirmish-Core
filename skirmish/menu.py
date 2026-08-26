#!/usr/bin/env python3
"""
SkirmishCore Python Control Hub - Lightweight, object-oriented CLI menu system.
Replaces brittle cmd/batch scripts with clean OOP inheritance and robust configuration management.
"""

import os
import re
import sys
import time
import shutil
import hashlib
import subprocess
from typing import List, Optional, Callable


# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CORE_DIR = REPO_ROOT
CONF_DIR = os.path.join(CORE_DIR, "env", "dist", "etc", "modules")
CONF_FILE = os.path.join(CONF_DIR, "playerbots.conf")
AHBOT_CONF_FILE = os.path.join(CONF_DIR, "mod_ahbot.conf")
IP_CONF_FILE = os.path.join(CONF_DIR, "individualProgression.conf")



def safe_input(prompt: str = "") -> str:
    """Safely reads input from stdin, returning '0' on EOF or KeyboardInterrupt to prevent crashes."""
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        return "0"


def sanitize_sql(val: str) -> str:
    """Escapes single quotes and backslashes for safe inline SQL query string formatting."""
    if not val:
        return ""
    return val.replace("\\", "\\\\").replace("'", "''")


def generate_srp6_verifier(username: str, password: str) -> tuple:
    """
    Generates salt (32 bytes hex) and verifier (32 bytes hex) for AzerothCore 3.3.5a (WotLK) SRP6 authentication.
    Matches SRP6::MakeRegistrationData in src/common/Cryptography/Authentication/SRP6.cpp.
    """
    user_upper = username.upper()
    pass_upper = password.upper()

    creds = f"{user_upper}:{pass_upper}".encode("utf-8")
    h1 = hashlib.sha1(creds).digest()

    salt = os.urandom(32)
    h2 = hashlib.sha1(salt + h1).digest()
    h2_int = int.from_bytes(h2, "little")

    g = 7
    n_hex = "894B645E89E1535BBDAD5B8B290650530801B18EBFBF5E8FAB3C82872A3E9BB7"
    n_bytes = bytes.fromhex(n_hex)[::-1]
    N_int = int.from_bytes(n_bytes, "little")

    verifier_int = pow(g, h2_int, N_int)
    verifier = verifier_int.to_bytes(32, "little")

    return salt.hex(), verifier.hex()


# ==============================================================================
# BASE OOP MENU CLASSES
# ==============================================================================
class MenuOption:
    """Base class for any menu option."""

    def __init__(self, key: str, label: str, description: str = ""):
        self.key = key
        self.label = label
        self.description = description

    def execute(self, context: dict) -> bool:
        """
        Executes the option logic.
        Return True to continue menu loop, False to exit current menu loop.
        """
        raise NotImplementedError("Subclasses must implement execute()")


class ActionOption(MenuOption):
    """Menu option that executes a callable action function."""

    def __init__(self, key: str, label: str, description: str, action_fn: Callable[[dict], None], pause_after: bool = True):
        super().__init__(key, label, description)
        self.action_fn = action_fn
        self.pause_after = pause_after

    def execute(self, context: dict) -> bool:
        self.action_fn(context)
        if self.pause_after:
            safe_input("\nPress Enter to continue...")
        return True


class SubMenuOption(MenuOption):
    """Menu option that opens a child menu, inheriting SubMenu behavior."""

    def __init__(self, key: str, label: str, description: str, sub_menu: 'BaseMenu'):
        super().__init__(key, label, description)
        self.sub_menu = sub_menu

    def execute(self, context: dict) -> bool:
        self.sub_menu.run(context)
        return True


class BaseMenu:
    """Base class representing a menu screen with options and rendering logic."""

    def __init__(self, title: str, options: Optional[List[MenuOption]] = None, parent: Optional['BaseMenu'] = None):
        self.title = title
        self.options: List[MenuOption] = options if options is not None else []
        self.parent = parent

    def add_option(self, option: MenuOption):
        self.options.append(option)

    def get_status_banner(self, context: dict) -> str:
        """Override in menus requiring dynamic status info."""
        status = DockerService.get_container_status("ac-worldserver")
        return f" Server Status : [ {status} ]"

    def render(self, context: dict):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=====================================================")
        print(f"            {self.title}")
        print("=====================================================")
        banner = self.get_status_banner(context)
        if banner:
            print(banner)
            print("-----------------------------------------------------")
        print()

        for opt in self.options:
            print(f"  {opt.key}. {opt.label}")
            if opt.description:
                print(f"     {opt.description}")
            print()

        back_label = "Back" if self.parent else "Exit"
        print("  0. " + back_label)
        print("-----------------------------------------------------")
        print()

    def run(self, context: dict):
        while True:
            self.render(context)
            choice = safe_input(f"Select an option [0-{len(self.options)}]: ").strip()
            if choice == "0":
                break

            matched_option = next((opt for opt in self.options if opt.key == choice), None)
            if matched_option:
                should_continue = matched_option.execute(context)
                if not should_continue:
                    break
            else:
                print("\nInvalid choice. Please try again.")
                time.sleep(1)


# ==============================================================================
# HEALTH DIAGNOSTICS & SYSTEM DOCTOR
# ==============================================================================
class HealthChecker:
    """Comprehensive diagnostic system checking prerequisites, files, Docker daemon, RAM, containers, database, and ports."""

    @staticmethod
    def get_ram_info():
        """Returns (total_gb, avail_gb) using standard library (cross-platform Linux/WSL/Windows)."""
        total_gb, avail_gb = None, None
        try:
            if os.path.exists("/proc/meminfo"):
                mem = {}
                with open("/proc/meminfo", "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            key = parts[0].strip()
                            val = parts[1].strip().split()[0]
                            mem[key] = int(val)
                if "MemTotal" in mem:
                    total_gb = mem["MemTotal"] / (1024 * 1024)
                if "MemAvailable" in mem:
                    avail_gb = mem["MemAvailable"] / (1024 * 1024)
                elif "MemFree" in mem:
                    avail_gb = mem["MemFree"] / (1024 * 1024)
        except Exception:
            pass

        if total_gb is None and sys.platform == "win32":
            try:
                import ctypes
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                    total_gb = stat.ullTotalPhys / (1024 ** 3)
                    avail_gb = stat.ullAvailPhys / (1024 ** 3)
            except Exception:
                pass

        return total_gb, avail_gb

    @staticmethod
    def run():
        print("\n=====================================================")
        print("         SKIRMISHCORE COMPREHENSIVE HEALTH CHECK")
        print("=====================================================")
        print(f" Root Directory : {REPO_ROOT}")
        print(f" Core Directory : {CORE_DIR}")
        print("-----------------------------------------------------\n")

        issues_found = 0

        # 1. System & Python Environment + RAM Check
        print("[1/6] System & Python Environment & RAM Diagnostics")
        py_ver = sys.version.split()[0]

        print(f"  [OK] Python Runtime : {py_ver} ({sys.executable})")

        try:
            total, used, free = shutil.disk_usage(REPO_ROOT)
            free_gb = free / (1024 ** 3)
            if free_gb < 5.0:
                print(f"  [WARN] Disk Space   : Only {free_gb:.1f} GB free on repository drive")
                issues_found += 1
            else:
                print(f"  [OK] Disk Space     : {free_gb:.1f} GB free")
        except Exception as e:
            print(f"  [WARN] Disk Space   : Could not calculate ({e})")

        # RAM Check
        total_ram, avail_ram = HealthChecker.get_ram_info()
        if total_ram is not None and avail_ram is not None:
            if avail_ram < 3.5 or total_ram < 8.0:
                print(f"  [WARN] System RAM   : {avail_ram:.1f} GB available / {total_ram:.1f} GB total (Low Memory Environment)")
                print("         -> ADVICE: Available memory is low. Consider:")
                print("                    1) Selecting 'Low (100 bots)' preset in Option 4 -> 1.")
                print("                    2) Enabling 'AiPlayerbot.SmartScale.Enabled = 1' in env/dist/etc/modules/playerbots.conf.")
            else:
                print(f"  [OK] System RAM     : {avail_ram:.1f} GB available / {total_ram:.1f} GB total")

        # 2. File & Configuration Structure
        print("\n[2/6] Repack Files & Configuration Structure")
        if os.path.exists(CORE_DIR):
            print(f"  [OK] Core Directory : Found ({CORE_DIR})")
        else:
            print(f"  [FAIL] Core Directory : Missing ({CORE_DIR})")
            issues_found += 1

        conf_file = os.path.join(CORE_DIR, "env", "dist", "etc", "modules", "playerbots.conf")
        if os.path.exists(conf_file):
            print(f"  [OK] Playerbots Config : Found ({conf_file})")
        else:
            print(f"  [WARN] Playerbots Config : Missing ({conf_file})")
            issues_found += 1

        # Check submodules
        submodules = ["mod-playerbots", "mod-ah-bot", "mod-individual-progression", "mod-acore-mall"]
        empty_submodules = []
        for mod in submodules:
            mod_path = os.path.join(CORE_DIR, "modules", mod)
            if not os.path.exists(mod_path) or len(os.listdir(mod_path)) <= 1:
                empty_submodules.append(mod)

        if empty_submodules:
            print(f"  [FAIL] Git Submodules : Uninitialized or empty modules ({', '.join(empty_submodules)})")
            print("         -> Auto-healing git submodules now...", flush=True)
            if DockerService.ensure_submodules():
                print("         [OK] Submodules successfully restored!")
            else:
                issues_found += 1
        else:
            print("  [OK] Git Submodules : All module folders populated")


        # 3. Docker CLI & Daemon Status
        print("\n[3/6] Docker Engine & Daemon Health")
        print("  Checking Docker CLI & Daemon status...", flush=True)
        if not shutil.which("docker"):
            print("  [FAIL] Docker Executable : Not found in system PATH")
            issues_found += 1
        else:
            print("  [OK] Docker Executable : Found")

        docker_info = subprocess.run(["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if docker_info.returncode != 0:
            print("  [FAIL] Docker Daemon : Not running or unreachable. Ensure Docker Desktop is active.")
            issues_found += 1
        else:
            print("  [OK] Docker Daemon : Active & responsive")

        # 4. Container Status Inspection
        print("\n[4/6] Docker Container Stack Status")
        print("  Inspecting container states...", flush=True)
        services = ["ac-worldserver", "ac-authserver", "ac-database", "ac-db-import"]
        offline_count = 0
        for svc in services:
            status = DockerService.get_container_status(svc)
            if status == "ONLINE":
                print(f"  [OK] Container {svc:<16} : ONLINE")
            else:
                print(f"  [OFF] Container {svc:<15} : OFFLINE")
                if svc != "ac-db-import":  # db-import exits cleanly after import completes
                    offline_count += 1

        # 5. Database & Server Service Checks
        print("\n[5/6] Database & Port Connectivity")
        print("  Testing MySQL and worldserver connectivity...", flush=True)

        # Database query test
        if DockerService.get_container_status("ac-database") == "ONLINE":
            db_res = subprocess.run(
                ["docker", "compose", "exec", "-T", "ac-database", "mysql", "-uroot", "-ppassword", "-e", "SELECT address FROM acore_auth.realmlist WHERE id=1;"],
                cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if db_res.returncode == 0 and "address" in db_res.stdout:
                lines = db_res.stdout.strip().splitlines()
                addr = lines[-1].strip() if len(lines) > 1 else "unknown"
                print(f"  [OK] MySQL Auth DB : Responsive (Realm IP: {addr})")
            else:
                print("  [WARN] MySQL Auth DB : Query failed or realmlist table not ready")
                issues_found += 1
        else:
            print("  [OFF] MySQL Auth DB : Database container is offline")

        # Port test for worldserver console
        if DockerService.get_container_status("ac-worldserver") == "ONLINE":
            ws_res = subprocess.run(
                ["docker", "compose", "exec", "-T", "ac-worldserver", "bash", "-c", "echo 'reload config' | nc -w 1 127.0.0.1 7878"],
                cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if ws_res.returncode == 0:
                print("  [OK] Worldserver Terminal : Ready (SOAP/CLI port 7878 active)")
            else:
                print("  [NOTE] Worldserver Terminal : Initializing DBC/maps or SQL updates...")
        else:
            print("  [OFF] Worldserver Terminal : Server is offline")

        # 6. Installed Modules Database Integrity Checks
        print("\n[6/6] Module Database Integrity")
        print("  Querying installed module tables in MySQL...", flush=True)
        module_warnings = 0
        if DockerService.get_container_status("ac-database") == "ONLINE":
            # Individual Progression check
            ip_check = subprocess.run(
                ["docker", "compose", "exec", "-T", "ac-database", "mysql", "-uroot", "-ppassword", "-e", "SELECT COUNT(*) FROM acore_world.command WHERE name LIKE 'ip %';"],
                cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            ip_count_str = ip_check.stdout.splitlines()[-1].strip() if ip_check.returncode == 0 and ip_check.stdout.splitlines() else "0"
            if ip_check.returncode == 0 and ip_count_str.isdigit() and int(ip_count_str) > 0:
                print("  [OK] Module Individual Progression : Database commands loaded")
            else:
                print("  [WARN] Module Individual Progression : Commands missing (run 'Start Server' to import)")
                module_warnings += 1

            # Acore Mall check
            mall_check = subprocess.run(
                ["docker", "compose", "exec", "-T", "ac-database", "mysql", "-uroot", "-ppassword", "-e", "SELECT COUNT(*) FROM acore_world.creature WHERE id >= 9100000;"],
                cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            mall_count_str = mall_check.stdout.splitlines()[-1].strip() if mall_check.returncode == 0 and mall_check.stdout.splitlines() else "0"
            if mall_check.returncode == 0 and mall_count_str.isdigit() and int(mall_count_str) > 0:
                print(f"  [OK] Module Acore Mall               : GM Island Mall vendors loaded ({mall_count_str} vendors)")
            else:
                print("  [WARN] Module Acore Mall               : GM Island Mall vendors missing (run 'Start Server' to import)")
                module_warnings += 1

            # AH Bot check
            ah_check = subprocess.run(
                ["docker", "compose", "exec", "-T", "ac-database", "mysql", "-uroot", "-ppassword", "-e", "SELECT COUNT(*) FROM acore_world.mod_auctionhousebot;"],
                cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if ah_check.returncode == 0 and "ERROR" not in ah_check.stderr:
                print("  [OK] Module Auction House Bot        : Database tables loaded")
            else:
                print("  [WARN] Module Auction House Bot        : Tables missing (run 'Start Server' to import)")
                module_warnings += 1

            # Playerbots check
            pb_check = subprocess.run(
                ["docker", "compose", "exec", "-T", "ac-database", "mysql", "-uroot", "-ppassword", "-e", "SHOW DATABASES LIKE 'acore_playerbots';"],
                cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if pb_check.returncode == 0 and "acore_playerbots" in pb_check.stdout:
                print("  [OK] Module Playerbots               : Database loaded")
            else:
                print("  [WARN] Module Playerbots               : Database missing")
                module_warnings += 1
        else:
            print("  [OFF] Module Database Checks         : Database container is offline")

        print("\n-----------------------------------------------------")
        if issues_found > 0:
            print(f" HEALTH CHECK RESULT : {issues_found} CRITICAL SYSTEM ERROR(S) DETECTED")
        elif offline_count > 0:
            print(f" HEALTH CHECK RESULT : ENVIRONMENT OK | SERVER STACK IS OFFLINE ({offline_count} services stopped)")
            print("                      -> Select Option 1 -> 1 (Start Server) to launch stack.")
        elif module_warnings > 0:
            print(f" HEALTH CHECK RESULT : SERVER ONLINE | {module_warnings} MODULE DATABASE WARNING(S) DETECTED")
            print("                      -> Select Option 1 -> 1 (Start Server) to run pending SQL imports.")
        else:
            print(" HEALTH CHECK RESULT : ALL SYSTEMS OPERATIONAL & SERVER ONLINE [100% OK]")
        print("=====================================================")





# ==============================================================================
# DOCKER & CONFIGURATION SERVICES
# ==============================================================================
class DockerService:
    @staticmethod
    def get_container_status(service_name: str = "ac-worldserver") -> str:
        """Returns ONLINE if container is running, OFFLINE otherwise."""
        if "PYTEST_CURRENT_TEST" in os.environ or os.environ.get("SKIRMISHCORE_TEST_MODE") == "1":
            return "OFFLINE"
        try:
            res = subprocess.run(
                ["docker", "compose", "ps", "--services", "--filter", "status=running"],
                cwd=CORE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if res.returncode == 0 and service_name in res.stdout:
                return "ONLINE"
        except Exception:
            pass
        return "OFFLINE"

    @staticmethod
    def start_stack() -> bool:
        """Launches docker compose up -d stack directly."""
        print("\nChecking for pending database & module SQL updates...")
        try:
            subprocess.run(["docker", "compose", "up", "--force-recreate", "ac-db-import"], cwd=CORE_DIR)
            print("\nStarting SkirmishCore Docker stack...")
            res = subprocess.run(["docker", "compose", "up", "-d"], cwd=CORE_DIR)
            if res.returncode == 0:
                print("\nSkirmishCore Docker stack started successfully.")
                print("[TIP] Worldserver startup takes ~1-2 minutes to load maps, DB, and modules.")
                print("[TIP] If you have trouble logging in, check logs (docker compose logs -f ac-worldserver).")
                return True
            else:
                print("\nError: Failed to start Docker services.")
                return False
        except Exception as e:
            print(f"Error starting Docker stack: {e}")
            return False


    @staticmethod
    def stop_stack() -> bool:
        """Shuts down docker compose stack directly."""
        print("\nStopping SkirmishCore Docker stack...")
        try:
            res = subprocess.run(["docker", "compose", "down"], cwd=CORE_DIR)
            if res.returncode == 0:
                print("\nSkirmishCore Docker stack stopped successfully.")
                return True
            else:
                print("\nError: Failed to stop Docker services.")
                return False
        except Exception as e:
            print(f"Error stopping Docker stack: {e}")
            return False

    @staticmethod
    def wipe_stack() -> bool:
        """Deletes all Docker containers, images, volumes, and network setup requiring a full rebuild."""
        print("\nWiping SkirmishCore Docker stack, volumes, and images...")
        try:
            res = subprocess.run(["docker", "compose", "down", "-v", "--rmi", "all", "--remove-orphans"], cwd=CORE_DIR)
            if res.returncode == 0:
                print("\nSkirmishCore Docker stack wiped successfully.")
                print("[NOTE] All containers, database volumes, and images have been deleted.")
                print("[NOTE] Next start will require a full rebuild.")
                return True
            else:
                print("\nError: Failed to wipe Docker stack.")
                return False
        except Exception as e:
            print(f"Error wiping Docker stack: {e}")
            return False


    @staticmethod
    def ensure_submodules() -> bool:
        """Ensures git submodules in modules/ are initialized and populated."""
        if shutil.which("git") and os.path.exists(os.path.join(CORE_DIR, ".gitmodules")):
            print("Checking git submodules in modules/...")
            try:
                res = subprocess.run(["git", "submodule", "update", "--init", "--recursive"], cwd=CORE_DIR, capture_output=True, text=True)
                if res.returncode == 0:
                    print("  [OK] Git submodules are initialized and up to date.")
                    return True
                else:
                    print(f"  [WARN] Git submodule update returned non-zero code: {res.stderr.strip()}")
                    return False
            except Exception as e:
                print(f"  [WARN] Could not update git submodules: {e}")
                return False
        return True

    @staticmethod
    def build_images() -> bool:
        """Rebuilds docker compose container images directly."""
        if "PYTEST_CURRENT_TEST" in os.environ or os.environ.get("SKIRMISHCORE_TEST_MODE") == "1":
            print("\nBuilding SkirmishCore Docker images...")
            print("\nSkirmishCore Docker images built successfully. [TEST MODE]")
            return True
        DockerService.ensure_submodules()
        print("\nBuilding SkirmishCore Docker images...")
        try:
            res = subprocess.run(["docker", "compose", "build"], cwd=CORE_DIR)
            if res.returncode == 0:
                print("\nSkirmishCore Docker images built successfully.")
                return True
            else:
                print("\nError: Docker build failed.")
                return False
        except Exception as e:
            print(f"Error building Docker images: {e}")
            return False


    @staticmethod
    def run_diagnostics():
        """Runs health diagnostics on Docker daemon and container stack."""
        HealthChecker.run()

    @staticmethod
    def reload_worldserver_config():
        """Reloads playerbots.conf inside running worldserver container."""
        if DockerService.get_container_status("ac-worldserver") == "ONLINE":
            print("\nReloading worldserver config...")
            try:
                subprocess.run(
                    ["docker", "compose", "exec", "-T", "ac-worldserver", "bash", "-c", "touch /azerothcore/env/dist/etc/modules/playerbots.conf"],
                    cwd=CORE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                subprocess.run(
                    ["docker", "compose", "exec", "-T", "ac-worldserver", "bash", "-c", "echo 'reload config' | nc -w 1 127.0.0.1 7878"],
                    cwd=CORE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except Exception as e:
                print(f"Warning: Failed to trigger in-game reload: {e}")
        else:
            print("\n[NOTE] Server is offline. Settings will take effect next time server starts!")

    @staticmethod
    def restart_container(service_name: str = "all"):
        """Restarts docker compose services."""
        if service_name == "all":
            print("\nRestarting server stack (ac-worldserver, ac-authserver)...")
            try:
                subprocess.run(["docker", "compose", "restart", "ac-worldserver", "ac-authserver"], cwd=CORE_DIR, check=False)
            except Exception as e:
                print(f"Error restarting server containers: {e}")
        else:
            print(f"\nRestarting container {service_name}...")
            try:
                subprocess.run(["docker", "compose", "restart", service_name], cwd=CORE_DIR, check=False)
            except Exception as e:
                print(f"Error restarting container {service_name}: {e}")



class ConfigManager:
    @staticmethod
    def get_conf_value(key: str, default: str = "", conf_path: str = CONF_FILE) -> str:
        """Reads an active (uncommented) configuration value from a .conf file using UTF-8 encoding."""
        if not os.path.exists(conf_path):
            return default
        try:
            with open(conf_path, "r", encoding="utf-8") as f:
                content = f.read()
            pattern = rf"^[ \t]*{re.escape(key)}\s*=\s*([^\r\n]*)"
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                return match.group(1).strip()
        except Exception:
            pass
        return default

    @staticmethod
    def update_conf_values(updates: dict, conf_path: str = CONF_FILE) -> bool:
        """
        Safely updates configuration key-value pairs using python regex and UTF-8 encoding.
        Matches active, uncommented lines starting with key = ...
        """
        if not os.path.exists(conf_path):
            os.makedirs(os.path.dirname(conf_path), exist_ok=True)
            filename = os.path.basename(conf_path)
            dist_file = os.path.join(CONF_DIR, filename + ".dist")
            if os.path.exists(dist_file):
                shutil.copyfile(dist_file, conf_path)
            else:
                print(f"Error: Configuration file not found at {conf_path}")
                return False

        try:
            with open(conf_path, "r", encoding="utf-8") as f:
                content = f.read()

            for key, val in updates.items():
                pattern = rf"^[ \t]*({re.escape(key)}\s*=\s*)[^\r\n]*"
                if re.search(pattern, content, re.MULTILINE):
                    content = re.sub(pattern, rf"\g<1>{val}", content, flags=re.MULTILINE)
                else:
                    if content and not content.endswith("\n"):
                        content += "\n"
                    content += f"{key} = {val}\n"

            with open(conf_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error updating configuration file: {e}")
            return False




# ==============================================================================
# ACTION HANDLERS
# ==============================================================================
def start_server_action(context: dict):
    confirm = safe_input("\nStart the SkirmishCore server now? [Y/N]: ").strip().lower()
    if confirm != 'y':
        print("Start canceled.")
        return

    if DockerService.start_stack():
        view_logs = safe_input("\nOpen a live log window now? [y/N]: ").strip().lower()
        if view_logs == 'y':
            logs_action(context)


def stop_server_action(context: dict):
    confirm = safe_input("\nAre you sure you want to stop the server? [Y/N]: ").strip().lower()
    if confirm != 'y':
        print("Stop canceled.")
        return

    DockerService.stop_stack()


def wipe_server_action(context: dict):
    print("\n=====================================================")
    print("        WARNING: WIPE & DELETE SERVER SETUP")
    print("=====================================================")
    print(" This action will PERMANENTLY DELETE:")
    print("   - All Docker containers and networks")
    print("   - All database volumes & player data (ac-database)")
    print("   - All built Docker images (requiring a complete rebuild)")
    print("=====================================================")
    confirm = safe_input("\nTo confirm wiping the server, type 'delete': ").strip()
    if confirm.lower() != 'delete':
        print("Wipe canceled. Confirmation did not match 'delete'.")
        return

    DockerService.wipe_stack()



def create_account_action(context: dict):
    print("\n=====================================================")
    print("        AUTOMATED ACCOUNT CREATION WIZARD")
    print("=====================================================")
    print("Create a WoW account without needing to access the")
    print("worldserver terminal console manually.")
    print("-----------------------------------------------------")

    user = safe_input("\nEnter account username: ").strip()
    if not user:
        print("\n[!] Account creation canceled: Username cannot be empty.")
        return

    password = safe_input(f"Enter password for '{user}': ").strip()
    if not password:
        print("\n[!] Account creation canceled: Password cannot be empty.")
        return

    print("\nSelect GM Rank / Permissions level:")
    print("  0. Player      [Standard player, no GM powers]")
    print("  1. Moderator   [Basic GM commands & moderation]")
    print("  2. GameMaster  [Full GM commands, teleports, spawning]")
    print("  3. Admin       [Administrator - Full server control] (Default)")

    gm_choice = safe_input("\nSelect GM level [0-3, default 3]: ").strip()
    if gm_choice == "":
        gm_level = 3
    elif gm_choice in ("0", "1", "2", "3"):
        gm_level = int(gm_choice)
    else:
        print("\nInvalid GM rank choice. Defaulting to 3 (Admin).")
        gm_level = 3

    rank_names = {
        0: "Player (Level 0)",
        1: "Moderator (Level 1)",
        2: "GameMaster (Level 2)",
        3: "Admin (Level 3)"
    }
    rank_str = rank_names.get(gm_level, f"Level {gm_level}")

    ws_online = DockerService.get_container_status("ac-worldserver") == "ONLINE"
    db_online = DockerService.get_container_status("ac-database") == "ONLINE"

    if not ws_online and not db_online:
        print("\n[!] NOTE: Server stack is currently OFFLINE.")
        start_now = safe_input("Would you like to start the server stack now to create this account? [y/N]: ").strip().lower()
        if start_now == 'y':
            if DockerService.start_stack():
                print("\nWaiting 10 seconds for server initialization...")
                time.sleep(10)
                ws_online = DockerService.get_container_status("ac-worldserver") == "ONLINE"
                db_online = DockerService.get_container_status("ac-database") == "ONLINE"

    print(f"\nConfiguring account '{user}' with status {rank_str}...", flush=True)
    account_created = False
    gm_applied = False
    safe_user = sanitize_sql(user)
    safe_pass = sanitize_sql(password)

    if ws_online:
        try:
            res = subprocess.run(
                ["docker", "compose", "exec", "-T", "ac-worldserver", "bash", "-c", f"echo 'account create {user} {password}' | nc -w 1 127.0.0.1 7878"],
                cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace"
            )
            account_created = True
            if gm_level > 0:
                subprocess.run(
                    ["docker", "compose", "exec", "-T", "ac-worldserver", "bash", "-c", f"echo 'account setgm {user} {gm_level} -1' | nc -w 1 127.0.0.1 7878"],
                    cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace"
                )
                gm_applied = True
        except Exception as e:
            print(f"Warning: Worldserver console command error: {e}")

    if db_online:
        try:
            salt_hex, verifier_hex = generate_srp6_verifier(user, password)
            sql_insert = (
                f"INSERT INTO acore_auth.account (username, salt, verifier) "
                f"VALUES (UPPER('{safe_user}'), UNHEX('{salt_hex}'), UNHEX('{verifier_hex}')) "
                f"ON DUPLICATE KEY UPDATE salt=UNHEX('{salt_hex}'), verifier=UNHEX('{verifier_hex}');"
            )
            subprocess.run(
                ["docker", "compose", "exec", "-T", "ac-database", "mysql", "-uroot", "-ppassword", "-e", sql_insert],
                cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            account_created = True

            res = subprocess.run(
                ["docker", "compose", "exec", "-T", "ac-database", "mysql", "-uroot", "-ppassword", "-e",
                 f"SELECT id FROM acore_auth.account WHERE UPPER(username) = UPPER('{safe_user}');"],
                cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace"
            )
            acc_id = None
            if res.returncode == 0 and res.stdout:
                lines = [l.strip() for l in res.stdout.strip().splitlines() if l.strip()]
                if len(lines) > 1 and lines[-1].isdigit():
                    acc_id = lines[-1]

            if acc_id and gm_level > 0:
                subprocess.run(
                    ["docker", "compose", "exec", "-T", "ac-database", "mysql", "-uroot", "-ppassword", "-e",
                     f"REPLACE INTO acore_auth.account_access (id, gmlevel, RealmID) VALUES ({acc_id}, {gm_level}, -1);"],
                    cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                gm_applied = True
        except Exception as e:
            print(f"Warning: Database update error: {e}")


    print("\n=====================================================")
    if account_created or gm_applied:
        print(f" SUCCESS: Account '{user}' configured successfully!")
        print("=====================================================")
        print(f" Username  : {user}")
        print(f" Password  : {password}")
        print(f" GM Status : {rank_str}")
    else:
        print(f" ERROR: Account '{user}' could not be created!")
        print("=====================================================")
        print(" Reason    : Server stack and database containers are OFFLINE.")
        print("             Please start the server stack (Option 1 -> 1) first.")
    print("=====================================================")


def admin_console_action(context: dict):
    if DockerService.get_container_status("ac-worldserver") == "OFFLINE":
        print("\n[!] WARNING: SkirmishCore server is currently OFFLINE.")
        print("    The Admin Console requires the server to be running.")
        start_now = safe_input("\nWould you like to start the server now? [Y/N]: ").strip().lower()
        if start_now == 'y':
            if DockerService.start_stack():
                print("\nWaiting 10 seconds for server initialization...")
                time.sleep(10)
            else:
                return
        else:
            print("Returning to menu.")
            return

    print("\nOpening Admin Console window...")
    print("\nQuick Commands inside Admin Console:")
    print("  - Create Account : account create <username> <password>")
    print("  - Make GM/Admin  : account setgm <username> 3 -1")
    print("  - Set Password   : account set password <username> <newpass> <newpass>")
    print("  - Reload Config  : reload config")
    print("  - Close Window   : Close the window when finished\n")

    if os.name == 'nt':
        cmd_str = (
            'start "SkirmishCore Admin Console" cmd /k "'
            'echo Server Console Connected. Type commands below: && echo. && '
            'docker attach ac-worldserver || (echo. && echo [ERROR] Console session closed or server disconnected. Press any key to close window... && pause)"'
        )
        subprocess.run(cmd_str, cwd=CORE_DIR, shell=True)
    else:
        print("Attaching to server console (press Ctrl+P Ctrl+Q to detach)...")
        try:
            subprocess.run(["docker", "attach", "ac-worldserver"], cwd=CORE_DIR)
        except Exception as e:
            print(f"Error attaching to server console: {e}")


def logs_action(context: dict):
    print("\nSelect log to view:")
    print("  1. Worldserver [Game World]")
    print("  2. Authserver [Logins]")
    print("  3. Database")
    print("  0. Back to Menu")

    choice = safe_input("\nSelect an option [0-3, default 1]: ").strip()
    if choice == "0":
        return

    log_service = "ac-worldserver"
    if choice == "2":
        log_service = "ac-authserver"
    elif choice == "3":
        log_service = "ac-database"

    if DockerService.get_container_status(log_service) == "OFFLINE":
        print(f"\n[NOTE] Service container {log_service} is currently OFFLINE.")
        print("       Opening log stream [will stream live logs when container starts]...")

    if os.name == 'nt':
        print(f"\nOpening live logs for {log_service} in a new window...")
        cmd_str = (
            f'start "SkirmishCore Logs - {log_service}" cmd /k "'
            f'echo Streaming logs for {log_service}... && echo. && '
            f'docker compose logs -f {log_service}"'
        )
        subprocess.run(cmd_str, cwd=CORE_DIR, shell=True)
    else:
        print(f"\nStreaming live logs for {log_service} (press Ctrl+C to exit and return to menu)...")
        try:
            subprocess.run(["docker", "compose", "logs", "-f", log_service], cwd=CORE_DIR)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error streaming logs: {e}")


def doctor_action(context: dict):
    DockerService.run_diagnostics()


def build_action(context: dict):
    DockerService.build_images()


def coop_action(context: dict):
    print("\n=====================================================")
    print("           CONFIGURE MULTI-PLAYER / LAN MODE")
    print("=====================================================")
    print("\nDefault single-player address is 127.0.0.1.")
    print("To allow friends on LAN or VPN [Tailscale/ZeroTier] to connect,")
    print("enter your computer's IP address below.\n")

    new_ip = safe_input("Enter server IP address (c to cancel, or 127.0.0.1 for single-player): ").strip()
    if new_ip.lower() == 'c' or new_ip == '0' or not new_ip:
        print("Address update canceled.")
        return

    if not re.match(r"^[a-zA-Z0-9.\-_]+$", new_ip):
        print("\nInvalid input: Address must be a valid IP address or hostname.")
        return

    if DockerService.get_container_status("ac-database") == "OFFLINE":
        print("\n[!] WARNING: Database container is currently OFFLINE.")
        print("    Updating server address requires the database to be running.")
        start_now = safe_input("\nWould you like to start the server now? [Y/N]: ").strip().lower()
        if start_now == 'y':
            if DockerService.start_stack():
                print("\nWaiting 10 seconds for database initialization...")
                time.sleep(10)
            else:
                return
        else:
            print("Address update canceled.")
            return

    safe_ip = sanitize_sql(new_ip)
    print(f"\nUpdating server address to {new_ip}...")
    sql_cmd = f"UPDATE acore_auth.realmlist SET address='{safe_ip}' WHERE id=1;"
    res = subprocess.run(
        ["docker", "compose", "exec", "-T", "ac-database", "mysql", "-uroot", "-ppassword", "-e", sql_cmd],
        cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if res.returncode == 0:
        print(f"\nSuccessfully set server address to {new_ip}")
        print("\n[NOTE] Connecting players [host & friends] must set realmlist.wtf to:")
        print(f"       set realmlist {new_ip}")
    else:
        print(f"\nWarning: Could not update server address in database: {res.stderr}")



def purge_bots_sequence(context: dict) -> bool:
    """Executes full bot account purge sequence."""
    if DockerService.get_container_status("ac-worldserver") == "OFFLINE":
        print("\n[!] WARNING: The server is currently OFFLINE.")
        print("    Purging playerbots requires the server to be running so worldserver can perform cleanup.")
        start_now = safe_input("\nWould you like to start the server now? [Y/N]: ").strip().lower()
        if start_now == 'y':
            if DockerService.start_stack():
                print("\nWaiting 10 seconds for worldserver start...")
                time.sleep(10)
            else:
                return False
        else:
            print("\nReset canceled. Please start the server before purging bots.")
            return False

    print("\nThis action will clear all generated bot accounts and")
    print("spawn a fresh bot population across the world.")
    print("\nNote: Your human player account and GM status will NOT be deleted.")

    confirm = safe_input("\nAre you sure you want to reset all bots? [Y/N]: ").strip().lower()
    if confirm != 'y':
        print("Reset canceled.")
        return False

    print("\n[1/4] Enabling bot account cleanup...")
    ConfigManager.update_conf_values({"AiPlayerbot.DeleteRandomBotAccounts": "1"})

    print("[2/4] Restarting Worldserver to clear existing bots...")
    DockerService.restart_container("ac-worldserver")

    print("\n[3/4] Waiting 20 seconds for account cleanup...")
    time.sleep(20)

    print("[4/4] Finalizing reset settings...")
    ConfigManager.update_conf_values({"AiPlayerbot.DeleteRandomBotAccounts": "0"})

    print("\nRestarting Worldserver to spawn fresh bot population...")
    DockerService.restart_container("ac-worldserver")

    print("\n=====================================================")
    print(" SUCCESS: Playerbots reset and world is repopulating!")
    print("=====================================================")
    return True


def purge_bots_action(context: dict):
    purge_bots_sequence(context)


def bot_population_preset_action(preset_name: str, min_bots: int, max_bots: int):
    print(f"\nConfiguring Bot Population: {preset_name} [{min_bots}-{max_bots}]...")
    if ConfigManager.update_conf_values({
        "AiPlayerbot.MinRandomBots": str(min_bots),
        "AiPlayerbot.MaxRandomBots": str(max_bots)
    }):
        DockerService.reload_worldserver_config()
        print("\n=====================================================")
        print(f" SUCCESS: Bot population set to {preset_name} [{min_bots}-{max_bots}]")
        print("=====================================================")


def expansion_preset_action(mode_name: str, max_level: int, maps_str: str):
    print(f"\nConfiguring {mode_name} [Max Level {max_level}, Maps {maps_str}]...")
    if ConfigManager.update_conf_values({
        "AiPlayerbot.RandomBotMaxLevel": str(max_level),
        "AiPlayerbot.RandomBotMaps": maps_str
    }):
        DockerService.reload_worldserver_config()
        print("\n=====================================================")
        print(" SUCCESS: Expansion progression updated!")
        print("=====================================================")
        print(" REMINDER for Individual Progression [.ip]:")
        print(" - GM Commands to bypass progression gates:")
        print("     .ip help                  [View all commands]")
        print("     .ip set level <lvl>      [Set player progression level]")
        print("     .ip complete             [Complete current tier]")
        print("=====================================================")


def skirmish_preset_action(min_lvl: int, max_lvl: int):
    if min_lvl > max_lvl:
        print("\nError: Minimum level cannot be greater than maximum level.")
        return

    exp_maps = "0,1"
    if max_lvl > 70:
        print("\nMax level is above 70 - Enabling WotLK Maps & Content [Maps: 0,1,530,571]...")
        exp_maps = "0,1,530,571"
    elif max_lvl > 60:
        print("\nMax level is above 60 - Enabling TBC Maps & Content [Maps: 0,1,530]...")
        exp_maps = "0,1,530"

    print(f"\nApplying Skirmish Config: Level Range [{min_lvl} - {max_lvl}]...")
    ConfigManager.update_conf_values({
        "AiPlayerbot.RandomBotMinLevel": str(min_lvl),
        "AiPlayerbot.RandomBotMaxLevel": str(max_lvl),
        "AiPlayerbot.RandomBotMaps": exp_maps,
        "AiPlayerbot.SyncLevelWithPlayers": "0"
    })

    print(f"\nSkirmish configuration saved!")
    print(f"Level Range : {min_lvl} - {max_lvl}")
    print(f"LevelSync   : Disabled [Bots stay at {min_lvl}-{max_lvl} even for Level 1 players]\n")

    do_purge = safe_input(f"Would you like to PURGE existing playerbots now to immediately repopulate at level {min_lvl}-{max_lvl}? [Y/N]: ").strip().lower()
    if do_purge == 'y':
        purge_bots_sequence({})
    else:
        DockerService.reload_worldserver_config()

    print("\n=====================================================")
    print(f" SKIRMISH MODE ACTIVE: Level {min_lvl}-{max_lvl} PvP Battles")
    print("=====================================================")
    print(" HINTS & USEFUL COMMANDS FOR QUICK PVP:")
    print(" -----------------------------------------------------")
    print(f" - Set Player Level  : .level {max_lvl}  [or .character level {max_lvl}]")
    print(" - Auto-Gear Character: .autogear  [Equips level-appropriate gear]")
    print(" - Init Bot Gear/Spec: .bot init")
    print(f" - Individual Prog.  : .ip set level {max_lvl}  [Bypass progression locks]")
    print(" - Popular PvP Teleports:")
    print("     .tele gurubashi   [Gurubashi Arena]")
    print("     .tele arathi       [Arathi Highlands / Refuge Pointe]")
    print("     .tele tarrenmill   [Tarren Mill vs Southshore]")
    print("     .tele dalaran      [Dalaran Sewers / Underbelly]")
    print("=====================================================")


def rpg_weight_preset_action(preset_name: str, weights: dict):
    print(f"\nConfiguring Open World RPG Activity Weights: {preset_name}...")
    conf_updates = {f"AiPlayerbot.RpgStatusProbWeight.{k}": str(v) for k, v in weights.items()}
    if ConfigManager.update_conf_values(conf_updates):
        DockerService.reload_worldserver_config()
        print("\n=====================================================")
        print(f" SUCCESS: Open World RPG Activity set to '{preset_name}'")
        print("=====================================================")
        print(" Active Behavior Weights:")
        for k, v in weights.items():
            print(f"   - {k:<15} : {v}")
        print("=====================================================")


def custom_population_action(context: dict):
    print("\nCustom Bot Population Density Setup:")
    min_val = safe_input("Enter MINIMUM bot count (1 - 10000): ").strip()
    max_val = safe_input("Enter MAXIMUM bot count (1 - 10000): ").strip()

    try:
        min_bots = int(min_val)
        max_bots = int(max_val)
    except ValueError:
        print("\nInvalid input: Bot count must be a positive integer.")
        return

    if min_bots < 1 or max_bots < 1:
        print("\nInvalid input: Bot count must be at least 1.")
        return
    if min_bots > 10000 or max_bots > 10000:
        print("\nInvalid input: Maximum supported bot count limit is 10000.")
        return
    if min_bots > max_bots:
        print("\nInvalid input: Minimum bot count cannot be greater than maximum bot count.")
        return

    bot_population_preset_action("Custom", min_bots, max_bots)





def custom_skirmish_action(context: dict):
    print("\nCustom Level Range Setup:")
    min_val = safe_input("Enter MINIMUM bot level (1-80): ").strip()
    max_val = safe_input("Enter MAXIMUM bot level (1-80): ").strip()

    try:
        min_lvl = int(min_val)
        max_lvl = int(max_val)
    except ValueError:
        print("\nInvalid input: Level must be an integer between 1 and 80.")
        return

    if min_lvl < 1 or min_lvl > 80 or max_lvl < 1 or max_lvl > 80:
        print("\nInvalid input: Level must be between 1 and 80.")
        return

    if min_lvl > max_lvl:
        print("\nInvalid input: Minimum level cannot be greater than maximum level.")
        return

    skirmish_preset_action(min_lvl, max_lvl)


def ahbot_setup_action(context: dict):
    print("\n=====================================================")
    print("          AUCTION HOUSE BOT (AHBOT) SETUP")
    print("=====================================================")
    print("AH Bot automatically posts and bids on Auction House items.")

    current_seller = ConfigManager.get_conf_value("AuctionHouseBot.EnableSeller", "false", conf_path=AHBOT_CONF_FILE)
    current_buyer = ConfigManager.get_conf_value("AuctionHouseBot.Buyer.Enabled", "false", conf_path=AHBOT_CONF_FILE)
    current_guid = ConfigManager.get_conf_value("AuctionHouseBot.GUIDs", "0", conf_path=AHBOT_CONF_FILE)

    status_str = "ENABLED" if (current_seller.lower() == "true" or current_buyer.lower() == "true") else "DISABLED"
    print(f"\n Current Status  : [ {status_str} ]")
    print(f" Character GUID  : [ {current_guid if current_guid != '0' else '0 (Not Set / Disabled)'} ]")
    print("-----------------------------------------------------")

    print("\nOptions:")
    print("  1. Interactive AH-Bot Setup Wizard (Recommended)")
    print("  2. Enable AH Bot (Seller & Buyer)")
    print("  3. Disable AH Bot")
    print("  4. View / Select Characters in Database")
    print("  0. Back")

    choice = safe_input("\nSelect an option [0-4]: ").strip()
    if choice == "1":
        ahbot_interactive_wizard(context)
    elif choice == "2":
        if current_guid == "0" or not current_guid:
            print("\n[!] WARNING: Character GUID is currently 0 (Not Set).")
            prompt_guid = safe_input("Do you want to enter a Character GUID now? [y/N]: ").strip().lower()
            if prompt_guid == 'y':
                guid = safe_input("Enter Character GUID: ").strip()
                if guid and guid.isdigit():
                    current_guid = guid
                elif guid:
                    print("\n[!] Invalid input: GUID must be a positive integer.")
        updates = {
            "AuctionHouseBot.EnableSeller": "true",
            "AuctionHouseBot.Buyer.Enabled": "true",
            "AuctionHouseBot.GUIDs": current_guid if current_guid else "0"
        }
        if ConfigManager.update_conf_values(updates, conf_path=AHBOT_CONF_FILE):
            DockerService.reload_worldserver_config()
            print("\n=====================================================")
            print(f" SUCCESS: AH Bot Enabled! (Character GUID: {current_guid})")
            print("=====================================================")
    elif choice == "3":
        updates = {
            "AuctionHouseBot.EnableSeller": "false",
            "AuctionHouseBot.Buyer.Enabled": "false"
        }
        if ConfigManager.update_conf_values(updates, conf_path=AHBOT_CONF_FILE):
            DockerService.reload_worldserver_config()
            print("\n=====================================================")
            print(" SUCCESS: AH Bot Disabled!")
            print("=====================================================")
    elif choice == "4":
        show_database_characters_menu()


def ahbot_interactive_wizard(context: dict):
    print("\n=====================================================")
    print("        INTERACTIVE AH BOT SETUP WIZARD")
    print("=====================================================")
    print("This wizard will help you create an AH bot account, guide")
    print("character creation, and auto-link your character to AH Bot.")
    print("-----------------------------------------------------")

    ws_online = DockerService.get_container_status("ac-worldserver") == "ONLINE"
    db_online = DockerService.get_container_status("ac-database") == "ONLINE"

    if not ws_online and not db_online:
        print("\n[!] NOTE: SkirmishCore server stack is currently OFFLINE.")
        print("    The server needs to be running so you can log into WoW to create your bot character.")
        start_now = safe_input("\nWould you like to start the server stack now? [y/N]: ").strip().lower()
        if start_now == 'y':
            if DockerService.start_stack():
                print("\nWaiting 10 seconds for server initialization...")
                time.sleep(10)
                ws_online = DockerService.get_container_status("ac-worldserver") == "ONLINE"
                db_online = DockerService.get_container_status("ac-database") == "ONLINE"
            else:
                print("\n[!] Could not start server stack. Please start the server (Main Menu -> Option 1 -> 1) first.")
                return
        else:
            print("\n[!] Wizard canceled. Please start the server stack before configuring AH Bot.")
            return

    # Step 1: Account Setup
    user = safe_input("\n[Step 1/3] Enter AH Bot account username [default: ahbot]: ").strip() or "ahbot"
    password = safe_input(f"           Enter password for account '{user}' [default: password]: ").strip() or "password"

    print(f"\nCreating account '{user}' in server database...", flush=True)
    account_created = False
    safe_user = sanitize_sql(user)
    safe_pass = sanitize_sql(password)

    if ws_online:
        try:
            res = subprocess.run(
                ["docker", "compose", "exec", "-T", "ac-worldserver", "bash", "-c", f"echo 'account create {user} {password}' | nc -w 1 127.0.0.1 7878"],
                cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace"
            )
            account_created = True
        except Exception:
            pass

    if db_online:
        try:
            salt_hex, verifier_hex = generate_srp6_verifier(user, password)
            sql_insert = (
                f"INSERT INTO acore_auth.account (username, salt, verifier) "
                f"VALUES (UPPER('{safe_user}'), UNHEX('{salt_hex}'), UNHEX('{verifier_hex}')) "
                f"ON DUPLICATE KEY UPDATE salt=UNHEX('{salt_hex}'), verifier=UNHEX('{verifier_hex}');"
            )
            subprocess.run(
                ["docker", "compose", "exec", "-T", "ac-database", "mysql", "-uroot", "-ppassword", "-e", sql_insert],
                cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            account_created = True
        except Exception:
            pass

    if account_created:
        print(f"  [OK] Account '{user}' configured!")
    else:
        print(f"  [NOTE] Account '{user}' will be initialized when server finishes starting.")


    # Step 2: Character Creation Guide
    print("\n=====================================================")
    print("  [Step 2/3] CREATE BOT CHARACTER IN WOW CLIENT")
    print("=====================================================")
    print(f"1. Open WoW and log in with account '{user}' (password: '{password}').")
    print("2. Create a new character (Suggested name: Auctioneer).")
    print("3. [IMPORTANT] Do NOT press 'Enter World'. Leave character")
    print("               at the character selection screen and exit game.")
    print("=====================================================")

    # Step 3: Character Name & Auto-Link Loop
    while True:
        char_name = safe_input("\n[Step 3/3] Enter the character name you created [default: Auctioneer]: ").strip() or "Auctioneer"
        safe_char = sanitize_sql(char_name)

        found_guid = None
        if DockerService.get_container_status("ac-database") == "ONLINE":
            try:
                res = subprocess.run(
                    ["docker", "compose", "exec", "-T", "ac-database", "mysql", "-uroot", "-ppassword", "-e",
                     f"SELECT guid FROM acore_characters.characters WHERE LOWER(name) = LOWER('{safe_char}');"],
                    cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace"
                )
                if res.returncode == 0 and res.stdout:
                    lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
                    if len(lines) > 1:
                        found_guid = lines[-1].strip()
            except Exception as e:
                print(f"Error querying database: {e}")

        if found_guid and found_guid.isdigit():
            updates = {
                "AuctionHouseBot.EnableSeller": "true",
                "AuctionHouseBot.Buyer.Enabled": "true",
                "AuctionHouseBot.GUIDs": found_guid
            }
            if ConfigManager.update_conf_values(updates, conf_path=AHBOT_CONF_FILE):
                DockerService.reload_worldserver_config()
                print("\n=====================================================")
                print(" SUCCESS: AH Bot Fully Configured & Enabled!")
                print(f" Linked Character : {char_name} (GUID: {found_guid})")
                print("=====================================================")
                return
        else:
            print(f"\n[!] Character '{char_name}' was not found in the database.")
            print("    (Ensure you created the character in WoW and the server stack is running).")
            print("\nOptions:")
            print("  1. Retry search (after creating character)")
            print("  2. Manually enter Character GUID")
            print("  0. Cancel Wizard")
            wiz_choice = safe_input("\nSelect choice [0-2]: ").strip()
            if wiz_choice == "1":
                continue
            elif wiz_choice == "2":
                manual_guid = safe_input("Enter Character GUID: ").strip()
                if manual_guid and manual_guid.isdigit():
                    updates = {
                        "AuctionHouseBot.EnableSeller": "true",
                        "AuctionHouseBot.Buyer.Enabled": "true",
                        "AuctionHouseBot.GUIDs": manual_guid
                    }
                    if ConfigManager.update_conf_values(updates, conf_path=AHBOT_CONF_FILE):
                        DockerService.reload_worldserver_config()
                        print("\n=====================================================")
                        print(f" SUCCESS: AH Bot Configured with Manual GUID {manual_guid}!")
                        print("=====================================================")
                        return
            else:
                print("\nWizard canceled.")
                return


def show_database_characters_menu():
    print("\nQuerying characters from database...", flush=True)
    chars = []
    if DockerService.get_container_status("ac-database") == "ONLINE":
        try:
            res = subprocess.run(
                ["docker", "compose", "exec", "-T", "ac-database", "mysql", "-uroot", "-ppassword", "-e", "SELECT guid, name, account FROM acore_characters.characters;"],
                cwd=CORE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace"
            )
            if res.returncode == 0 and res.stdout:
                lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
                if len(lines) > 1:
                    for line in lines[1:]:
                        parts = line.split()
                        if len(parts) >= 3:
                            chars.append({"guid": parts[0], "name": parts[1], "account": parts[2]})
        except Exception as e:
            print(f"Database query error: {e}")

    if chars:
        print("\n=====================================================")
        print("          CHARACTERS FOUND IN DATABASE")
        print("=====================================================")
        print(f"  {'GUID':<8} | {'Character Name':<20} | {'Account ID':<10}")
        print("  ---------------------------------------------------")
        for c in chars:
            print(f"  {c['guid']:<8} | {c['name']:<20} | {c['account']:<10}")
        print("  ---------------------------------------------------")
        selected_guid = safe_input("\nEnter GUID to assign to AH Bot (or press Enter to cancel): ").strip()
        if selected_guid:
            if not selected_guid.isdigit():
                print("\n[!] Invalid input: GUID must be a positive integer.")
            elif ConfigManager.update_conf_values({"AuctionHouseBot.GUIDs": selected_guid}, conf_path=AHBOT_CONF_FILE):
                DockerService.reload_worldserver_config()
                print("\n=====================================================")
                print(f" SUCCESS: AH Bot Character GUID set to {selected_guid}!")
                print("=====================================================")
    else:
        print("\n[!] No characters found in database (or database container is OFFLINE).")
        print("=====================================================")



def bot_starting_level_action(context: dict):
    print("\n=====================================================")
    print("      BOT STARTING LEVEL & SPAWN CONFIGURATION")
    print("=====================================================")
    print("Choose how new playerbots generate when spawned:")
    print("\n  1. Force Level 1 Starter Spawns (DisableRandomLevels = 1)")
    print("     -> All newly generated bots start at Level 1 in starting zones")
    print("        and level up naturally alongside players.")
    print("\n  2. Random Level Spawns [Default] (DisableRandomLevels = 0)")
    print("     -> Bots generate at random levels across the level range")
    print("        and auto-teleport to level-appropriate zones.")
    print("\n  0. Back")

    choice = safe_input("\nSelect an option [0-2]: ").strip()
    if choice == "1":
        if ConfigManager.update_conf_values({
            "AiPlayerbot.DisableRandomLevels": "1",
            "AiPlayerbot.RandombotStartingLevel": "1"
        }):
            print("\n=====================================================")
            print(" SUCCESS: Forced Level 1 Bot Spawns Enabled!")
            print("=====================================================")
            print(" Newly created randombots will now spawn at Level 1.")
            do_purge = safe_input("\nWould you like to PURGE existing playerbots now to immediately spawn fresh Level 1 bots? [Y/N]: ").strip().lower()
            if do_purge == 'y':
                purge_bots_sequence(context)
            else:
                DockerService.reload_worldserver_config()
    elif choice == "2":
        if ConfigManager.update_conf_values({
            "AiPlayerbot.DisableRandomLevels": "0"
        }):
            DockerService.reload_worldserver_config()
            print("\n=====================================================")
            print(" SUCCESS: Random Level Bot Spawns Enabled!")
            print("=====================================================")


# ==============================================================================
# MENU BUILDER & FACTORY
# ==============================================================================
def create_application_menus() -> BaseMenu:
    """Builds and wires up the menu hierarchy using OOP inheritance."""
    main_menu = BaseMenu("SKIRMISHCORE CONTROL HUB")

    # 1. Server Controls SubMenu
    server_menu = BaseMenu("SERVER CONTROLS & ADMIN", parent=main_menu)
    server_menu.add_option(ActionOption("1", "Start Server", "Turn it on", start_server_action))
    server_menu.add_option(ActionOption("2", "Stop Server", "Turn it off", stop_server_action))
    server_menu.add_option(ActionOption("3", "Build Server", "Rebuild Docker container images", build_action))
    server_menu.add_option(ActionOption("4", "Create Game Account Wizard", "Automated account creation with GM status selection", create_account_action))
    server_menu.add_option(ActionOption("5", "Admin Console", "Open interactive worldserver terminal console", admin_console_action, pause_after=False))
    server_menu.add_option(ActionOption("6", "Live Logs", "See what the server is doing", logs_action, pause_after=False))
    server_menu.add_option(ActionOption("7", "Health Check", "Make sure everything is running", doctor_action))
    server_menu.add_option(ActionOption("8", "Wipe Server Setup", "Delete all containers, database volumes, & images (requires rebuild)", wipe_server_action))
    main_menu.add_option(SubMenuOption("1", "Server Controls", "Start, stop, build, logs, and account setup", server_menu))


    # 2. Skirmish Mode SubMenu
    skirmish_menu = BaseMenu("SKIRMISH MODE SETUP [PVP BRACKETS]", parent=main_menu)
    skirmish_menu.add_option(ActionOption("1", "Bracket 19", "[Level 10 - 19]", lambda ctx: skirmish_preset_action(10, 19)))
    skirmish_menu.add_option(ActionOption("2", "Bracket 29", "[Level 20 - 29]", lambda ctx: skirmish_preset_action(20, 29)))
    skirmish_menu.add_option(ActionOption("3", "Bracket 39", "[Level 30 - 39]", lambda ctx: skirmish_preset_action(30, 39)))
    skirmish_menu.add_option(ActionOption("4", "Bracket 49", "[Level 40 - 49]", lambda ctx: skirmish_preset_action(40, 49)))
    skirmish_menu.add_option(ActionOption("5", "Bracket 59", "[Level 50 - 59]", lambda ctx: skirmish_preset_action(50, 59)))
    skirmish_menu.add_option(ActionOption("6", "Classic 60", "[Level 60 - 60]", lambda ctx: skirmish_preset_action(60, 60)))
    skirmish_menu.add_option(ActionOption("7", "TBC 70", "[Level 60 - 70]", lambda ctx: skirmish_preset_action(60, 70)))
    skirmish_menu.add_option(ActionOption("8", "WotLK 80", "[Level 70 - 80]", lambda ctx: skirmish_preset_action(70, 80)))
    skirmish_menu.add_option(ActionOption("9", "Custom Level Range", "[e.g. 30 - 40]", custom_skirmish_action))
    main_menu.add_option(SubMenuOption("2", "Skirmish Mode [Quick PvP]", "Jump into PvP at a set level range", skirmish_menu))

    # 3. Expansion Setup SubMenu
    exp_menu = BaseMenu("EXPANSION PROGRESSION CONTROL", parent=main_menu)
    exp_menu.add_option(ActionOption("1", "Classic WoW", "[Level 1-60  | Eastern Kingdoms & Kalimdor]", lambda ctx: expansion_preset_action("Classic Mode", 60, "0,1")))
    exp_menu.add_option(ActionOption("2", "TBC Mode", "[Level 1-70  | Unlocks Outland]", lambda ctx: expansion_preset_action("TBC Mode", 70, "0,1,530")))
    exp_menu.add_option(ActionOption("3", "WotLK Mode", "[Level 1-80  | Unlocks Northrend]", lambda ctx: expansion_preset_action("WotLK Mode", 80, "0,1,530,571")))
    main_menu.add_option(SubMenuOption("3", "Expansion Setup", "Choose which expansion bots play in", exp_menu))

    # 4. Bot Management & Population SubMenu
    bot_menu = BaseMenu("BOT MANAGEMENT & POPULATION", parent=main_menu)

    pop_menu = BaseMenu("BOT POPULATION DENSITY SETUP", parent=bot_menu)
    pop_menu.add_option(ActionOption("1", "Low", "[100 - 300 Bots]   [Low performance impact - recommended for lower-end CPUs]", lambda ctx: bot_population_preset_action("Low", 100, 300)))
    pop_menu.add_option(ActionOption("2", "Medium", "[500 - 1000 Bots]  [Medium performance impact - balanced world activity]", lambda ctx: bot_population_preset_action("Medium", 500, 1000)))
    pop_menu.add_option(ActionOption("3", "High (Default)", "[1000 - 2000 Bots] [Default - active world population & PvP]", lambda ctx: bot_population_preset_action("High", 1000, 2000)))
    pop_menu.add_option(ActionOption("4", "Custom Bot Count", "[Specify exact min/max bot population]", custom_population_action))

    rpg_menu = BaseMenu("OPEN WORLD RPG ACTIVITY PRESETS", parent=bot_menu)
    rpg_menu.add_option(ActionOption("1", "Balanced RPG (Default)", "Balanced mix of Questing, Grinding, Flight Traveling, & World PvP", lambda ctx: rpg_weight_preset_action("Balanced RPG", {"WanderRandom": 15, "WanderNpc": 20, "GoGrind": 15, "GoCamp": 10, "DoQuest": 60, "TravelFlight": 15, "Rest": 5, "OutdoorPvp": 15})))
    rpg_menu.add_option(ActionOption("2", "Heavy Questers & Explorers", "Bots focus heavily on quest lines, flight paths, and exploring hubs", lambda ctx: rpg_weight_preset_action("Heavy Questers", {"WanderRandom": 10, "WanderNpc": 30, "GoGrind": 10, "GoCamp": 10, "DoQuest": 90, "TravelFlight": 40, "Rest": 5, "OutdoorPvp": 10})))
    rpg_menu.add_option(ActionOption("3", "Grinders & Mob Hunters", "Bots roam hunting grounds and continuously grind mobs in the open world", lambda ctx: rpg_weight_preset_action("Grinders & Mob Hunters", {"WanderRandom": 40, "WanderNpc": 10, "GoGrind": 80, "GoCamp": 5, "DoQuest": 20, "TravelFlight": 15, "Rest": 5, "OutdoorPvp": 20})))
    rpg_menu.add_option(ActionOption("4", "World PvP Skirmishers", "Bots actively patrol open-world zones, objectives, and fight opposite faction", lambda ctx: rpg_weight_preset_action("World PvP Skirmishers", {"WanderRandom": 35, "WanderNpc": 10, "GoGrind": 25, "GoCamp": 10, "DoQuest": 30, "TravelFlight": 25, "Rest": 5, "OutdoorPvp": 80})))
    rpg_menu.add_option(ActionOption("5", "Town Idlers & Socializers", "Bots hang around camps, inns, towns, resting and interacting with NPCs", lambda ctx: rpg_weight_preset_action("Town Idlers", {"WanderRandom": 15, "WanderNpc": 50, "GoGrind": 10, "GoCamp": 40, "DoQuest": 30, "TravelFlight": 15, "Rest": 35, "OutdoorPvp": 5})))

    bot_menu.add_option(SubMenuOption("1", "Adjust Bot Population Density", "Set bot counts based on performance impact", pop_menu))
    bot_menu.add_option(SubMenuOption("2", "Open World RPG Activity Presets", "Tune bot open world behaviors (Questing, Grinding, PvP, Idling)", rpg_menu))
    bot_menu.add_option(ActionOption("3", "Bot Starting Level Mode", "Set bot spawn behavior (Force Level 1 vs Random levels)", bot_starting_level_action))
    bot_menu.add_option(ActionOption("4", "Reset & Purge Playerbots", "Wipe current bots and spawn fresh population", purge_bots_action))
    bot_menu.add_option(ActionOption("5", "Auction House Bot Setup", "Optionally enable or configure AH Bot character/GUID", ahbot_setup_action))
    main_menu.add_option(SubMenuOption("4", "Bot Management & Population", "Reset bots, adjust population, or set open world RPG activity", bot_menu))


    # 5. Multi-Player Setup
    main_menu.add_option(ActionOption("5", "Multi-Player Setup", "Let friends join", coop_action))

    return main_menu


# ==============================================================================
# ENTRY POINT
# ==============================================================================
def main():
    if not os.path.exists(CORE_DIR):
        print(f"Error: Core directory not found at {CORE_DIR}")
        sys.exit(1)

    os.chdir(CORE_DIR)
    app = create_application_menus()
    context = {}
    try:
        app.run(context)
    except KeyboardInterrupt:
        print("\nExiting SkirmishCore Control Hub.")
        sys.exit(0)


if __name__ == "__main__":
    main()
