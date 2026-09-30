import csv
import json
import math

from pathlib import Path
from datetime import date, timedelta


BASE_DIR = Path(__file__).resolve().parent

HISTORY_FILE = (
    BASE_DIR / "medicine_history.csv"
)

MODEL_FILE = (
    BASE_DIR / "medicine_demand_model.json"
)


# ============================================================
# LOAD MODEL
# ============================================================

with open(
    MODEL_FILE,
    "r",
    encoding="utf-8"
) as file:

    MODEL = json.load(file)


# ============================================================
# LOAD HISTORY
# ============================================================

def load_history():

    rows = []

    with open(
        HISTORY_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            rows.append(row)

    return rows


# ============================================================
# FORECAST ONE MEDICINE
# ============================================================

def forecast_medicine(
    medicine,
    days=7
):

    history = load_history()


    medicine_rows = [

        row

        for row in history

        if row["medicine"] == medicine

    ]


    if not medicine_rows:

        return None


    if medicine not in MODEL["models"]:

        return None


    coefficients = (
        MODEL["models"]
        [medicine]
        ["coefficients"]
    )


    # --------------------------------------------------------
    # LAST OBSERVED DATA
    # --------------------------------------------------------

    last_row = medicine_rows[-1]

    last_date = date.fromisoformat(
        last_row["date"]
    )


    patient_values = [

        float(row["patient_load"])

        for row
        in medicine_rows[-7:]

    ]


    pressure_values = [

        float(row["disease_pressure"])

        for row
        in medicine_rows[-7:]

    ]


    demand_values = [

        float(row["demand"])

        for row
        in medicine_rows
    ]


    current_patient_load = (

        sum(patient_values)
        / len(patient_values)

    )


    current_pressure = (

        sum(pressure_values)
        / len(pressure_values)

    )


    predictions = []


    # ========================================================
    # RECURSIVE FORECAST
    # ========================================================

    for i in range(1, days + 1):


        future_date = (

            last_date
            + timedelta(days=i)

        )


        # Slightly increase pressure.
        # This represents an ongoing epidemic scenario.

        future_patient_load = (

            current_patient_load
            * (1.01 ** i)

        )


        future_pressure = (

            current_pressure
            * (1.01 ** i)

        )


        # Latest predicted/observed demand

        if predictions:

            lag_1 = predictions[-1][
                "predicted_demand"
            ]

        else:

            lag_1 = demand_values[-1]


        recent_demands = (

            demand_values[-6:]
        )


        for item in predictions[-6:]:

            recent_demands.append(

                item["predicted_demand"]

            )


        rolling_7 = (

            sum(recent_demands)
            / len(recent_demands)

        )


        # IMPORTANT:
        # Time is relative to this medicine only.

        day_index = (

            len(medicine_rows)
            - 1
            + i

        )


        X = [

            1.0,

            future_patient_load,

            future_pressure,

            day_index,

            lag_1,

            rolling_7

        ]


        log_prediction = sum(

            x * coefficient

            for x, coefficient
            in zip(
                X,
                coefficients
            )

        )


        demand = max(

            0,

            math.expm1(
                log_prediction
            )

        )


        predictions.append({

            "date":
                future_date.isoformat(),

            "predicted_demand":
                round(
                    demand,
                    2
                )

        })


    return predictions


# ============================================================
# API OUTPUT
# ============================================================

def get_ml_predictions():

    history = load_history()


    medicines = sorted(

        set(

            row["medicine"]

            for row in history

        )

    )


    results = []


    for medicine in medicines:


        forecast = forecast_medicine(

            medicine,
            days=7

        )


        total_demand = sum(

            item["predicted_demand"]

            for item in forecast

        )


        results.append({

            "phc":
                "PHC-A",

            "medicine":
                medicine,

            "predicted_7_day_demand":
                round(
                    total_demand
                ),

            "daily_forecast":
                forecast,

            "model_mae":
                MODEL["mae"]

        })


    return {

        "forecast_horizon_days":
            7,

        "model_type":
            MODEL["model_type"],

        "results":
            results

    }