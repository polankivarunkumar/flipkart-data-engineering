
import requests
import json
import time
from pathlib import Path

from src.utils.logger import get_logger


# Configuration
BASE_URL = "https://dummyjson.com/users"

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_FILE = BASE_DIR / "data" / "raw" / "customers.json"

BATCH_SIZE = 30
MAX_RETRIES = 3

logger = get_logger("CustomerExtraction")


def fetch_with_retry(url, params):

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            logger.info(f"API request attempt: {attempt}")

            response = requests.get(
                url,
                params=params,
                timeout=30
            )

            response.raise_for_status()

            return response.json()

        except (requests.Timeout, requests.ConnectionError):

            logger.exception("Network error occurred")

        except requests.HTTPError as error:

            status = error.response.status_code

            if status != 429 and status < 500:
                raise

            logger.warning(f"Temporary HTTP error: {status}")

        if attempt < MAX_RETRIES:

            wait_time = 2 ** attempt

            logger.info(f"Retrying after {wait_time} seconds")

            time.sleep(wait_time)

    raise Exception("Customer API failed after maximum retries")


def extract_customers():

    all_customers = []

    skip = 0
    total = None

    logger.info("Customer extraction started")

    while total is None or skip < total:

        params = {
            "limit": BATCH_SIZE,
            "skip": skip
        }

        data = fetch_with_retry(BASE_URL, params)

        customers = data["users"]
        total = data["total"]

        if not customers:
            break

        all_customers.extend(customers)

        logger.info(
            f"Fetched {len(customers)} customers. "
            f"Total: {len(all_customers)} / {total}"
        )

        skip += len(customers)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w") as file:

        json.dump(all_customers, file, indent=4)

    logger.info("Customer extraction completed")

    logger.info(f"Total customers: {len(all_customers)}")

    logger.info(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":

    try:
        extract_customers()

    except Exception:
        logger.exception("Customer extraction pipeline failed")
        raise
