import csv
import json
import math
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = BASE_DIR / "medicine_history.csv"
MODEL_FILE = BASE_DIR / "medicine_demand_model.json"


# ============================================================
# LOAD CSV
# ============================================================

rows = []

with open(
    DATA_FILE,
    "r",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:
        rows.append(row)


# ============================================================
# GROUP DATA BY MEDICINE
# ============================================================

medicine_data = {}

for row in rows:

    medicine = row["medicine"]

    if medicine not in medicine_data:
        medicine_data[medicine] = []

    medicine_data[medicine].append(row)


# ============================================================
# LINEAR REGRESSION USING NUMPY
# ============================================================

import numpy as np


models = {}

all_actual = []
all_predictions = []


for medicine, data in medicine_data.items():

    # --------------------------------------------------------
    # BUILD FEATURES
    # --------------------------------------------------------

    X = []
    y = []

    previous_demands = []

    for day_index, row in enumerate(data):

        patient_load = float(
            row["patient_load"]
        )

        disease_pressure = float(
            row["disease_pressure"]
        )

        demand = float(
            row["demand"]
        )

        # Log transform keeps predicted demand positive.
        log_demand = math.log1p(demand)

        # Lag demand
        if previous_demands:
            lag_1 = previous_demands[-1]
        else:
            lag_1 = demand

        # 7-day average
        recent = previous_demands[-7:]

        if recent:
            rolling_7 = sum(recent) / len(recent)
        else:
            rolling_7 = demand

        X.append([
            1.0,                   # intercept
            patient_load,
            disease_pressure,
            day_index,
            lag_1,
            rolling_7
        ])

        y.append(log_demand)

        previous_demands.append(demand)


    X = np.array(X, dtype=float)
    y = np.array(y, dtype=float)


    # --------------------------------------------------------
    # LAST 18 DAYS = TEST DATA
    # --------------------------------------------------------

    split = len(X) - 18

    X_train = X[:split]
    y_train = y[:split]

    X_test = X[split:]
    y_test = y[split:]


    # --------------------------------------------------------
    # TRAIN
    # --------------------------------------------------------

    coefficients = np.linalg.lstsq(
        X_train,
        y_train,
        rcond=None
    )[0]


    # --------------------------------------------------------
    # TEST
    # --------------------------------------------------------

    log_predictions = (
        X_test @ coefficients
    )

    predictions = [
        max(
            0,
            math.expm1(value)
        )
        for value in log_predictions
    ]

    actual = [
        math.expm1(value)
        for value in y_test
    ]


    all_predictions.extend(predictions)
    all_actual.extend(actual)


    # --------------------------------------------------------
    # SAVE MODEL FOR THIS MEDICINE
    # --------------------------------------------------------

    models[medicine] = {

        "coefficients":
            coefficients.tolist(),

        "last_day_index":
            len(data) - 1
    }


# ============================================================
# MODEL ERROR
# ============================================================

mae = sum(
    abs(actual - predicted)
    for actual, predicted
    in zip(
        all_actual,
        all_predictions
    )
) / len(all_actual)


# ============================================================
# SAVE MODEL
# ============================================================

model_data = {

    "model_type":
        "Per-medicine NumPy Linear Regression",

    "mae":
        round(float(mae), 2),

    "models":
        models
}


with open(
    MODEL_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        model_data,
        file,
        indent=4
    )


print("======================================")
print("MEDICINE ML MODEL TRAINED")
print("======================================")

print(
    f"Medicines: {len(models)}"
)

print(
    f"Total records: {len(rows)}"
)

print(
    f"MAE: {mae:.2f}"
)

print(
    f"Model saved to:\n{MODEL_FILE}"
)