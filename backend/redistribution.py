import json
import math
from pathlib import Path

from medicine_forecast import forecast_medicine


BASE_DIR = Path(__file__).resolve().parent

PHC_FILE = BASE_DIR / "phcs.json"
NETWORK_INVENTORY_FILE = BASE_DIR / "network_inventory.json"


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# DISTANCE (HAVERSINE)
# ============================================================

def calculate_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    return (
        earth_radius
        * 2
        * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a),
        )
    )


# ============================================================
# REDISTRIBUTION ENGINE
# ============================================================

def get_redistribution(
    recipient_phc,
    medicine,
    demand_multiplier=1.0
):
    phc_data = load_json(PHC_FILE)["phcs"]
    inventory_data = load_json(NETWORK_INVENTORY_FILE)["inventory"]

    # --------------------------------------------------------
    # FIND RECIPIENT PHC
    # --------------------------------------------------------

    recipient = next(
        (
            phc
            for phc in phc_data
            if phc["phc"] == recipient_phc
        ),
        None,
    )

    if recipient is None:
        return {
            "error": "Recipient PHC not found"
        }

    recipient_inventory = next(
        (
            item
            for item in inventory_data
            if item["phc"] == recipient_phc
            and item["medicine"] == medicine
        ),
        None,
    )

    if recipient_inventory is None:
        return {
            "error": "Medicine not found for recipient PHC"
        }

    # --------------------------------------------------------
    # FORECAST 7-DAY DEMAND
    # --------------------------------------------------------

    demand_forecast = forecast_medicine(
        medicine,
        days=7,
    )

    if demand_forecast is None:
        return {
            "error": "Forecast unavailable"
        }

    adjusted_forecast = [
        {
            **item,
            "predicted_demand":
                float(item["predicted_demand"])
                * float(demand_multiplier)
        }
        for item in demand_forecast
    ]

    total_forecast = sum(
        item["predicted_demand"]
        for item in adjusted_forecast
    )

    # ============================================================
    # RECIPIENT STOCKOUT ESTIMATE
    # ============================================================

    recipient_stock = float(
        recipient_inventory["current_stock"]
    )

    recipient_incoming = float(
        recipient_inventory["incoming_stock"]
    )

    recipient_incoming_days = int(
        recipient_inventory["incoming_in_days"]
    )

    simulated_stock = recipient_stock

    stockout_hours = None

    incoming_added = False

    for day_number, day in enumerate(
        adjusted_forecast,
        start=1
    ):

        if (
            not incoming_added
            and recipient_incoming_days <= day_number
        ):

            simulated_stock += recipient_incoming

            incoming_added = True

        simulated_stock -= day["predicted_demand"]

        if simulated_stock <= 0:

            stockout_hours = day_number * 24

            break

    if stockout_hours is None:

        stockout_hours = 7 * 24

    # --------------------------------------------------------
    # RECIPIENT TARGET
    # --------------------------------------------------------

    safety_stock = total_forecast * 0.20

    usable_incoming = 0.0

    if recipient_incoming_days <= 7:
        usable_incoming = recipient_incoming

    required_stock = total_forecast + safety_stock

    transfer_need = max(
        0.0,
        required_stock
        - recipient_stock
        - usable_incoming,
    )

    # --------------------------------------------------------
    # FIND DONORS
    # --------------------------------------------------------

    donors = []

    for donor in phc_data:

        if donor["phc"] == recipient_phc:
            continue

        donor_inventory = next(
            (
                item
                for item in inventory_data
                if item["phc"] == donor["phc"]
                and item["medicine"] == medicine
            ),
            None
        )

        if donor_inventory is None:
            continue

        donor_factor = float(
            donor.get("demand_factor", 1.0)
        )

        donor_forecast = (
            total_forecast
            * donor_factor
        )

        donor_daily_demand = (
            donor_forecast / 7.0
        )

        # Keep two days of donor demand as reserve.
        donor_safety_stock = (
            donor_daily_demand * 2.0
        )

        donor_incoming = 0.0

        if int(
            donor_inventory["incoming_in_days"]
        ) <= 7:

            donor_incoming = float(
                donor_inventory["incoming_stock"]
            )

        safe_surplus = (
            float(donor_inventory["current_stock"])
            + donor_incoming
            - donor_forecast
            - donor_safety_stock
        )

        if safe_surplus <= 0:
            continue

        distance = calculate_distance(
            float(recipient["latitude"]),
            float(recipient["longitude"]),
            float(donor["latitude"]),
            float(donor["longitude"])
        )

        # Demo transport assumption.
        transport_hours = distance / 40.0

        # Donor must be able to reach recipient
        # before the estimated shortage.
        if transport_hours >= stockout_hours:
            continue

        donors.append(
            {
                "phc": donor["phc"],
                "distance_km": round(
                    distance,
                    2
                ),
                "transport_hours": round(
                    transport_hours,
                    2
                ),
                "safe_surplus": round(
                    safe_surplus,
                    2
                )
            }
        )

    # --------------------------------------------------------
    # NEAREST FEASIBLE DONOR FIRST
    # --------------------------------------------------------

    donors.sort(
        key=lambda donor: donor["transport_hours"]
    )

    recommendations = []

    remaining_need = float(transfer_need)

    for donor in donors:

        if remaining_need <= 0:
            break

        transfer_quantity = min(
            remaining_need,
            float(donor["safe_surplus"]),
        )

        transfer_quantity = round(
            transfer_quantity
        )

        if transfer_quantity <= 0:
            continue

        recommendations.append(
            {
                "source_phc": donor["phc"],
                "destination_phc": recipient_phc,
                "medicine": medicine,
                "quantity": transfer_quantity,
                "distance_km": donor["distance_km"],
                "estimated_transport_hours": donor[
                    "transport_hours"
                ],
                "donor_safe_surplus": round(
                    donor["safe_surplus"]
                ),
            }
        )

        remaining_need -= transfer_quantity
    # --------------------------------------------------------
    # SOS
    # --------------------------------------------------------

    sos = remaining_need > 0

    return {
        "recipient": recipient_phc,
        "medicine": medicine,
        "current_stock": round(recipient_stock),
        "predicted_7_day_demand": round(total_forecast),
        "safety_stock": round(safety_stock),
        "required_transfer": round(transfer_need),
        "remaining_unmet_need": round(
            max(0.0, remaining_need)
        ),
        "estimated_stockout_hours": stockout_hours,
        "recommendations": recommendations,
        "sos": sos,
    }