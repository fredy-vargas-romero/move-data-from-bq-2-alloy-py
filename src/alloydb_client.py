import logging
import sqlalchemy
from sqlalchemy import text
from google.cloud.alloydb.connector import Connector
from typing import List, Dict, Any, Tuple
from contextlib import contextmanager
import os
import socket
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class AlloyDBClient:
    def __init__(self, instance_uri: str, user: str, password: str, database: str):
        self.instance_uri = instance_uri
        self.user = user
        self.password = password
        self.database = database
        self.engine = None
        self.connector = None
        self.max_retries = 3
        self.retry_delay = 1

    def create_sqlalchemy_engine(self) -> Tuple[sqlalchemy.engine.Engine, Connector]:
        """Create SQLAlchemy engine and connector"""
        try:
            logger.info("Attempting to create database connector...")
            connector = Connector()
            logger.info("Connector created successfully")

            def getconn():
                try:
                    logger.info(
                        f"Attempting to connect to database at {self.instance_uri}"
                    )
                    logger.info(
                        f"Connection details - User: {self.user}, DB: {self.database}, URI: {self.instance_uri}"
                    )

                    conn = connector.connect(
                        self.instance_uri,
                        "pg8000",
                        user=self.user,
                        password=self.password,
                        db=self.database,
                    )
                    logger.info("Database connection established successfully")
                    return conn
                except socket.timeout:
                    logger.error(
                        "Connection timeout occurred while connecting to database"
                    )
                    raise
                except RequestException as e:
                    logger.error(f"HTTP connection error: {str(e)}")
                    raise
                except Exception as e:
                    logger.error(f"Failed to connect to database: {str(e)}")
                    raise

            engine = sqlalchemy.create_engine(
                "postgresql+pg8000://",
                creator=getconn,
                pool_pre_ping=True,
                pool_recycle=300,
            )

            # Verify connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection test successful")

            return engine, connector

        except Exception as e:
            logger.error(f"Failed to create engine/connector: {str(e)}")
            logger.error(f"Connection error details: {type(e).__name__}")
            raise

    def connect(self):
        """Initialize AlloyDB connection"""
        try:
            self.engine, self.connector = self.create_sqlalchemy_engine()
        except Exception as e:
            logger.error(f"Failed to connect to AlloyDB: {str(e)}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        if not self.engine:
            raise Exception("No database connection available. Call connect() first.")

        conn = self.engine.connect()
        try:
            yield conn
        finally:
            if conn:
                conn.close()

    def write_data(self, table_name: str, data: List[Dict[str, Any]]) -> int:
        """Write data to AlloyDB table"""
        if not data:
            logger.warning("No data to insert")
            return 0

        try:
            columns = list(data[0].keys())
            placeholders = [f":{col}" for col in columns]
            insert_query = f"""
                INSERT INTO {table_name} 
                ({', '.join(columns)}) 
                VALUES ({', '.join(placeholders)})
            """

            with self.get_connection() as conn:
                result = conn.execute(text(insert_query), data)
                conn.commit()
                rows_affected = result.rowcount
                logger.info(f"Inserted {rows_affected} rows into {table_name}")
                return rows_affected

        except Exception as e:
            logger.error(f"Error writing data to AlloyDB: {str(e)}")
            raise

    def execute_schema_file(self, filename: str) -> None:
        """Execute schema file for table creation/updates"""
        try:
            schema_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "sql", "alloydb", filename
            )
            logger.info(f"Loading schema from {schema_path}")

            with open(schema_path, "r") as file:
                schema_sql = file.read()

            with self.get_connection() as conn:
                # Split multiple statements and execute each one
                for statement in schema_sql.split(";"):
                    if statement.strip():
                        conn.execute(text(statement))
                conn.commit()
                logger.info(f"Schema file {filename} executed successfully")

        except Exception as e:
            logger.error(f"Error executing schema file {filename}: {str(e)}")
            raise

    def load_query_from_file(self, filename: str) -> str:
        """Load query from SQL file"""
        try:
            query_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "sql", "alloydb", filename
            )
            logger.info(f"Loading query from {query_path}")

            with open(query_path, "r") as file:
                query = file.read()

            return query.strip()
        except Exception as e:
            logger.error(f"Error loading query file {filename}: {str(e)}")
            raise

    def close(self):
        """Close AlloyDB connections"""
        try:
            if self.engine:
                self.engine.dispose()
            if self.connector:
                self.connector.close()
            logger.info("AlloyDB connections closed")
        except Exception as e:
            logger.error(f"Error closing AlloyDB connections: {str(e)}")
