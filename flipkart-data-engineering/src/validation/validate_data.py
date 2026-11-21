
import json
from pathlib import Path

from src.utils.logger import get_logger


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"

logger = get_logger("DataValidation")


# --------------------------------------------------
# LOAD JSON DATA
# --------------------------------------------------

def load_json(filename):

    file_path = RAW_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    with open(file_path, "r") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            f"{filename} must contain a JSON array"
        )

    logger.info(
        f"Loaded {len(data)} records from {filename}"
    )

    return data


# --------------------------------------------------
# DUPLICATE CHECK
# --------------------------------------------------

def check_duplicates(records, id_field, dataset_name):

    ids = [record.get(id_field) for record in records]

    valid_ids = [
        value for value in ids
        if value is not None
    ]

    duplicate_count = (
        len(valid_ids) - len(set(valid_ids))
    )

    if duplicate_count > 0:

        logger.error(
            f"{dataset_name}: {duplicate_count} duplicate IDs"
        )

        return False

    logger.info(
        f"{dataset_name}: Duplicate check PASSED"
    )

    return True


# --------------------------------------------------
# REQUIRED FIELD CHECK
# --------------------------------------------------

def check_required_fields(records, fields, dataset_name):

    valid = True

    for index, record in enumerate(records):

        if not isinstance(record, dict):

            logger.error(
                f"{dataset_name}: Record {index} is not an object"
            )

            valid = False
            continue

        for field in fields:

            value = record.get(field)

            if value is None or value == "":

                logger.error(
                    f"{dataset_name}: Record {index}: "
                    f"Required field {field} is missing"
                )

                valid = False

    return valid


# --------------------------------------------------
# POSITIVE NUMBER CHECK
# --------------------------------------------------

def check_positive(records, field, dataset_name):

    valid = True

    for record in records:

        value = record.get(field)

        try:

            if value is None or float(value) <= 0:
                raise ValueError()

        except (ValueError, TypeError):

            logger.error(
                f"{dataset_name}: Invalid {field} "
                f"in record {record}"
            )

            valid = False

    return valid


# --------------------------------------------------
# PRODUCT VALIDATION
# --------------------------------------------------

def validate_products(products):

    logger.info("Validating products")

    results = [

        check_duplicates(
            products, "id", "Products"
        ),

        check_required_fields(
            products,
            ["id", "title", "category", "price"],
            "Products"
        ),

        check_positive(
            products, "price", "Products"
        )

    ]

    return all(results)


# --------------------------------------------------
# CUSTOMER VALIDATION
# --------------------------------------------------

def validate_customers(customers):

    logger.info("Validating customers")

    valid = True

    valid &= check_duplicates(
        customers, "id", "Customers"
    )

    # Only mandatory fields are checked.
    # maidenName and other optional fields are allowed to be empty.

    required_fields = [
        "id",
        "firstName",
        "lastName",
        "email"
    ]

    valid &= check_required_fields(
        customers,
        required_fields,
        "Customers"
    )

    for customer in customers:

        email = customer.get("email")

        if isinstance(email, str):

            if (
                "@" not in email
                or "." not in email.split("@")[-1]
            ):

                logger.error(
                    f"Invalid email for customer ID: "
                    f"{customer.get('id')}"
                )

                valid = False

    if valid:

        logger.info("Customer validation PASSED")

    return bool(valid)


# --------------------------------------------------
# ORDER VALIDATION
# --------------------------------------------------

def validate_orders(orders, customers):

    logger.info("Validating orders")

    valid = True

    valid &= check_duplicates(
        orders, "order_id", "Orders"
    )

    valid &= check_required_fields(
        orders,
        [
            "order_id",
            "customer_id",
            "order_date",
            "order_status",
            "total_amount"
        ],
        "Orders"
    )

    customer_ids = {
        customer["id"]
        for customer in customers
        if customer.get("id") is not None
    }

    for order in orders:

        if order.get("customer_id") not in customer_ids:

            logger.error(
                f"Order {order.get('order_id')} "
                f"has invalid customer ID "
                f"{order.get('customer_id')}"
            )

            valid = False

        try:

            if float(order.get("total_amount", 0)) <= 0:

                logger.error(
                    f"Invalid order amount: "
                    f"{order.get('order_id')}"
                )

                valid = False

        except (ValueError, TypeError):

            logger.error(
                f"Invalid order amount: "
                f"{order.get('order_id')}"
            )

            valid = False

    return bool(valid)


# --------------------------------------------------
# ORDER ITEM VALIDATION
# --------------------------------------------------

def validate_order_items(order_items, orders, products):

    logger.info("Validating order items")

    valid = True

    order_ids = {
        order["order_id"]
        for order in orders
        if order.get("order_id") is not None
    }

    product_ids = {
        product["id"]
        for product in products
        if product.get("id") is not None
    }

    valid &= check_required_fields(
        order_items,
        [
            "order_id",
            "product_id",
            "quantity",
            "unit_price",
            "item_total"
        ],
        "Order Items"
    )

    for item in order_items:

        if item.get("order_id") not in order_ids:

            logger.error(
                f"Invalid order ID: {item.get('order_id')}"
            )

            valid = False

        if item.get("product_id") not in product_ids:

            logger.error(
                f"Invalid product ID: {item.get('product_id')}"
            )

            valid = False

        try:

            if int(item.get("quantity", 0)) <= 0:
                raise ValueError()

            if float(item.get("unit_price", 0)) <= 0:
                raise ValueError()

            if float(item.get("item_total", 0)) <= 0:
                raise ValueError()

        except (ValueError, TypeError):

            logger.error(
                f"Invalid order item values: {item}"
            )

            valid = False

    return bool(valid)


# --------------------------------------------------
# PAYMENT VALIDATION
# --------------------------------------------------

def validate_payments(payments, orders):

    logger.info("Validating payments")

    valid = True

    valid &= check_duplicates(
        payments, "payment_id", "Payments"
    )

    valid &= check_required_fields(
        payments,
        [
            "payment_id",
            "order_id",
            "payment_date",
            "payment_method",
            "payment_status",
            "payment_amount"
        ],
        "Payments"
    )

    order_ids = {
        order["order_id"]
        for order in orders
        if order.get("order_id") is not None
    }

    for payment in payments:

        if payment.get("order_id") not in order_ids:

            logger.error(
                f"Payment {payment.get('payment_id')} "
                f"references invalid order"
            )

            valid = False

        try:

            if float(payment.get("payment_amount", 0)) <= 0:
                raise ValueError()

        except (ValueError, TypeError):

            logger.error(
                f"Invalid payment amount: "
                f"{payment.get('payment_id')}"
            )

            valid = False

    return bool(valid)


# --------------------------------------------------
# MAIN VALIDATION PIPELINE
# --------------------------------------------------

def validate_all_datasets():

    logger.info("=" * 50)
    logger.info("DATA QUALITY VALIDATION STARTED")
    logger.info("=" * 50)

    products = load_json("products.json")
    customers = load_json("customers.json")
    orders = load_json("orders.json")
    order_items = load_json("order_items.json")
    payments = load_json("payments.json")

    results = {

        "Products": validate_products(products),

        "Customers": validate_customers(customers),

        "Orders": validate_orders(orders, customers),

        "Order Items": validate_order_items(
            order_items,
            orders,
            products
        ),

        "Payments": validate_payments(
            payments,
            orders
        )

    }

    # --------------------------------------------------
    # VALIDATION SUMMARY
    # --------------------------------------------------

    logger.info("=" * 50)
    logger.info("DATA QUALITY VALIDATION SUMMARY")
    logger.info("=" * 50)

    for dataset, status in results.items():

        result = "PASSED" if status else "FAILED"

        logger.info(
            f"{dataset}: {result}"
        )

    passed = sum(results.values())

    failed = len(results) - passed

    logger.info(f"Total datasets: {len(results)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")

    if failed > 0:

        failed_datasets = [
            name
            for name, status in results.items()
            if not status
        ]

        logger.error(
            f"Failed datasets: {failed_datasets}"
        )

        raise ValueError(
            "Data quality validation failed"
        )

    logger.info("ALL DATASETS PASSED VALIDATION")


# --------------------------------------------------
# EXECUTION
# --------------------------------------------------

if __name__ == "__main__":

    try:

        validate_all_datasets()

    except Exception:

        logger.exception(
            "Data validation pipeline failed"
        )

        raise
