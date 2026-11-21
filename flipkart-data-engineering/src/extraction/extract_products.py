
import requests
import json
from pathlib import Path

BASE_URL = "https://dummyjson.com/products"

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_FILE = BASE_DIR / "data" / "raw" / "products.json"

BATCH_SIZE = 30


def extract_products():

    all_products = []
    skip = 0
    total = None

    print("Starting paginated extraction...")

    while total is None or skip < total:

        params = {
            "limit": BATCH_SIZE,
            "skip": skip
        }

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        products = data["products"]
        total = data["total"]

        all_products.extend(products)

        print(
            f"Fetched {len(products)} records. "
            f"Total collected: {len(all_products)} / {total}"
        )

        if not products:
            break

        skip += len(products)

    with open(OUTPUT_FILE, "w") as file:
        json.dump(all_products, file, indent=4)

    print("Extraction completed!")
    print("Total products:", len(all_products))


if __name__ == "__main__":
    extract_products()
