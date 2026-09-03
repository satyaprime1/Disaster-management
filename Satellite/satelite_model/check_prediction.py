from pathlib import Path
import json

import numpy as np


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent

OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
)

PROBABILITY_FILE = (
    OUTPUT_DIR
    / "stitched_probability.npy"
)

RESULT_FILE = (
    OUTPUT_DIR
    / "prediction_results.json"
)


# ============================================================
# LOAD
# ============================================================

print()
print("=" * 70)
print("PREDICTION DIAGNOSTICS")
print("=" * 70)

if not PROBABILITY_FILE.exists():

    raise FileNotFoundError(
        f"Probability map not found:\n"
        f"{PROBABILITY_FILE}"
    )

probability = np.load(
    PROBABILITY_FILE
)

probability = np.nan_to_num(
    probability,
    nan=0.0,
    posinf=1.0,
    neginf=0.0
)

probability = np.clip(
    probability,
    0.0,
    1.0
)


# ============================================================
# STATISTICS
# ============================================================

shape = probability.shape

minimum = float(
    probability.min()
)

maximum = float(
    probability.max()
)

mean = float(
    probability.mean()
)

median = float(
    np.median(probability)
)


print()
print(
    "Shape:",
    shape
)

print(
    "Min:",
    minimum
)

print(
    "Max:",
    maximum
)

print(
    "Mean:",
    mean
)

print(
    "Median:",
    median
)


# ============================================================
# PERCENTILES
# ============================================================

print()
print("Percentiles:")

for p in [
    90,
    95,
    99,
    99.5,
    99.9,
    99.99,
    99.999
]:

    value = float(
        np.percentile(
            probability,
            p
        )
    )

    print(
        f"{p:7.3f}% : "
        f"{value:.8f}"
    )


# ============================================================
# THRESHOLDS
# ============================================================

print()
print(
    "Pixels above thresholds:"
)

for threshold in [
    0.1,
    0.2,
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.8,
    0.9
]:

    count = int(
        np.sum(
            probability >= threshold
        )
    )

    percentage = (
        count /
        probability.size *
        100
    )

    print(

        f">= {threshold:.1f} : "
        f"{count:8d} pixels "
        f"({percentage:.6f}%)"

    )


# ============================================================
# UPDATE JSON
# ============================================================

if RESULT_FILE.exists():

    with open(
        RESULT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        result = json.load(f)

else:

    result = {}


result[
    "diagnostics"
] = {

    "shape":
        list(shape),

    "minimum":
        minimum,

    "maximum":
        maximum,

    "mean":
        mean,

    "median":
        median,

    "percentiles": {

        "90":
            float(
                np.percentile(
                    probability,
                    90
                )
            ),

        "95":
            float(
                np.percentile(
                    probability,
                    95
                )
            ),

        "99":
            float(
                np.percentile(
                    probability,
                    99
                )
            ),

        "99.9":
            float(
                np.percentile(
                    probability,
                    99.9
                )
            ),

        "99.99":
            float(
                np.percentile(
                    probability,
                    99.99
                )
            )

    }

}


with open(
    RESULT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        result,
        f,
        indent=4
    )


print()
print("=" * 70)
print("DIAGNOSTICS COMPLETE")
print("=" * 70)