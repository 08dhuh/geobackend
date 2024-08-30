# GeoBackend API

This Django backend provides an API for calculating wellbore parameters based on geological data. It utilises the `geodrillcalc` Python package for the core calculations and interacts with a GeoServer instance to retrieve the necessary geological information.

## Features

- **Wellbore Parameter Calculation:** Computes wellbore parameters such as well depth, pump depth, and more, considering factors like aquifer properties, required flow rate, and drawdown.
- **GeoServer Integration:** Retrieves depth data and aquifer information from a GeoServer WMS service.
- **Data Validation:** Ensures user input is valid and checks the feasibility of calculations based on the retrieved geological data.
- **Session-Based Results:** Stores calculation results associated with user sessions for later retrieval.

## API Endpoints

The API provides the following endpoints:

- `/calculate-wellbore`: Accepts user input, retrieves geological data, performs calculations, and returns the results.
- `/calculate-profile`: A test endpoint for directly testing the wellbore calculation logic with provided data.

## Data Flow

1. **User Input:** The frontend sends user-defined parameters (e.g., coordinates, required flow rate) and initial input values to the `/calculate-wellbore` endpoint.
2. **Data Retrieval:** The backend queries the GeoServer WMS service to obtain depth data and aquifer information for the specified location.
3. **Calculation:** The `geodrillcalc` package uses the retrieved data and user input to calculate wellbore parameters.
4. **Result Storage:** Calculation results are stored in the database, associated with the user's session.
5. **Response:** The API returns the calculated wellbore parameters to the frontend.

## Dependencies

- Django
- djangorestframework
- requests
- beautifulsoup4
- pyproj
- numpy
- redis (for caching)
- geodrillcalc (https://github.com/08dhuh/geodrillcalc): A Python package used for wellbore parameter calculations

## Installation

1. Install the required Python packages.
2. Configure the GeoServer connection settings in the backend settings.
3. Run migrations to set up the database.

## Usage

The API can be integrated into a frontend application to provide users with the ability to calculate wellbore parameters based on location and other input factors.

