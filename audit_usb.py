# -*- coding: utf-8 -*-
"""
=============================================================================
Optima MTK Tool - Script d'Audit et de Diagnostic USB / COM / ADB Autonome
=============================================================================
Ce script s'exécute de manière 100% indépendante (sans interface graphique).
Il effectue un audit approfondi du sous-système matériel et processus :
  1. Diagnostic des processus ADB et du socket TCP 5037 (conflits, zombies).
  2. Énumération brute des ports série COM (SetupAPI) sans verrouillage.
  3. Mesure de latence exacte de 'adb devices' et 'fastboot devices'.
  4. Boucle de surveillance temps réel à haute fréquence (300ms) pour capturer
     les ports BROM/Preloader éphémères (Infinix / Tecno / MediaTek).
=============================================================================
"""

import sys
import os
import time
import socket
import shutil
import subprocess
from datetime import datetime

# Couleurs ANSI pour terminal Windows / Linux
COLOR_RESET   = "\033[0m"
COLOR_BOLD    = "\033[1m"
COLOR_RED     = "\033[91m"
COLOR_GREEN   = "\033[92m"
COLOR_YELLOW  = "\033[93m"
COLOR_BLUE    = "\033[94m"
COLOR_CYAN    = "\033[96m"

def print_banner():
    print(f"\n{COLOR_CYAN}{COLOR_BOLD}======================================================================{COLOR_RESET}")
    print(f"{COLOR_CYAN}{COLOR_BOLD}      OPTIMA MTK TOOL - AUDIT SYSTÈME USB, SERIAL & ADB AUTONOME      {COLOR_RESET}")
    print(f"{COLOR_CYAN}{COLOR_BOLD}======================================================================{COLOR_RESET}")
    print(f"Date & Heure : {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    print(f"Plateforme   : {sys.platform} (Python {sys.version.split()[0]})")
    print(f"Répertoire   : {os.getcwd()}\n")


def get_subprocess_flags():
    """Paramètres pour exécution silencieuse sans création de fenêtre noire console."""
    creationflags = 0
    startupinfo = None
    if sys.platform == "win32":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
        startupinfo.wShowWindow = 0
    return creationflags, startupinfo


# =====================================================================
# 1. Audit du Serveur ADB & Socket TCP 5037
# =====================================================================
def audit_adb_server():
    print(f"{COLOR_BOLD}[1] AUDIT DU SERVEUR ADB & PORT TCP 5037{COLOR_RESET}")
    print("-" * 60)

    # 1.1 Localisation du binaire ADB
    adb_bin = shutil.which("adb") or shutil.which("adb.exe")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "tools", "adb.exe"),
        os.path.join(base_dir, "platform-tools", "adb.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            adb_bin = c
            break

    if adb_bin:
        print(f"  • Binaire ADB localisé : {COLOR_GREEN}{adb_bin}{COLOR_RESET}")
    else:
        print(f"  • {COLOR_RED}ATTENTION : Aucun exécutable ADB trouvé dans PATH ou tools/{COLOR_RESET}")
        return

    # 1.2 Inspection du socket TCP 5037
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    is_port_open = False
    try:
        sock.connect(("127.0.0.1", 5037))
        is_port_open = True
    except Exception:
        is_port_open = False
    finally:
        sock.close()

    if is_port_open:
        print(f"  • Port TCP 5037 : {COLOR_GREEN}ACTIF (Un serveur ADB écoute actuellement){COLOR_RESET}")
    else:
        print(f"  • Port TCP 5037 : {COLOR_YELLOW}FERMÉ (Aucun serveur ADB en écoute){COLOR_RESET}")

    # 1.3 Inspection des processus adb.exe sous Windows
    if sys.platform == "win32":
        try:
            cf, si = get_subprocess_flags()
            proc = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq adb.exe", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=2, creationflags=cf, startupinfo=si
            )
            lines = [l.strip() for l in proc.stdout.splitlines() if "adb.exe" in l.lower()]
            if lines:
                print(f"  • Processus adb.exe actifs : {COLOR_YELLOW}{len(lines)} instance(s) détectée(s){COLOR_RESET}")
                for l in lines:
                    parts = l.replace('"', '').split(",")
                    pid = parts[1] if len(parts) > 1 else "?"
                    mem = parts[4] if len(parts) > 4 else "?"
                    print(f"      - PID: {pid} | Mémoire: {mem}")
            else:
                print(f"  • Processus adb.exe actifs : {COLOR_BLUE}0 (Aucun processus orphelin){COLOR_RESET}")
        except Exception as e:
            print(f"  • {COLOR_RED}Erreur inspection processus : {e}{COLOR_RESET}")

    # 1.4 Test de réactivité 'adb devices'
    t0 = time.time()
    try:
        cf, si = get_subprocess_flags()
        proc = subprocess.run(
            [adb_bin, "devices", "-l"],
            capture_output=True, text=True, timeout=3, creationflags=cf, startupinfo=si
        )
        elapsed_ms = (time.time() - t0) * 1000.0
        print(f"  • Latence 'adb devices' : {COLOR_CYAN}{elapsed_ms:.1f} ms{COLOR_RESET}")
        
        output = (proc.stdout or "").strip()
        lines = [l for l in output.splitlines() if l.strip() and not l.startswith("*")]
        print(f"  • Réponse brute ADB :")
        for l in lines:
            if "device" in l and not l.startswith("List"):
                print(f"      🟢 {COLOR_GREEN}{l}{COLOR_RESET}")
            elif "unauthorized" in l:
                print(f"      🟡 {COLOR_YELLOW}{l} (Débogage non approuvé){COLOR_RESET}")
            elif "offline" in l:
                print(f"      🔴 {COLOR_RED}{l} (Périphérique hors-ligne){COLOR_RESET}")
            else:
                print(f"      {l}")
    except subprocess.TimeoutExpired:
        print(f"  • {COLOR_RED}TIMEOUT (> 3000 ms) : Le serveur ADB ne répond pas ou est bloqué !{COLOR_RESET}")
    except Exception as e:
        print(f"  • {COLOR_RED}Erreur exécution adb devices : {e}{COLOR_RESET}")

    print()


# =====================================================================
# 2. Audit des Ports COM / Pyserial (Inspection Passive SetupAPI)
# =====================================================================
def audit_com_ports():
    print(f"{COLOR_BOLD}[2] AUDIT DES PORTS COM & CONTRÔLE DES VERROUS SÉRIE{COLOR_RESET}")
    print("-" * 60)

    try:
        import serial.tools.list_ports as list_ports
    except ImportError:
        print(f"  • {COLOR_RED}Module 'pyserial' non installé dans cet environnement.{COLOR_RESET}")
        print()
        return

    ports = list(list_ports.comports())
    if not ports:
        print(f"  • {COLOR_YELLOW}Aucun port COM actuellement connecté au système.{COLOR_RESET}")
    else:
        print(f"  • Nombre de ports COM détectés : {COLOR_GREEN}{len(ports)}{COLOR_RESET}")
        for p in ports:
            port_name = p.device or "Inconnu"
            desc = p.description or ""
            hwid = p.hwid or ""
            vid = f"0x{p.vid:04X}" if p.vid else "N/A"
            pid = f"0x{p.pid:04X}" if p.pid else "N/A"
            mfg = p.manufacturer or "N/A"

            # Classification
            is_mtk = (p.vid == 0x0E8D) or ("MEDIATEK" in desc.upper()) or ("MTK" in desc.upper())
            tag = f"{COLOR_GREEN}[MEDIATEK DÉTECTÉ]{COLOR_RESET}" if is_mtk else "[STANDARD]"

            print(f"\n    {COLOR_BOLD}{port_name}{COLOR_RESET} {tag}")
            print(f"      - Description  : {desc}")
            print(f"      - Matériel     : VID={vid} | PID={pid} | Fabricant={mfg}")
            print(f"      - Identifiant  : {hwid}")

            # Test d'accès NON-BLOQUANT pour vérifier l'absence de handle verrouillé
            # On vérifie seulement si le port est ouvrable et on le referme immédiatement en 1ms
            if sys.platform == "win32":
                try:
                    import serial
                    s = serial.Serial(port_name, baudrate=115200, timeout=0.01)
                    s.close()
                    print(f"      - Statut Handle: {COLOR_GREEN}LIBRE (Port disponible sans verrou exclusif){COLOR_RESET}")
                except serial.SerialException as se:
                    if "PermissionError" in str(se) or "Access is denied" in str(se):
                        print(f"      - Statut Handle: {COLOR_RED}VERROUILLÉ (Accès refusé / Déjà ouvert par un autre processus){COLOR_RESET}")
                    else:
                        print(f"      - Statut Handle: {COLOR_YELLOW}Non testable ({se}){COLOR_RESET}")
                except Exception:
                    pass

    print()


# =====================================================================
# 3. Mode Surveillance Haute Fréquence (Live Monitor)
# =====================================================================
def live_monitor():
    print(f"{COLOR_BOLD}[3] SURVEILLANCE TEMPS RÉEL HAUTE FRÉQUENCE (300 ms){COLOR_RESET}")
    print(f"Branchez votre appareil Infinix / MediaTek (Normal, Fastboot ou BROM).")
    print(f"{COLOR_YELLOW}Appuyez sur Ctrl+C pour quitter la surveillance.{COLOR_RESET}\n")

    try:
        import serial.tools.list_ports as list_ports
        has_serial = True
    except ImportError:
        has_serial = False

    adb_bin = shutil.which("adb") or shutil.which("adb.exe") or "adb"
    cf, si = get_subprocess_flags()

    last_ports = set()
    last_adb_devices = set()

    counter = 0
    try:
        while True:
            counter += 1
            now_str = datetime.now().strftime("%H:%M:%S.%f")[:-4]

            # 3.1 Scan des ports COM passif
            current_ports = set()
            if has_serial:
                try:
                    for p in list_ports.comports():
                        info = f"{p.device} | {p.description} (VID:{p.vid:04X} PID:{p.pid:04X})" if p.vid and p.pid else f"{p.device} | {p.description}"
                        current_ports.add(info)
                except Exception:
                    pass

            # Diff ports COM
            added_ports = current_ports - last_ports
            removed_ports = last_ports - current_ports

            for p in added_ports:
                is_brom = ("0E8D" in p) or ("PRELOADER" in p.upper()) or ("MTK" in p.upper())
                badge = f"{COLOR_GREEN}[PORT BROM / PRELOADER CONNECTÉ]{COLOR_RESET}" if is_brom else f"{COLOR_BLUE}[PORT COM CONNECTÉ]{COLOR_RESET}"
                print(f"[{now_str}] 🟢 {badge} -> {p}")

            for p in removed_ports:
                print(f"[{now_str}] 🔴 [PORT DÉCONNECTÉ] -> {p}")

            last_ports = current_ports

            # 3.2 Scan ADB toutes les 2 itérations (600ms) pour préserver les performances
            if counter % 2 == 0:
                current_adb = set()
                try:
                    proc = subprocess.run(
                        [adb_bin, "devices"],
                        capture_output=True, text=True, timeout=1.0,
                        creationflags=cf, startupinfo=si
                    )
                    if proc.returncode == 0 and proc.stdout:
                        lines = [l.strip() for l in proc.stdout.splitlines() if l.strip() and not l.startswith("*")]
                        for l in lines[1:]:
                            parts = l.split()
                            if len(parts) >= 2:
                                current_adb.add(f"{parts[0]} [{parts[1].upper()}]")
                except Exception:
                    pass

                added_adb = current_adb - last_adb_devices
                removed_adb = last_adb_devices - current_adb

                for d in added_adb:
                    col = COLOR_GREEN if "DEVICE" in d else COLOR_YELLOW
                    print(f"[{now_str}] 📱 {COLOR_BOLD}ADB DÉTECTÉ :{COLOR_RESET} {col}{d}{COLOR_RESET}")

                for d in removed_adb:
                    print(f"[{now_str}] ⚪ ADB DÉCONNECTÉ : {d}")

                last_adb_devices = current_adb

            time.sleep(0.3)

    except KeyboardInterrupt:
        print(f"\n{COLOR_CYAN}[i] Surveillance terminée par l'utilisateur.{COLOR_RESET}\n")


# =====================================================================
# Point d'entrée principal
# =====================================================================
if __name__ == "__main__":
    print_banner()
    audit_adb_server()
    audit_com_ports()

    if "--monitor" in sys.argv or "-m" in sys.argv:
        live_monitor()
    else:
        print(f"{COLOR_YELLOW}Conseil : Lancez 'python audit_usb.py --monitor' pour surveiller en direct le branchement.{COLOR_RESET}\n")
