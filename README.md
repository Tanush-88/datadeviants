# PHC-INTEL

## AI Healthcare System for Medicine Demand & Supply Chain Resilience

PHC-INTEL is a prototype focused on helping Primary Health Centres
(PHCs) understand medicine demand, monitor inventory, identify expiry
exposure, and explore resource redistribution between facilities.

The project was developed for **Track 3 --- Smart Health & Supply Chain
Resilience**.

> **Prototype note:** This README is based on project details visible in
> the development conversation and screenshots. Update
> implementation-specific details (such as the exact model, data source,
> or deployment setup) to match the final repository.

------------------------------------------------------------------------

## Key Features

-   **Medicine demand forecasting:** Displays a short-horizon medicine
    demand forecast. The API response includes a forecast horizon, model
    type, and prediction results.
-   **Inventory intelligence:** Tracks inventory information such as
    current stock, incoming stock, incoming days, expiry days, daily
    consumption, stock days, and status.
-   **Expiry intelligence:** Provides an endpoint for expiry alerts
    based on inventory records.
-   **Smart resource redistribution:** Identifies potential donor
    facilities with safe surplus for facilities with an unmet need,
    considering distance and estimated transport time.
-   **Transfer approval endpoint:** Provides an API route for approving
    a proposed transfer.
-   **Dashboard interface:** A dark-themed web interface with navigation
    for Command Center, PHC Intelligence, Disease Intelligence, Medicine
    Intelligence, Analytics, AI Predictions, and Priority Actions.

## How It Works

1.  The backend loads inventory information from its JSON inventory
    file.
2.  Demand predictions are retrieved for PHC/medicine combinations.
3.  The system compares predicted demand with available stock and safety
    stock.
4.  If a facility has a need, the redistribution logic checks potential
    donor facilities for safe surplus.
5.  Distance and estimated transport time are considered in the
    recommendation.
6.  The dashboard presents the information and proposed transfer for
    review.

Recommendations are decision-support outputs. They should be reviewed by
authorized healthcare or supply-chain personnel before any real-world
action.

## Technology

The visible project structure and commands indicate:

-   **Backend:** Python, FastAPI, and Uvicorn
-   **Frontend:** HTML-based interface (`frontend/index.html`)
-   **Data:** JSON inventory file (`backend/network_inventory.json`)
-   **API documentation/testing:** FastAPI interactive API docs (Swagger
    UI)

The exact machine-learning library, model algorithm, database, and
external data sources were not established in the conversation. Add them
here if they are part of the final implementation.

## Project Structure

The following structure is indicated by the development conversation.
Adjust filenames if your repository differs.

``` text
project-root/
├── backend/
│   ├── main.py
│   ├── redistribution.py
│   └── network_inventory.json
└── frontend/
    └── index.html
```

## Run Locally

### Requirements

-   Python installed
-   A terminal such as PowerShell
-   The project files cloned or downloaded from the repository

### Install dependencies

If the repository includes a `requirements.txt`, run:

``` powershell
cd backend
python -m pip install -r requirements.txt
```

If there is no requirements file, ensure the project's Python
dependencies, including FastAPI and Uvicorn, are installed.

### Start the backend

From the `backend` directory, run:

``` powershell
python -m uvicorn main:app --reload
```

The development session showed the backend running at:

``` text
http://127.0.0.1:8000
```

### Open API documentation

With the backend running, open:

``` text
http://127.0.0.1:8000/docs
```

Use the interactive docs to call the available endpoints and inspect
their responses.

### Open the frontend

Open `frontend/index.html` in a browser if the frontend is designed to
run directly as a local file.

If the frontend makes API requests, keep the backend running. If the
browser blocks requests because of local-file or CORS restrictions,
serve the frontend using a local development server and ensure the
backend's CORS settings allow that origin.

## API Endpoints

The following routes were visible in the development conversation:

  ----------------------------------------------------------------------------------------
  Method                  Endpoint                                 Purpose
  ----------------------- ---------------------------------------- -----------------------
  `GET`                   `/api/predictions`                       Returns demand forecast
                                                                   data, including
                                                                   forecast horizon, model
                                                                   type, and results.

  `GET`                   `/api/inventory`                         Returns inventory
                                                                   records for the PHC
                                                                   network.

  `GET`                   `/api/expiry`                            Returns expiry alerts
                                                                   based on inventory
                                                                   information.

  `GET`                   `/api/redistribution/{phc}/{medicine}`   Calculates
                                                                   redistribution
                                                                   information for a
                                                                   recipient PHC and
                                                                   medicine.

  `POST`                  `/api/transfers/approve`                 Endpoint for approving
                                                                   a proposed transfer.
  ----------------------------------------------------------------------------------------

### Example: redistribution

A successful request was shown for:

``` text
GET /api/redistribution/PHC-A/ORS
```

The response included fields such as:

-   `recipient`
-   `medicine`
-   `current_stock`
-   `predicted_7_day_demand`
-   `safety_stock`
-   `required_transfer`
-   `remaining_unmet_need`
-   `estimated_stockout_hours`
-   `recommendations`
-   `sos`

One example returned a recommendation to transfer **354 ORS** from
**PHC-C** to **PHC-A**, with a displayed distance of **1.06 km** and
estimated transport time of **0.03 hr**. These are sample prototype
values, not live operational guidance.

The transfer-approval route appeared in the API docs as requiring a JSON
request body. The exact body schema was not established in the
conversation; check `/docs` for the current schema before calling it.

## Data

The screenshots showed inventory records with fields similar to:

-   `phc`
-   `medicine`
-   `current_stock`
-   `incoming_stock`
-   `incoming_in_days`
-   `expiry_days`
-   `daily_consumption`
-   `stock_days`
-   `status`

The backend code shown loads inventory from `network_inventory.json`.
Keep the file structure consistent with what the backend expects.

Do not use real patient-identifiable information in demo data. For a
prototype presentation, use synthetic or appropriately de-identified
data.

## Demo and Submission

The repository and demo video serve different purposes:

-   **GitHub repository:** Share the source code, project structure, and
    setup instructions. Ensure the repository is public if the
    submission form requires public access.
-   **Demo video:** Record the application running locally, show the
    dashboard and API-backed features, and upload the video to a service
    such as Google Drive with access set to **Anyone with the link**.
-   **Presentation PDF:** Include the problem, solution, architecture,
    features, demonstration screenshots, and limitations.

A localhost address is only reachable from the computer running the
application; it is not a public demo link. The demo video lets reviewers
see the working prototype without running it themselves.

## Limitations and Responsible Use

-   This is a prototype, not a validated clinical or public-health
    decision system.
-   Forecast quality depends on input data and the model implementation;
    document the model and its evaluation in the repository.
-   Inventory and transfer values shown in the demo may be sample data.
-   Redistribution recommendations should be verified against actual
    stock, expiry, storage, transport, and local operating requirements
    before action.
-   Do not treat an API response or dashboard recommendation as
    authorization to move medical supplies.

## Future Improvements

Potential next steps, depending on the final project scope:

-   Document the forecasting model, training data, evaluation method,
    and limitations.
-   Add input validation and clear errors for missing or inconsistent
    inventory data.
-   Add tests for prediction, stock calculations, expiry alerts, and
    redistribution constraints.
-   Document the transfer-approval workflow and its request/response
    schema.
-   Provide reproducible setup instructions and a sample dataset.
-   Deploy the frontend and backend if a public live demo is required.

## License

Add the license and usage terms chosen for this project before public
distribution.
