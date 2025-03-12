# BigQuery to AlloyDB Data Migration

This project provides a Flask API service that manages data between BigQuery and AlloyDB.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set required environment variables:
```bash
export DB_HOST=your_alloydb_host
export DB_USER=your_alloydb_user
export DB_PASSWORD=your_alloydb_password
export DB_NAME=sample_db  # optional, defaults to sample_db
```

## API Endpoints

The service provides the following endpoints:

- `GET /health` - Health check endpoint
- `GET /users` - Retrieve all users from AlloyDB
- `GET /users/<id>` - Retrieve a specific user by ID
- `GET /customers` - Retrieve customers from BigQuery
- `POST /transfer/customers` - Transfer customers data from BigQuery to AlloyDB

## Running the Application

Start the Flask server:
```bash
python -m src.main
```

The server will start on port 8080 by default. You can override this by setting the PORT environment variable.
