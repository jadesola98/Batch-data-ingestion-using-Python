"""
NYC taxi batch ingestion: download monthly trip files and load them into PostgreSQL.

Each month is loaded in chunks inside one transaction. Before loading, any rows
already loaded for that month are deleted, so re-running a month replaces it
instead of duplicating it. Every run is recorded in an ingestion_runs table.

Configuration comes from environment variables (see .env.example).
Usage:
    python ingest_data.py --taxi yellow --year 2021 --months 1 2 3
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATA_URL = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{taxi}/{taxi}_tripdata_{year}-{month:02d}.csv.gz"

# Pickup and dropoff column names differ between yellow and green taxi files
DATETIME_COLUMNS = {
    "yellow": ["tpep_pickup_datetime", "tpep_dropoff_datetime"],
    "green": ["lpep_pickup_datetime", "lpep_dropoff_datetime"],
}

# Explicit types stop pandas guessing differently from one chunk to the next
DTYPES = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "RatecodeID": "Int64",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "trip_type": "Int64",
    "store_and_fwd_flag": "string",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def get_engine():
    """Build the database connection from environment variables."""
    url = os.getenv("DATABASE_URL")
    if not url:
        url = (
            f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
            f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}"
            f"/{os.environ['POSTGRES_DB']}"
        )
    return create_engine(url)


def create_run_log(engine):
    """Create the table that records every ingestion run, if it doesn't exist."""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ingestion_runs (
                taxi        VARCHAR(10),
                source_month VARCHAR(7),
                rows_loaded BIGINT,
                status      VARCHAR(10),
                error       TEXT,
                started_at  TIMESTAMP,
                finished_at TIMESTAMP
            )
        """))


def log_run(engine, taxi, month_key, rows, status, error, started_at):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO ingestion_runs
                    (taxi, source_month, rows_loaded, status, error, started_at, finished_at)
                VALUES (:taxi, :month, :rows, :status, :error, :started, CURRENT_TIMESTAMP)
            """),
            {"taxi": taxi, "month": month_key, "rows": rows, "status": status,
             "error": error, "started": started_at},
        )


def table_exists(conn, table):
    return conn.dialect.has_table(conn, table)


def load_month(engine, taxi, year, month, chunksize):
    """Load one month of trips. Returns the number of rows loaded."""
    table = f"{taxi}_taxi_trips"
    month_key = f"{year}-{month:02d}"
    url = DATA_URL.format(taxi=taxi, year=year, month=month)
    logger.info(f"Loading {month_key} from {url}")

    chunks = pd.read_csv(
        url,
        dtype=DTYPES,
        parse_dates=DATETIME_COLUMNS[taxi],
        iterator=True,
        chunksize=chunksize,
    )

    total_rows = 0
    # One transaction per month: either the whole month lands, or none of it does
    with engine.begin() as conn:
        if table_exists(conn, table):
            deleted = conn.execute(
                text(f"DELETE FROM {table} WHERE source_month = :month"),
                {"month": month_key},
            ).rowcount
            if deleted:
                logger.info(f"Removed {deleted:,} rows previously loaded for {month_key}")

        for i, chunk in enumerate(chunks, start=1):
            started = time.time()
            chunk["source_month"] = month_key
            chunk.to_sql(table, conn, if_exists="append", index=False)
            total_rows += len(chunk)
            logger.info(f"  chunk {i}: {len(chunk):,} rows in {time.time() - started:.1f}s")

        # Index the month column so the delete above stays fast as months accumulate
        conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{table}_source_month ON {table} (source_month)"))

    logger.info(f"Finished {month_key}: {total_rows:,} rows loaded into {table}")
    return total_rows


def main():
    parser = argparse.ArgumentParser(description="Load NYC taxi trips into PostgreSQL")
    parser.add_argument("--taxi", choices=["yellow", "green"], default=os.getenv("TAXI", "yellow"))
    parser.add_argument("--year", type=int, default=int(os.getenv("YEAR", "2021")))
    parser.add_argument("--months", type=int, nargs="+",
                        default=[int(m) for m in os.getenv("MONTHS", "1").split()])
    parser.add_argument("--chunksize", type=int, default=int(os.getenv("CHUNKSIZE", "100000")))
    args = parser.parse_args()

    engine = get_engine()
    create_run_log(engine)

    failures = 0
    for month in args.months:
        month_key = f"{args.year}-{month:02d}"
        started_at = datetime.now()
        try:
            rows = load_month(engine, args.taxi, args.year, month, args.chunksize)
            log_run(engine, args.taxi, month_key, rows, "success", None, started_at)
        except Exception as e:
            failures += 1
            logger.error(f"Failed to load {month_key}: {e}")
            log_run(engine, args.taxi, month_key, 0, "failed", str(e)[:1000], started_at)

    if failures:
        logger.error(f"{failures} of {len(args.months)} months failed")
        sys.exit(1)
    logger.info("All months loaded successfully")


if __name__ == "__main__":
    main()
