"""ETL configuration: database connection and constants."""

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dearth:dearth_pass@localhost:5432/dearth_map",
)

# Parse DATABASE_URL into components for psycopg2
def get_db_params() -> dict:
    """Parse DATABASE_URL into psycopg2 connection parameters."""
    url = DATABASE_URL
    # postgresql://user:pass@host:port/dbname
    url = url.replace("postgresql://", "")
    userpass, hostdb = url.split("@", 1)
    user, password = userpass.split(":", 1)
    hostport, dbname = hostdb.split("/", 1)
    if ":" in hostport:
        host, port = hostport.split(":", 1)
    else:
        host = hostport
        port = "5432"
    return {
        "dbname": dbname,
        "user": user,
        "password": password,
        "host": host,
        "port": int(port),
    }

# Dearth score weights
WEIGHT_DENSITY = 0.4
WEIGHT_DISTANCE = 0.3
WEIGHT_DRIVETIME = 0.2
WEIGHT_WAITTIME = 0.1

# Default proxy values for MVP
DRIVETIME_FACTOR = 1.5  # minutes = 1.5 * distance_miles
DEFAULT_WAITTIME_SCORE = 50.0

# Dearth label thresholds
DEARTH_LABELS = [
    (20, "Well Served"),
    (40, "Adequate"),
    (60, "Moderate Shortage"),
    (80, "Significant Shortage"),
    (100, "Severe Shortage"),
]

STATES = ["CA", "TX", "NY", "MS", "MT"]
