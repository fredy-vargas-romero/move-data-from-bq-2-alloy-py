import logging
import os
from sqlalchemy import text
from flask import Flask, jsonify, request
from datetime import datetime
import json
from .bigquery_client import BigQueryClient
from .alloydb_client import AlloyDBClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
ALLOYDB_URI = os.environ.get("DB_HOST")
ALLOYDB_USER = os.environ.get("DB_USER")
ALLOYDB_PASSWORD = os.environ.get("DB_PASSWORD")
ALLOYDB_DATABASE = os.environ.get("DB_NAME", "sample_db")

# Add validation for required environment variables
if not all([ALLOYDB_URI, ALLOYDB_USER, ALLOYDB_PASSWORD]):
    raise ValueError(
        "Missing required environment variables: DB_HOST, DB_USER, DB_PASSWORD"
    )


def get_alloy_client():
    """Get or create AlloyDB client"""
    client = AlloyDBClient(
        instance_uri=ALLOYDB_URI,
        user=ALLOYDB_USER,
        password=ALLOYDB_PASSWORD,
        database=ALLOYDB_DATABASE,
    )
    client.connect()
    return client


def get_bq_client():
    """Get or create BigQuery client"""
    client = BigQueryClient(project_id="nodal-cogency-451902-e0")
    client.connect()
    return client


@app.before_request
def log_request_info():
    logger.info(f"Request Method: {request.method}")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Request Headers: {dict(request.headers)}")


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


@app.route("/health", methods=["GET"])
def health_check():
    logger.info("Health check endpoint called")
    return jsonify({"status": "healthy"}), 200


@app.route("/users", methods=["GET"])
def get_users():
    alloy_client = None
    try:
        alloy_client = get_alloy_client()
        query = alloy_client.load_query_from_file("get_all_users.sql")
        with alloy_client.get_connection() as conn:
            result = conn.execute(text(query))
            logger.info(
                "Query executed successfully returning results",
                extra={"result": result},
            )
            users = []
            for row in result:
                user_dict = {
                    "id": row.id,
                    "name": row.name,
                    "email": row.email,
                    "created_at": row.created_at,
                }
                users.append(user_dict)
            logger.info(f"Retrieved {len(users)} users")
            return (
                json.dumps(users, cls=DateTimeEncoder),
                200,
                {"Content-Type": "application/json"},
            )
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        return jsonify({"error": "Failed to retrieve users"}), 500
    finally:
        if alloy_client:
            alloy_client.close()


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    alloy_client = None
    try:
        alloy_client = get_alloy_client()
        query = alloy_client.load_query_from_file("get_user_by_id.sql")
        with alloy_client.get_connection() as conn:
            result = conn.execute(text(query), {"user_id": user_id})
            user = result.fetchone()
            if user is None:
                return jsonify({"error": "User not found"}), 404

            user_dict = {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at,
            }

            logger.info(f"Retrieved user {user_id}")
            return (
                json.dumps(user_dict, cls=DateTimeEncoder),
                200,
                {"Content-Type": "application/json"},
            )
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {str(e)}")
        return jsonify({"error": "Failed to retrieve user"}), 500
    finally:
        if alloy_client:
            alloy_client.close()


@app.route("/customers", methods=["GET"])
def get_customers():
    bq_client = None
    try:
        bq_client = get_bq_client()
        customers = bq_client.read_query_from_file("get_customers.sql")
        logger.info(f"Retrieved {len(customers)} customers from BigQuery")
        return jsonify({"count": len(customers), "customers": customers}), 200
    except Exception as e:
        logger.error(f"Error retrieving customers from BigQuery: {str(e)}")
        return jsonify({"error": "Failed to retrieve customers"}), 500
    finally:
        if bq_client:
            bq_client.close()


@app.route("/transfer/customers", methods=["POST"])
def transfer_customers():
    alloy_client = None
    bq_client = None
    try:
        alloy_client = get_alloy_client()
        bq_client = get_bq_client()

        # First, ensure the customers table exists
        alloy_client.execute_schema_file("create_customers_table.sql")

        # Get data from BigQuery
        customers = bq_client.read_query_from_file("get_customers.sql")
        logger.info(f"Retrieved {len(customers)} customers from BigQuery")

        if not customers:
            return jsonify({"message": "No customers found to transfer"}), 200

        # Write to AlloyDB
        rows_affected = alloy_client.write_data("customers", customers)

        return (
            jsonify(
                {
                    "message": "Transfer completed successfully",
                    "records_transferred": rows_affected,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error transferring customers data: {str(e)}")
        return jsonify({"error": "Failed to transfer customers data"}), 500
    finally:
        if alloy_client:
            alloy_client.close()
        if bq_client:
            bq_client.close()


@app.errorhandler(500)
def handle_500(e):
    logger.error(f"Internal Server Error: {str(e)}")
    return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting application on port {port}")
    app.run(host="0.0.0.0", port=port)
