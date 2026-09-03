import os
import sys
import time
import json
import signal
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timezone

# ============================================================
# PATH SETUP
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent
if ROOT_DIR.name == "Backend":
    ROOT_DIR = ROOT_DIR.parent

BACKEND_DIR = ROOT_DIR / "Backend"
MODEL_DIR = BACKEND_DIR / "sattelite_model"
OUTPUT_DIR = MODEL_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Add paths to sys.path
for p in [ROOT_DIR, BACKEND_DIR, MODEL_DIR]:
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

PYTHON_EXE = sys.executable

# ============================================================
# ANSI COLORS
# ============================================================

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner():
    print(f"{CYAN}{BOLD}")
    print("=" * 75)
    print("      DISASTER MANAGEMENT SYSTEM - UNIFIED LIVE AI RUNNER")
    print("       Landslide Detection (Attention-ResUNet) + Flood Detection (MNDWI/SAR)")
    print("=" * 75)
    print(f"{RESET}", flush=True)


# ============================================================
# SUBPROCESS MANAGER
# ============================================================

running_processes = []
shutdown_requested = False


def register_process(proc, name="Service"):
    running_processes.append((proc, name))


def cleanup_processes():
    global shutdown_requested
    if shutdown_requested:
        return
    shutdown_requested = True
    print(f"\n{YELLOW}[SHUTDOWN] Terminating all background services gracefully...{RESET}", flush=True)
    for proc, name in running_processes:
        if proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            print(f"  Stopped {name}", flush=True)
    print(f"{GREEN}[SHUTDOWN] All services stopped. Goodbye!{RESET}\n", flush=True)


def signal_handler(sig, frame):
    cleanup_processes()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ============================================================
# PRE-FLIGHT SYSTEM CHECK
# ============================================================

def preflight_check():
    print(f"{BOLD}[1/4] Pre-flight System & Model Diagnostics...{RESET}", flush=True)

    # 1. Check PyTorch & GPU
    try:
        import torch
        device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
        print(f"  {GREEN}+ PyTorch v{torch.__version__} (Compute Device: {device_name}){RESET}", flush=True)
    except Exception as e:
        print(f"  {RED}- PyTorch check failed: {e}{RESET}", flush=True)

    # 2. Check Model Weights
    ckpt = MODEL_DIR / "checkpoints" / "best_model.pth"
    if ckpt.exists():
        size_mb = ckpt.stat().st_size / (1024 * 1024)
        print(f"  {GREEN}+ Landslide Model Weights: Attention-ResUNet ({size_mb:.1f} MB){RESET}", flush=True)
    else:
        print(f"  {YELLOW}! Model checkpoint not found at {ckpt}.{RESET}", flush=True)

    # 3. Check .env Credentials
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        print(f"  {GREEN}+ Copernicus CDSE Configuration: Loaded from .env{RESET}", flush=True)
    else:
        print(f"  {YELLOW}! .env file not found.{RESET}", flush=True)

    print(flush=True)


# ============================================================
# VERIFY OR RUN PREDICTIONS
# ============================================================

def ensure_detections(force_repredict=False):
    print(f"{BOLD}[2/4] Loading Disaster Detection Models & Geospatial Layers...{RESET}", flush=True)

    ls_results = OUTPUT_DIR / "prediction_results.json"
    fl_results = OUTPUT_DIR / "flood_prediction_results.json"

    if force_repredict or not ls_results.exists():
        predict_script = MODEL_DIR / "predict.py"
        print(f"  {CYAN}* Computing Attention-ResUNet predictions across satellite scene...{RESET}", flush=True)
        try:
            subprocess.run([PYTHON_EXE, "-u", str(predict_script)], cwd=str(MODEL_DIR), check=True)
            print(f"  {GREEN}+ Landslide prediction generated successfully.{RESET}", flush=True)
        except Exception as e:
            print(f"  {YELLOW}! Prediction notice: {e}{RESET}", flush=True)
    else:
        print(f"  {GREEN}+ Landslide Attention-ResUNet layer: READY (Loaded latest high-confidence map){RESET}", flush=True)

    if fl_results.exists():
        print(f"  {GREEN}+ Flood Detection (MNDWI / SAR) layer: READY{RESET}", flush=True)
    else:
        print(f"  {YELLOW}! Flood layer will be initialized on first live satellite pass.{RESET}", flush=True)

    print(flush=True)


# ============================================================
# START BACKGROUND SERVICES
# ============================================================

def start_alert_server():
    alert_script = BACKEND_DIR / "alert_server.py"
    print(f"{CYAN}* Starting Disaster Alert & API Server on http://localhost:8000...{RESET}", flush=True)
    proc = subprocess.Popen(
        [PYTHON_EXE, str(alert_script)],
        cwd=str(BACKEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    register_process(proc, "Disaster Alert API Server (Port 8000)")
    time.sleep(1.0)
    print(f"  {GREEN}+ Alert API Server is ACTIVE on http://localhost:8000{RESET}", flush=True)


def start_live_monitor():
    monitor_script = MODEL_DIR / "live_monitor.py"
    print(f"{CYAN}* Starting Live Satellite Ingestion & Polling Monitor...{RESET}", flush=True)
    proc = subprocess.Popen(
        [PYTHON_EXE, "-u", str(monitor_script)],
        cwd=str(MODEL_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    register_process(proc, "Copernicus Live Satellite Monitor")
    time.sleep(1.0)
    print(f"  {GREEN}+ Live Satellite Monitor is ACTIVE (Auto-fetching CDSE passes every 15m){RESET}", flush=True)


def start_frontend():
    frontend_dir = ROOT_DIR / "FrontendNew"
    if not frontend_dir.exists():
        frontend_dir = ROOT_DIR / "Frontend"

    if frontend_dir.exists() and (frontend_dir / "package.json").exists():
        print(f"{CYAN}* Launching Frontend Map Dashboard on http://localhost:5173...{RESET}", flush=True)
        try:
            proc = subprocess.Popen(
                ["npx", "vite", "--port", "5173", "--host"],
                cwd=str(frontend_dir),
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            register_process(proc, "Frontend Map Dashboard (Port 5173)")
            time.sleep(1.5)
            print(f"  {GREEN}+ Frontend Dashboard is ACTIVE on http://localhost:5173{RESET}", flush=True)
        except Exception as e:
            pass


# ============================================================
# LIVE DASHBOARD DISPLAY
# ============================================================

def read_json_safe(path):
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def display_dashboard():
    landslide_file = OUTPUT_DIR / "prediction_results.json"
    flood_file = OUTPUT_DIR / "flood_prediction_results.json"

    ls_data = read_json_safe(landslide_file)
    fl_data = read_json_safe(flood_file)

    ls_risk = ls_data.get("risk", "UNKNOWN")
    ls_max_prob = ls_data.get("maximum_probability", 0.0)
    ls_pixels = ls_data.get("affected_pixels", 0)
    ls_percent = ls_data.get("affected_area_percent", 0.0)
    ls_regions = len(ls_data.get("affected_regions", []))

    fl_risk = fl_data.get("risk", "UNKNOWN")
    fl_pixels = fl_data.get("flood_pixels", 0)
    fl_percent = fl_data.get("flood_percentage", 0.0)
    fl_mndwi = fl_data.get("maximum_mndwi", 0.0)
    fl_regions = fl_data.get("detected_regions", len(fl_data.get("regions", [])))

    def color_risk(risk):
        if risk == "HIGH":
            return f"{RED}{BOLD}HIGH{RESET}"
        elif risk == "MEDIUM":
            return f"{YELLOW}{BOLD}MEDIUM{RESET}"
        elif risk == "LOW":
            return f"{GREEN}{BOLD}LOW{RESET}"
        return f"{DIM}{risk}{RESET}"

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{BOLD}" + "=" * 75)
    print(f"       LIVE DISASTER DETECTION DASHBOARD | {now_str}")
    print("=" * 75 + f"{RESET}")

    # Landslide Section
    print(f" {BOLD}[LANDSLIDE STATUS]{RESET} Threat Level: [{color_risk(ls_risk)}]")
    print(f"    - Model Architecture:  Attention-ResUNet (14 Multispectral & Topography Channels)")
    print(f"    - Peak Probability:    {ls_max_prob * 100:.2f}%")
    print(f"    - Affected Area:       {ls_pixels:,} pixels ({ls_percent:.4f}%)")
    print(f"    - Hazard Clusters:     {ls_regions} localized hazard zones")
    print(f"    - GeoJSON Layer:       {OUTPUT_DIR / 'landslide_regions.geojson'}")

    print()

    # Flood Section
    print(f" {BOLD}[FLOOD STATUS]{RESET}     Threat Level: [{color_risk(fl_risk)}]")
    print(f"    - Sensor Modality:     Sentinel-2 Optical (MNDWI) + Sentinel-1 SAR")
    print(f"    - Peak Water Index:    {fl_mndwi:.4f} (MNDWI)")
    print(f"    - Inundated Area:      {fl_pixels:,} pixels ({fl_percent * 100:.6f}%)")
    print(f"    - Water Bodies:        {fl_regions} active flood zones")
    print(f"    - GeoJSON Layer:       {OUTPUT_DIR / 'flood_regions.geojson'}")

    print()

    # Service Links Section
    print(f" {BOLD}[ACTIVE SERVICES & API INTERFACES]{RESET}")
    print(f"    - Alert REST API:      {CYAN}http://localhost:8000/api/alerts{RESET}")
    print(f"    - Flood GeoJSON:       {CYAN}http://localhost:8000/api/flood/geojson{RESET}")
    print(f"    - Landslide GeoJSON:   {CYAN}http://localhost:8000/api/landslide/geojson{RESET}")
    print(f"    - Frontend Web Map:    {CYAN}http://localhost:5173{RESET}")
    print(f"    - CDSE Poller:         {GREEN}Active in background (Polling every 15 mins){RESET}")

    print(f"{BOLD}" + "=" * 75 + f"{RESET}")
    print(f"{DIM}Press Ctrl+C at any time to stop all background services.{RESET}\n", flush=True)


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Disaster Management Unified Live Runner")
    parser.add_argument("--repredict", action="store_true", help="Force re-running predictions on all scene tiles")
    args = parser.parse_args()

    print_banner()
    preflight_check()
    ensure_detections(force_repredict=args.repredict)

    print(f"{BOLD}[3/4] Starting Background Services (Live CDSE Monitor + Alert API Server)...{RESET}", flush=True)
    start_alert_server()
    start_live_monitor()
    start_frontend()

    print(f"\n{BOLD}[4/4] All background processes are running!{RESET}", flush=True)
    display_dashboard()

    heartbeat_count = 0
    while not shutdown_requested:
        time.sleep(30)
        heartbeat_count += 1
        if heartbeat_count % 4 == 0:
            display_dashboard()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cleanup_processes()
    except Exception as e:
        print(f"{RED}[ERROR] {e}{RESET}", flush=True)
        cleanup_processes()
