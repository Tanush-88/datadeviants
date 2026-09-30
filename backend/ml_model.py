import json
import numpy as np

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DISEASE_FILE = BASE_DIR / "diseases.json"


def load_disease_data():

    with open(
        DISEASE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def predict_disease(
    disease_name,
    future_days=3
):

    data = load_disease_data()

    disease_found = None
    values = None


    for disease, information in data.items():

        if disease.lower() == disease_name.lower():

            disease_found = disease
            values = information["values"]

            break


    if disease_found is None:

        return None


    # Convert data into numpy arrays

    X = np.array(
        range(1, len(values) + 1)
    ).reshape(-1, 1)

    y = np.array(values, dtype=float)


    # Create simple linear regression
    # using NumPy instead of scikit-learn.

    x_values = X.flatten()

    y_values = y.astype(float)

    slope, intercept = np.polyfit(
        x_values,
        y_values,
        1
    )


    # Predict future days

    future_X = np.array(
        range(
            len(values) + 1,
            len(values) + future_days + 1
        )
    ).reshape(-1, 1)


    predictions = (
        slope * future_X.flatten()
        + intercept
    )


    # Cases cannot be negative

    predictions = np.maximum(
        predictions,
        0
    )


    return {
        "disease": disease_found,
        "historical_values": values,
        "predictions": [
            round(float(value), 2)
            for value in predictions
        ]
    }