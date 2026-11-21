
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

from src.utils.logger import get_logger


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"

CUSTOMERS_FILE = RAW_DIR / "customers.json"
PRODUCTS_FILE = RAW_DIR / "products.json"

ORDERS_FILE = RAW_DIR / "orders.json"
ORDER_ITEMS_FILE = RAW_DIR / "order_items.json"
PAYMENTS_FILE = RAW_DIR / "payments.json"

NUMBER_OF_ORDERS = 500

logger = get_logger("OrderGeneration")

random.seed(42)


# --------------------------------------------------
# LOAD EXISTING DATA
# --------------------------------------------------

def load_json(file_path):

    with open(file_path, "r") as file:
        return json.load(file)


# --------------------------------------------------
# GENERATE ORDERS
# --------------------------------------------------

def generate_orders():

    logger.info("Order generation started")

    customers = load_json(CUSTOMERS_FILE)
    products = load_json(PRODUCTS_FILE)

    if not customers or not products:
        raise ValueError("Customers or products data is empty")

    orders = []
    order_items = []
    payments = []

    order_statuses = [
        "delivered",
        "shipped",
        "processing",
        "cancelled",
        "returned"
    ]

    payment_methods = [
        "UPI",
        "Credit Card",
        "Debit Card",
        "Net Banking",
        "Wallet"
    ]

    start_date = datetime.now() - timedelta(days=365)

    for order_id in range(1, NUMBER_OF_ORDERS + 1):

        customer = random.choice(customers)

        order_date = start_date + timedelta(
            days=random.randint(0, 365)
        )

        order_status = random.choice(order_statuses)

        number_of_items = random.randint(1, 3)

        total_amount = 0

        # Generate multiple products per order
        for _ in range(number_of_items):

            product = random.choice(products)

            quantity = random.randint(1, 3)

            unit_price = product["price"]

            item_total = round(
                quantity * unit_price, 2
            )

            total_amount += item_total

            order_items.append({

                "order_id": order_id,
                "product_id": product["id"],
                "product_title": product["title"],
                "quantity": quantity,
                "unit_price": unit_price,
                "item_total": item_total

            })

        total_amount = round(total_amount, 2)

        # Order header
        orders.append({

            "order_id": order_id,
            "customer_id": customer["id"],
            "order_date": order_date.isoformat(),
            "order_status": order_status,
            "total_amount": total_amount

        })

        # Payment status based on order status
        if order_status == "cancelled":
            payment_status = random.choice(["failed", "refunded"])

        elif order_status == "returned":
            payment_status = "refunded"

        else:
            payment_status = random.choice(["paid", "pending"])

        # Payment record
        payments.append({

            "payment_id": order_id,
            "order_id": order_id,
            "payment_date": (
                order_date + timedelta(minutes=random.randint(1, 60))
            ).isoformat(),
            "payment_method": random.choice(payment_methods),
            "payment_status": payment_status,
            "payment_amount": total_amount

        })

    # --------------------------------------------------
    # SAVE DATASETS
    # --------------------------------------------------

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    datasets = {
        ORDERS_FILE: orders,
        ORDER_ITEMS_FILE: order_items,
        PAYMENTS_FILE: payments
    }

    for file_path, records in datasets.items():

        with open(file_path, "w") as file:
            json.dump(records, file, indent=4)

        logger.info(
            f"Generated {len(records)} records: {file_path.name}"
        )

    logger.info("Order generation completed successfully")


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

if __name__ == "__main__":

    try:
        generate_orders()

    except Exception:
        logger.exception("Order generation failed")
        raise
