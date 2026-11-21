
import requests
import json
import time
from pathlib import Path

BASE_URL = "https://dummyjson.com/products"

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_FILE = BASE_DIR / "data" / "raw" / "products.json"

BATCH_SIZE = 30
MAX_RETRIES = 3


def fetch_with_retry(url, params):

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            print(f"API request attempt: {attempt}")

            response = requests.get(
                url,
                params=params,
                timeout=30
            )

            # Retry temporary server errors and rate limits
            if response.status_code == 429 or response.status_code >= 500:
                response.raise_for_status()

            response.raise_for_status()

            return response.json()

        except (requests.Timeout, requests.ConnectionError) as error:

            print(f"Network error: {error}")

        except requests.HTTPError as error:

            status = error.response.status_code

            if status != 429 and status < 500:
                raise

            print(f"Temporary API error: {status}")

        if attempt < MAX_RETRIES:
            wait_time = 2 ** attempt

            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    raise Exception("API extraction failed after maximum retries")


def extract_products():

    all_products = []
    skip = 0
    total = None

    print("Starting product extraction...")

    while total is None or skip < total:

        params = {
            "limit": BATCH_SIZE,
            "skip": skip
        }

        data = fetch_with_retry(BASE_URL, params)

        products = data["products"]
        total = data["total"]

        if not products:
            break

        all_products.extend(products)

        print(
            f"Fetched {len(products)} records. "
            f"Total: {len(all_products)} / {total}"
        )

        skip += len(products)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w") as file:
        json.dump(all_products, file, indent=4)

    print("Extraction completed!")
    print("Total products:", len(all_products))


if __name__ == "__main__":
    extract_products()
