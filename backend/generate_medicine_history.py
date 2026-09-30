import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DISEASE_FILE = BASE_DIR / "diseases.json"
MEDICINE_FILE = BASE_DIR / "medicines.json"
OUTPUT_FILE = BASE_DIR / "medicine_history.csv"


random.seed(42)


# ------------------------------------------------------------
# LOAD JSON
# ------------------------------------------------------------

def load_json(path):

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


diseases = load_json(DISEASE_FILE)
medicines = load_json(MEDICINE_FILE)["medicines"]


# ------------------------------------------------------------
# CREATE DISEASE BASELINE
# ------------------------------------------------------------

disease_pressure = {}

for disease, info in diseases.items():

    values = info["values"]

    average = sum(values) / len(values)

    disease_pressure[disease] = average


# ------------------------------------------------------------
# CREATE 90 DAYS OF SYNTHETIC HISTORY
# ------------------------------------------------------------

start_date = date.today() - timedelta(days=89)

rows = []


for day_number in range(90):

    current_date = start_date + timedelta(days=day_number)

    # Gradually increasing patient load toward the end.
    epidemic_factor = 1 + (day_number / 90) * 0.8

    weekend_factor = 0.9 if current_date.weekday() >= 5 else 1.0


    patient_load = (
        100
        * epidemic_factor
        * weekend_factor
        * random.uniform(0.90, 1.10)
    )


    for medicine in medicines:

        medicine_name = medicine["name"]

        base_consumption = medicine[
            "average_daily_consumption"
        ]


        # Find diseases associated with this medicine.
        used_for = medicine.get("used_for", [])


        disease_factor = 1.0


        if used_for:

            relevant_pressure = []

            for disease in used_for:

                if disease in disease_pressure:

                    relevant_pressure.append(
                        disease_pressure[disease]
                    )


            if relevant_pressure:

                avg_pressure = (
                    sum(relevant_pressure)
                    / len(relevant_pressure)
                )

                disease_factor = (
                    1 + (avg_pressure / 100)
                )


        # Final synthetic demand.
        demand = (
            base_consumption
            * disease_factor
            * epidemic_factor
            * random.uniform(0.85, 1.15)
        )


        rows.append({

            "date": current_date.isoformat(),

            "phc": "PHC-A",

            "medicine": medicine_name,

            "patient_load": round(
                patient_load, 2
            ),

            "disease_pressure": round(
                disease_factor, 3
            ),

            "demand": round(
                demand, 2
            )
        })


# ------------------------------------------------------------
# SAVE CSV
# ------------------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "date",
            "phc",
            "medicine",
            "patient_load",
            "disease_pressure",
            "demand"
        ]
    )

    writer.writeheader()

    writer.writerows(rows)


print("Medicine history created successfully.")

print(
    f"Rows generated: {len(rows)}"
)

print(
    f"Saved to: {OUTPUT_FILE}"
)