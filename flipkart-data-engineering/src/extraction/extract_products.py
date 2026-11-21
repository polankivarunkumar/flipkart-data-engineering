
import requests
import json
import time
from pathlib import Path

from src.utils.logger import get_logger


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_URL = "https://dummyjson.com/products"

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_FILE = BASE_DIR / "data" / "raw" / "products.json"

BATCH_SIZE = 30

MAX_RETRIES = 3

logger = get_logger("ProductExtraction")


# --------------------------------------------------
# API REQUEST WITH RETRY
# --------------------------------------------------

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

            logger.warning(
                f"Temporary API error: HTTP {status}"
            )

        if attempt < MAX_RETRIES:

            wait_time = 2 ** attempt

            logger.info(
                f"Retrying after {wait_time} seconds"
            )

            time.sleep(wait_time)

    raise Exception(
        "API request failed after maximum retries"
    )


# --------------------------------------------------
# PRODUCT DATA EXTRACTION
# --------------------------------------------------

def extract_products():

    all_products = []

    skip = 0

    total = None

    logger.info("Product extraction started")

    while total is None or skip < total:

        params = {
            "limit": BATCH_SIZE,
            "skip": skip
        }

        data = fetch_with_retry(
            BASE_URL,
            params
        )

        products = data["products"]

        total = data["total"]

        if not products:

            logger.warning("No more products available")

            break

        all_products.extend(products)

        logger.info(
            f"Fetched {len(products)} products. "
            f"Total collected: {len(all_products)} / {total}"
        )

        skip += len(products)

    # --------------------------------------------------
    # SAVE DATA
    # --------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(OUTPUT_FILE, "w") as file:

        json.dump(
            all_products,
            file,
            indent=4
        )

    logger.info("Product extraction completed")

    logger.info(
        f"Total products extracted: {len(all_products)}"
    )

    logger.info(
        f"Output file: {OUTPUT_FILE}"
    )


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

if __name__ == "__main__":

    try:

        extract_products()

    except Exception:

        logger.exception(
            "Product extraction pipeline failed"
        )

        raise
