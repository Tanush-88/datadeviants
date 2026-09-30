import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INVENTORY_FILE = BASE_DIR / "inventory.json"
PHC_FILE = BASE_DIR / "phcs.json"
NETWORK_FILE = BASE_DIR / "network_inventory.json"


# ============================================================
# LOAD EXISTING INVENTORY
# ============================================================

with open(
    INVENTORY_FILE,
    "r",
    encoding="utf-8"
) as file:

    original_data = json.load(file)


base_inventory = original_data["inventory"]


# ============================================================
# CREATE SYNTHETIC PHC NETWORK
# ============================================================

phcs = [

    {
        "phc": "PHC-A",
        "latitude": 19.00,
        "longitude": 73.00,
        "demand_factor": 1.00
    },

    {
        "phc": "PHC-B",
        "latitude": 19.03,
        "longitude": 73.02,
        "demand_factor": 0.80
    },

    {
        "phc": "PHC-C",
        "latitude": 19.06,
        "longitude": 73.01,
        "demand_factor": 0.90
    },

    {
        "phc": "PHC-D",
        "latitude": 19.01,
        "longitude": 73.07,
        "demand_factor": 1.10
    },

    {
        "phc": "PHC-E",
        "latitude": 19.09,
        "longitude": 73.06,
        "demand_factor": 1.20
    }

]


# ============================================================
# SAVE PHC DATA
# ============================================================

with open(
    PHC_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        {
            "phcs": phcs
        },
        file,
        indent=4
    )


# ============================================================
# CREATE NETWORK INVENTORY
# ============================================================

network_inventory = []


# Stock multipliers for synthetic donor PHCs
stock_multiplier = {

    "PHC-A": 1.0,

    "PHC-B": 4.0,

    "PHC-C": 3.0,

    "PHC-D": 2.0,

    "PHC-E": 1.5

}


# Incoming shipment multiplier
incoming_multiplier = {

    "PHC-A": 1.0,

    "PHC-B": 3.0,

    "PHC-C": 2.0,

    "PHC-D": 2.0,

    "PHC-E": 1.0

}


# Days until incoming shipment
incoming_days = {

    "PHC-A": 5,

    "PHC-B": 3,

    "PHC-C": 5,

    "PHC-D": 2,

    "PHC-E": 8

}


for phc in phcs:

    phc_name = phc["phc"]


    for item in base_inventory:

        network_inventory.append({

            "phc":
                phc_name,

            "medicine":
                item["medicine"],

            "current_stock":
                round(
                    item["current_stock"]
                    * stock_multiplier[phc_name]
                ),

            "incoming_stock":
                round(
                    item["incoming_stock"]
                    * incoming_multiplier[phc_name]
                ),

            "incoming_in_days":
                incoming_days[phc_name],

            "expiry_days":
                item["expiry_days"]

        })


# ============================================================
# SAVE NETWORK INVENTORY
# ============================================================

with open(
    NETWORK_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        {
            "inventory":
                network_inventory
        },
        file,
        indent=4
    )


print("========================================")
print("PHC NETWORK CREATED")
print("========================================")

print(
    "PHCs:",
    len(phcs)
)

print(
    "Inventory records:",
    len(network_inventory)
)

print(
    f"Created:\n{PHC_FILE}"
)

print(
    f"Created:\n{NETWORK_FILE}"
)