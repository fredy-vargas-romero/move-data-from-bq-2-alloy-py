import logging
from google.cloud import bigquery
from typing import List, Dict, Any
from google.api_core import retry
import os

logger = logging.getLogger(__name__)


class BigQueryClient:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.dataset = "my_dataset"  # Add dataset name
        self.client = None

    def connect(self):
        """Initialize BigQuery connection"""
        try:
            logger.info(f"Connecting to BigQuery project: {self.project_id}")
            self.client = bigquery.Client(project=self.project_id)
            logger.info("BigQuery connection established")
        except Exception as e:
            logger.error(f"Failed to connect to BigQuery: {str(e)}")
            raise

    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def read_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute query and return results"""
        try:
            if not self.client:
                self.connect()

            logger.info("Executing BigQuery query")
            logger.debug(f"Query: {query}")
            query_job = self.client.query(query)
            results = query_job.result()

            data = [dict(row.items()) for row in results]
            logger.info(f"Retrieved {len(data)} records from BigQuery")
            return data

        except Exception as e:
            logger.error(f"Error executing BigQuery query: {str(e)}")
            raise

    def load_query_from_file(self, filename: str) -> str:
        """Load query from SQL file"""
        try:
            query_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "sql", "bigquery", filename
            )
            logger.info(f"Loading query from {query_path}")

            with open(query_path, "r") as file:
                query = file.read()

            return query
        except Exception as e:
            logger.error(f"Error loading query file {filename}: {str(e)}")
            raise

    def read_query_from_file(self, filename: str) -> List[Dict[str, Any]]:
        """Load and execute query from file"""
        query = self.load_query_from_file(filename)
        return self.read_query(query)

    def close(self):
        """Close BigQuery connection"""
        try:
            if self.client:
                self.client.close()
                logger.info("BigQuery connection closed")
        except Exception as e:
            logger.error(f"Error closing BigQuery connection: {str(e)}")
