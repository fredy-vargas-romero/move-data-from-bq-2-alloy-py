# BigQuery to Alloy Data Migration

This project fetches data from BigQuery and sends it to Alloy API.

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

3. Create a `.env` file with:
```
ALLOY_API_KEY=your_api_key
ALLOY_ENDPOINT=your_endpoint_url
BQ_PROJECT_ID=your_project_id
```

## Usage

Run the script:
```bash
python main.py
```
