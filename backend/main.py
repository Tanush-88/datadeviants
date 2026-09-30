from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from statistics import mean

from ml_model import predict_disease
from medicine_forecast import get_ml_predictions
from redistribution import get_redistribution

# ============================================================
# PHC INTELLIGENCE BACKEND
# ============================================================

app = FastAPI(
    title="PHC Intelligence API",
    description="AI-based Primary Health Centre Intelligence Backend",
    version="1.0"
)


# ============================================================
# CORS
# Allows frontend to communicate with backend
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# FILE LOCATIONS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DISEASE_FILE = BASE_DIR / "diseases.json"
MEDICINE_FILE = BASE_DIR / "medicines.json"
INVENTORY_FILE = BASE_DIR / "network_inventory.json"


# ============================================================
# LOAD JSON FILE
# ============================================================

def load_json(file_path):

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "status": "online",
        "message": "PHC Intelligence Backend is running",
        "version": "1.0"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():

    return {
        "status": "healthy",
        "backend": "PHC Intelligence",
        "message": "Backend is working correctly"
    }


# ============================================================
# DISEASE INTELLIGENCE
# ============================================================

@app.get("/api/diseases")
def get_diseases():

    data = load_json(DISEASE_FILE)

    results = []

    for disease, information in data.items():

        results.append({
            "disease": disease,
            "values": information["values"],
            "signal": information["signal"],
            "risk": information["risk"]
        })

    return {
        "count": len(results),
        "results": results
    }


# ============================================================
# SINGLE DISEASE
# ============================================================

@app.get("/api/diseases/{disease_name}")
def get_single_disease(disease_name: str):

    data = load_json(DISEASE_FILE)

    # Case-insensitive search
    for disease, information in data.items():

        if disease.lower() == disease_name.lower():

            return {
                "disease": disease,
                "values": information["values"],
                "signal": information["signal"],
                "risk": information["risk"]
            }

    return {
        "error": "Disease not found"
    }
# ============================================================
# ML DISEASE FORECAST
# ============================================================

@app.get("/api/ml/disease/{disease_name}")
def ml_disease_prediction(
    disease_name: str,
    days: int = 3
):

    result = predict_disease(
        disease_name,
        days
    )

    if result is None:

        return {
            "error": "Disease not found"
        }

    return result

# ============================================================
# MEDICINES
# ============================================================

@app.get("/api/medicines")
def get_medicines():

    data = load_json(MEDICINE_FILE)

    return {
        "count": len(data["medicines"]),
        "results": data["medicines"]
    }


# ============================================================
# INVENTORY
# ============================================================

@app.get("/api/inventory")
def get_inventory():

    inventory_data = load_json(
        INVENTORY_FILE
    )

    results = []

    for item in inventory_data["inventory"]:

        current_stock = float(
            item["current_stock"]
        )

        medicine_name = item["medicine"]

        # Use the original medicine dataset
        # for the baseline daily consumption.
        medicine_data = load_json(
            MEDICINE_FILE
        )

        daily_consumption = 0

        for medicine in medicine_data["medicines"]:

            if medicine["name"] == medicine_name:

                daily_consumption = float(
                    medicine["average_daily_consumption"]
                )

                break

        if daily_consumption > 0:

            stock_days = (
                current_stock
                / daily_consumption
            )

        else:

            stock_days = 999


        if stock_days <= 3:

            status = "CRITICAL"

        elif stock_days <= 7:

            status = "LOW"

        elif stock_days <= 14:

            status = "MEDIUM"

        else:

            status = "HEALTHY"


        results.append({

            **item,

            "daily_consumption":
                daily_consumption,

            "stock_days":
                round(
                    stock_days,
                    1
                ),

            "status":
                status

        })


    return {

        "count":
            len(results),

        "results":
            results

    }

# ============================================================
# MEDICINE DEMAND PREDICTION
# ============================================================

# ============================================================
# ML MEDICINE DEMAND + INVENTORY INTELLIGENCE
# ============================================================

@app.get("/api/predictions")
def get_predictions():

    # Get ML forecasts
    prediction_data = get_ml_predictions()

    # Load current inventory
    inventory_data = load_json(
        INVENTORY_FILE
    )

    inventory_lookup = {}

    for item in inventory_data["inventory"]:

        key = (
            item["phc"],
            item["medicine"]
        )

        inventory_lookup[key] = item


    results = []


    for prediction in prediction_data["results"]:

        phc = prediction["phc"]

        medicine = prediction["medicine"]


        # Find matching inventory
        inventory = inventory_lookup.get(
            (phc, medicine)
        )


        if inventory is None:

            continue


        current_stock = float(
            inventory["current_stock"]
        )

        incoming_stock = float(
            inventory["incoming_stock"]
        )


        predicted_demand = float(
            prediction[
                "predicted_7_day_demand"
            ]
        )


        # ----------------------------------------------------
        # SAFETY STOCK
        # ----------------------------------------------------

        safety_stock = (
            predicted_demand * 0.20
        )


        # ----------------------------------------------------
        # TOTAL AVAILABLE SUPPLY
        # ----------------------------------------------------

        total_available = (
            current_stock
            + incoming_stock
        )


        # ----------------------------------------------------
        # PROJECTED STOCK
        # ----------------------------------------------------

        projected_stock = (
            total_available
            - predicted_demand
        )


        # ----------------------------------------------------
        # RECOMMENDED ORDER
        # ----------------------------------------------------

        recommended_order = max(

            0,

            predicted_demand
            + safety_stock
            - total_available

        )


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if projected_stock < 0:

            status = "CRITICAL"


        elif projected_stock < safety_stock:

            status = "HIGH"


        elif current_stock < predicted_demand:

            status = "MONITOR"


        else:

            status = "STABLE"


        results.append({

            "phc":
                phc,

            "medicine":
                medicine,

            "current_stock":
                round(
                    current_stock
                ),

            "incoming_stock":
                round(
                    incoming_stock
                ),

            "predicted_7_day_demand":
                round(
                    predicted_demand
                ),

            "safety_stock":
                round(
                    safety_stock
                ),

            "total_available":
                round(
                    total_available
                ),

            "projected_stock":
                round(
                    projected_stock
                ),

            "recommended_order":
                round(
                    recommended_order
                ),

            "status":
                status,

            "daily_forecast":
                prediction[
                    "daily_forecast"
                ],

            "model_mae":
                prediction[
                    "model_mae"
                ]

        })


    return {

        "forecast_horizon_days":
            prediction_data[
                "forecast_horizon_days"
            ],

        "model_type":
            prediction_data[
                "model_type"
            ],

        "results":
            results

    }


 # ============================================================
# RESOURCE REDISTRIBUTION
# ============================================================

@app.get("/api/redistribution/{phc}/{medicine}")
def get_redistribution_endpoint(
    phc: str,
    medicine: str,
    surge_factor: float = 1.0
):
    return get_redistribution(
        phc,
        medicine,
        surge_factor
    )
# ============================================================
# APPROVE RESOURCE TRANSFER
# ============================================================

@app.post("/api/transfers/approve")
def approve_transfer(request: dict):

    source_phc = request.get("source_phc")
    destination_phc = request.get("destination_phc")
    medicine = request.get("medicine")
    quantity = request.get("quantity")

    if not source_phc:
        return {
            "success": False,
            "message": "Source PHC is required"
        }

    if not destination_phc:
        return {
            "success": False,
            "message": "Destination PHC is required"
        }

    if not medicine:
        return {
            "success": False,
            "message": "Medicine is required"
        }

    if not quantity or quantity <= 0:
        return {
            "success": False,
            "message": "Transfer quantity must be positive"
        }

    network_file = BASE_DIR / "network_inventory.json"

    network_data = load_json(network_file)

    source_item = None
    destination_item = None

    for item in network_data["inventory"]:

        if (
            item["phc"] == source_phc
            and item["medicine"] == medicine
        ):
            source_item = item

        if (
            item["phc"] == destination_phc
            and item["medicine"] == medicine
        ):
            destination_item = item

    if source_item is None:
        return {
            "success": False,
            "message": "Source inventory not found"
        }

    if destination_item is None:
        return {
            "success": False,
            "message": "Destination inventory not found"
        }

    source_stock = float(
        source_item["current_stock"]
    )

    if quantity > source_stock:
        return {
            "success": False,
            "message": "Source PHC does not have enough stock"
        }

    source_item["current_stock"] = round(
        source_stock - quantity
    )

    destination_item["current_stock"] = round(
        float(destination_item["current_stock"])
        + quantity
    )

    with open(
        network_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            network_data,
            file,
            indent=4
        )

    return {
        "success": True,
        "message": "Transfer approved successfully",
        "source_phc": source_phc,
        "destination_phc": destination_phc,
        "medicine": medicine,
        "quantity": quantity,
        "source_remaining_stock":
            source_item["current_stock"],
        "destination_new_stock":
            destination_item["current_stock"],
        "status": "APPROVED"
    }
# ============================================================
# EXPIRY INTELLIGENCE
# ============================================================

@app.get("/api/expiry")
def get_expiry_alerts():

    data = load_json(INVENTORY_FILE)

    results = []

    for item in data["inventory"]:

        expiry_days = item["expiry_days"]

        if expiry_days <= 7:
            status = "CRITICAL"

        elif expiry_days <= 30:
            status = "EXPIRING SOON"

        elif expiry_days <= 60:
            status = "MONITOR"

        else:
            status = "SAFE"

        results.append({
            "phc": item["phc"],
            "medicine": item["medicine"],
            "current_stock": item["current_stock"],
            "expiry_days": expiry_days,
            "status": status
        })

    return {
        "results": results
    }


# ============================================================
# BED PREDICTION
# ============================================================

@app.get("/api/beds")
def get_bed_prediction():

    # Prototype values
    total_beds = 30
    currently_occupied = 22

    current_occupancy = (
        currently_occupied / total_beds
    ) * 100

    # Prototype forecast
    expected_increase = 5

    predicted_occupancy = (
        currently_occupied + expected_increase
    )

    occupancy_percentage = (
        predicted_occupancy / total_beds
    ) * 100

    if occupancy_percentage >= 90:
        risk = "CRITICAL"

    elif occupancy_percentage >= 75:
        risk = "HIGH"

    elif occupancy_percentage >= 60:
        risk = "MEDIUM"

    else:
        risk = "LOW"

    return {
        "total_beds": total_beds,
        "currently_occupied": currently_occupied,
        "current_occupancy_percentage": round(
            current_occupancy, 1
        ),
        "predicted_occupied_beds": predicted_occupancy,
        "predicted_occupancy_percentage": round(
            occupancy_percentage, 1
        ),
        "risk": risk
    }


# ============================================================
# WORKFORCE PREDICTION
# ============================================================

@app.get("/api/workforce")
def get_workforce_prediction():

    current_staff = {
        "doctors": 3,
        "nurses": 7,
        "pharmacists": 2,
        "lab_technicians": 2
    }

    predicted_patient_footfall = 180

    # Prototype workload assumptions
    doctor_requirement = max(
        1,
        round(predicted_patient_footfall / 60)
    )

    nurse_requirement = max(
        1,
        round(predicted_patient_footfall / 30)
    )

    pharmacist_requirement = max(
        1,
        round(predicted_patient_footfall / 100)
    )

    lab_requirement = max(
        1,
        round(predicted_patient_footfall / 90)
    )

    required_staff = {
        "doctors": doctor_requirement,
        "nurses": nurse_requirement,
        "pharmacists": pharmacist_requirement,
        "lab_technicians": lab_requirement
    }

    gaps = {}

    for role in required_staff:

        gaps[role] = max(
            0,
            required_staff[role] - current_staff[role]
        )

    return {
        "predicted_patient_footfall": predicted_patient_footfall,
        "current_staff": current_staff,
        "required_staff": required_staff,
        "staff_gap": gaps
    }


# ============================================================
# PRIORITY ALERTS
# ============================================================

@app.get("/api/alerts")
def get_alerts():

    inventory_data = load_json(INVENTORY_FILE)

    alerts = []

    for item in inventory_data["inventory"]:

        stock_days = (
            item["current_stock"] /
            item["daily_consumption"]
        )

        # Stock alert
        if stock_days <= 3:

            alerts.append({
                "type": "MEDICINE",
                "priority": "CRITICAL",
                "medicine": item["medicine"],
                "message":
                    f"{item['medicine']} stock may run out in "
                    f"{round(stock_days, 1)} days."
            })

        elif stock_days <= 7:

            alerts.append({
                "type": "MEDICINE",
                "priority": "HIGH",
                "medicine": item["medicine"],
                "message":
                    f"{item['medicine']} has approximately "
                    f"{round(stock_days, 1)} days of stock."
            })

        # Expiry alert
        if item["expiry_days"] <= 30:

            alerts.append({
                "type": "EXPIRY",
                "priority": "HIGH",
                "medicine": item["medicine"],
                "message":
                    f"{item['medicine']} stock expires in "
                    f"{item['expiry_days']} days."
            })

    return {
        "count": len(alerts),
        "alerts": alerts
    }


# ============================================================
# AI DECISION SUMMARY
# ============================================================

@app.get("/api/ai-summary")
def get_ai_summary():

    inventory_data = load_json(INVENTORY_FILE)
    disease_data = load_json(DISEASE_FILE)

    critical_medicines = []
    expiry_risks = []

    for item in inventory_data["inventory"]:

        stock_days = (
            item["current_stock"] /
            item["daily_consumption"]
        )

        if stock_days <= 3:
            critical_medicines.append(
                item["medicine"]
            )

        if item["expiry_days"] <= 30:
            expiry_risks.append(
                item["medicine"]
            )

    rising_diseases = []

    for disease, information in disease_data.items():

        if information["signal"] == "RISING":
            rising_diseases.append(disease)

    if len(critical_medicines) > 0:
        overall_risk = "HIGH"

    elif len(rising_diseases) >= 3:
        overall_risk = "MEDIUM"

    else:
        overall_risk = "LOW"

    return {

        "overall_risk": overall_risk,

        "rising_diseases": rising_diseases,

        "critical_medicines": critical_medicines,

        "expiry_risks": expiry_risks,

        "recommended_actions": [

            "Monitor rising disease trends",

            "Review medicines with low stock coverage",

            "Check medicines approaching expiry",

            "Prepare additional stock if disease demand continues rising",

            "Review bed and workforce requirements"
        ]
    }


# ============================================================
# RUNNING INFORMATION
# ============================================================

@app.get("/api")
def api_information():

    return {

        "message": "PHC Intelligence API",

        "available_endpoints": [

            "/api/health",

            "/api/diseases",

            "/api/diseases/{disease_name}",

            "/api/medicines",

            "/api/inventory",

            "/api/predictions",

            "/api/expiry",

            "/api/beds",

            "/api/workforce",

            "/api/alerts",

            "/api/ai-summary"
        ]
    }