from pathlib import Path
from datetime import datetime, timezone
import json
import time
import traceback
import subprocess
import sys


# ============================================================
# CONFIGURATION
# ============================================================

CHECK_INTERVAL_MINUTES = 15

BASE_DIR = Path(__file__).resolve().parent

BACKEND_DIR = BASE_DIR.parent

PRODUCTS_DIR = (
    BACKEND_DIR
    / "data"
    / "satellite"
    / "products"
)

OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
)

HISTORY_DIR = (
    OUTPUT_DIR
    / "history"
)

ALERTS_DIR = (
    OUTPUT_DIR
    / "alerts"
)

STATE_FILE = (
    OUTPUT_DIR
    / "monitor_state.json"
)

RESULT_FILE = (
    OUTPUT_DIR
    / "prediction_results.json"
)

TERRAIN_SCRIPT = (
    BASE_DIR
    / "build_terrain.py"
)

INPUT_SCRIPT = (
    BASE_DIR
    / "satellite_input.py"
)

PREDICT_SCRIPT = (
    BASE_DIR
    / "predict.py"
)

CHECK_SCRIPT = (
    BASE_DIR
    / "check_prediction.py"
)


# ============================================================
# DIRECTORIES
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

HISTORY_DIR.mkdir(
    parents=True,
    exist_ok=True
)

ALERTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# STATE
# ============================================================

def load_state():

    if not STATE_FILE.exists():

        return {

            "last_product":
                None,

            "last_check":
                None,

            "last_prediction":
                None

        }

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {

            "last_product":
                None,

            "last_check":
                None,

            "last_prediction":
                None

        }


def save_state(state):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            state,
            f,
            indent=4
        )


# ============================================================
# FIND SENTINEL PRODUCTS
# ============================================================

def find_products():

    if not PRODUCTS_DIR.exists():

        return []

    products = list(
        PRODUCTS_DIR.rglob(
            "*.SAFE"
        )
    )

    products = [
        p
        for p in products
        if p.is_dir()
    ]

    products.sort(
        key=lambda p:
        p.stat().st_mtime,
        reverse=True
    )

    return products


def get_latest_product():

    products = find_products()

    if not products:

        return None

    return products[0]


# ============================================================
# RUN SCRIPT
# ============================================================

def run_script(
    script_path,
    name
):

    print()
    print("=" * 70)
    print(
        f"RUNNING: {name}"
    )
    print("=" * 70)

    if not script_path.exists():

        raise FileNotFoundError(
            f"Script not found:\n"
            f"{script_path}"
        )

    result = subprocess.run(

        [
            sys.executable,
            str(script_path)
        ],

        cwd=str(
            BASE_DIR
        )

    )

    if result.returncode != 0:

        raise RuntimeError(

            f"{name} failed "
            f"with exit code "
            f"{result.returncode}"

        )

    print()
    print(
        f"{name} completed."
    )


# ============================================================
# READ RESULT
# ============================================================

def read_result():

    if not RESULT_FILE.exists():

        raise FileNotFoundError(
            "prediction_results.json "
            "was not created."
        )

    with open(
        RESULT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# SAVE HISTORY
# ============================================================

def save_history(
    result
):

    timestamp = datetime.now(
        timezone.utc
    )

    filename = (
        timestamp.strftime(
            "%Y%m%d_%H%M%S"
        )
        + ".json"
    )

    path = (
        HISTORY_DIR
        / filename
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            indent=4
        )

    return path


# ============================================================
# SAVE ALERT
# ============================================================

def save_alert(
    result
):

    if not result.get(
        "alert",
        False
    ):

        return None

    timestamp = datetime.now(
        timezone.utc
    )

    filename = (
        timestamp.strftime(
            "%Y%m%d_%H%M%S"
        )
        + ".json"
    )

    path = (
        ALERTS_DIR
        / filename
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            indent=4
        )

    return path


# ============================================================
# ALERT
# ============================================================

def process_alert(
    result
):

    risk = result.get(
        "risk",
        "LOW"
    )

    country = result.get(
        "country",
        "Unknown"
    )

    latitude = result.get(
        "latitude"
    )

    longitude = result.get(
        "longitude"
    )

    disaster = result.get(
        "disaster",
        "landslide"
    )

    affected = result.get(
        "affected_area_percent",
        0
    )

    print()
    print("=" * 70)
    print("🚨 DISASTER ALERT ENGINE")
    print("=" * 70)

    print()

    if result.get(
        "alert",
        False
    ):

        print(
            "🚨 ALERT DETECTED"
        )

        print(
            f"Disaster: "
            f"{disaster.upper()}"
        )

        print(
            f"Risk: {risk}"
        )

        print(
            f"Country: {country}"
        )

        print(
            f"Latitude: {latitude}"
        )

        print(
            f"Longitude: {longitude}"
        )

        print(
            f"Affected area: "
            f"{affected:.6f}%"
        )

        print()

        print(
            result.get(
                "alert_message",
                "Disaster detected."
            )
        )

        alert_path = save_alert(
            result
        )

        print()

        print(
            "Alert saved:"
        )

        print(
            alert_path
        )

    else:

        print(
            "✅ No active disaster alert."
        )


# ============================================================
# FULL PIPELINE
# ============================================================

def run_pipeline():

    print()
    print("=" * 70)
    print("🛰️ NEW SATELLITE DATA")
    print("=" * 70)

    run_script(
        TERRAIN_SCRIPT,
        "BUILD TERRAIN"
    )

    run_script(
        INPUT_SCRIPT,
        "SATELLITE INPUT"
    )

    run_script(
        PREDICT_SCRIPT,
        "LANDSLIDE PREDICTION"
    )

    run_script(
        CHECK_SCRIPT,
        "PREDICTION DIAGNOSTICS"
    )

    result = read_result()

    history = save_history(
        result
    )

    print()
    print(
        "History:"
    )

    print(
        history
    )

    process_alert(
        result
    )

    return result


# ============================================================
# ONE CHECK
# ============================================================

def check_once():

    state = load_state()

    now = datetime.now(
        timezone.utc
    )

    state[
        "last_check"
    ] = now.isoformat()

    print()
    print("=" * 70)
    print("🌏 SATELLITE MONITOR CHECK")
    print("=" * 70)

    print()
    print(
        "Check time:",
        now.isoformat()
    )

    product = get_latest_product()

    if product is None:

        print()
        print(
            "❌ No Sentinel-2 product found."
        )

        save_state(
            state
        )

        return

    print()
    print(
        "Latest product:"
    )

    print(
        product.name
    )

    last_product = state.get(
        "last_product"
    )

    if (
        last_product ==
        product.name
    ):

        print()
        print(
            "ℹ️ No new satellite product."
        )

        print(
            "Prediction skipped."
        )

        save_state(
            state
        )

        return

    print()
    print(
        "🛰️ NEW PRODUCT DETECTED"
    )

    try:

        result = run_pipeline()

        state[
            "last_product"
        ] = product.name

        state[
            "last_prediction"
        ] = datetime.now(
            timezone.utc
        ).isoformat()

        save_state(
            state
        )

        return result

    except Exception as e:

        print()
        print("=" * 70)
        print("❌ PIPELINE ERROR")
        print("=" * 70)

        print(
            type(e).__name__,
            e
        )

        traceback.print_exc()

        save_state(
            state
        )


# ============================================================
# MONITOR
# ============================================================

def start_monitor():

    print()
    print("=" * 70)
    print("🌏 INDIA + REGIONAL DISASTER MONITOR")
    print("=" * 70)

    print()

    print(
        "Monitoring interval:",
        f"{CHECK_INTERVAL_MINUTES} minutes"
    )

    print()

    print(
        "Press CTRL+C to stop."
    )

    print()

    while True:

        try:

            check_once()

            print()
            print("=" * 70)
            print("MONITOR ACTIVE")
            print("=" * 70)

            next_check = (
                time.time()
                +
                CHECK_INTERVAL_MINUTES
                * 60
            )

            while time.time() < next_check:

                remaining = int(
                    next_check -
                    time.time()
                )

                minutes = (
                    remaining // 60
                )

                seconds = (
                    remaining % 60
                )

                print(
                    f"\rNext check: "
                    f"{minutes:02d}:"
                    f"{seconds:02d}",
                    end="",
                    flush=True
                )

                time.sleep(1)

            print()

        except KeyboardInterrupt:

            print()
            print()
            print("=" * 70)
            print("MONITORING STOPPED")
            print("=" * 70)

            break

        except Exception as e:

            print()
            print(
                "Monitor error:",
                e
            )

            print(
                "Retrying in 60 seconds..."
            )

            time.sleep(60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    start_monitor()