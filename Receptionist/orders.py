
from Database_.connection import get_connection


def get_employee_dashboard_stats():
    """Return today's order count, available table count and open order count."""
    connection = get_connection()
    cursor = None
    try:
        connection.commit()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM orders
                    WHERE DATE(order_date) = CURRENT_DATE()
                ) AS todays_bookings,
                (
                    SELECT COUNT(*)
                    FROM cafe_tables
                    WHERE table_status = 'available'
                ) AS available_tables,
                (
                    SELECT COUNT(*)
                    FROM orders
                    WHERE order_status NOT IN ('completed', 'cancelled')
                ) AS open_orders
            """
        )
        stats = cursor.fetchone()
        connection.commit()
        if stats is None:
            raise RuntimeError("Could not load employee workspace statistics.")
        return stats
    finally:
        if cursor is not None:
            cursor.close()


def get_active_orders():
    """Return active orders with their customer, service, and item details."""
    connection = get_connection()
    cursor = None
    try:
        connection.commit()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                o.order_id,
                o.order_date,
                o.order_status,
                o.order_type,
                o.total_amount,
                c.customer_name,
                c.phone AS customer_phone,
                e.employee_name,
                t.table_number,
                COALESCE(mi.item_name, CONCAT('Item #', oi.item_id)) AS item_name,
                oi.quantity,
                oi.unit_price
            FROM orders AS o
            LEFT JOIN customers AS c ON c.customer_id = o.customer_id
            LEFT JOIN employees AS e ON e.employee_id = o.employee_id
            LEFT JOIN cafe_tables AS t ON t.table_id = o.table_id
            LEFT JOIN order_items AS oi ON oi.order_id = o.order_id
            LEFT JOIN menu_items AS mi ON mi.item_id = oi.item_id
            WHERE o.order_status NOT IN ('completed', 'cancelled')
            ORDER BY o.order_date DESC, o.order_id DESC
            """
        )
        rows = cursor.fetchall()
        connection.commit()
    finally:
        if cursor is not None:
            cursor.close()

    orders_by_id = {}
    for row in rows:
        order_id = row["order_id"]
        if order_id not in orders_by_id:
            orders_by_id[order_id] = {
                "order_id": order_id,
                "order_date": row["order_date"],
                "order_status": row["order_status"],
                "order_type": row["order_type"],
                "total_amount": row["total_amount"],
                "customer_name": row["customer_name"],
                "customer_phone": row["customer_phone"],
                "employee_name": row["employee_name"],
                "table_number": row["table_number"],
                "items": [],
            }
        if row["item_name"] is not None:
            orders_by_id[order_id]["items"].append(
                {
                    "item_name": row["item_name"],
                    "quantity": row["quantity"],
                    "unit_price": row["unit_price"],
                }
            )
    return list(orders_by_id.values())


def get_available_cafe_tables():
    """Return available café tables for dine-in orders."""
    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT table_id, table_number, capacity
            FROM cafe_tables
            WHERE table_status = 'available'
            ORDER BY table_number
            """
        )
        rows = cursor.fetchall()
        connection.commit()
        return rows
    finally:
        cursor.close()


def get_active_employees():
    """Return employee IDs and names for active employees."""
    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT employee_id, employee_name
            FROM employees
            WHERE is_active = 1
            ORDER BY employee_id
            """,
        )
        rows = cursor.fetchall()
        connection.commit()
        return rows
    finally:
        cursor.close()


def get_available_menu_items():
    """Return all currently available menu items."""
    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT item_id, item_name, description, price
            FROM menu_items
            WHERE is_available = 1
            ORDER BY item_id
        """

        cursor.execute(query)
        rows = cursor.fetchall()
        connection.commit()
        return rows

    finally:
        cursor.close()


def save_order(customer, employee_id, order_type, cart, payment_method, table_id=None):
    """Save a paid order and any new customer/table changes atomically."""
    if not cart:
        raise ValueError("Cannot save an order with no items.")

    if order_type not in ("dine_in", "takeaway"):
        raise ValueError("Order type must be 'dine_in' or 'takeaway'.")

    if (order_type == "dine_in") != (table_id is not None):
        raise ValueError("Dine-in orders require a table; takeaway orders must not have one.")

    if payment_method not in ("cash", "upi", "card"):
        raise ValueError("Payment method must be 'cash', 'upi', or 'card'.")

    bill_items, total = calculate_bill(cart)
    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor()

        customer_id = customer.get("customer_id")
        if customer_id is None:
            cursor.execute(
                """
                INSERT INTO customers (customer_name, phone, email)
                VALUES (%s, %s, %s)
                """,
                (
                    customer["customer_name"],
                    customer["phone"],
                    customer["email"],
                ),
            )
            customer_id = cursor.lastrowid

        cursor.execute(
            """
            SELECT employee_id
            FROM employees
            WHERE employee_id = %s AND is_active = 1
            LIMIT 1
            """,
            (employee_id,),
        )
        if cursor.fetchone() is None:
            raise ValueError(f"Employee {employee_id} does not exist or is inactive.")

        if table_id is not None:
            cursor.execute(
                """
                UPDATE cafe_tables
                SET table_status = 'occupied'
                WHERE table_id = %s AND table_status = 'available'
                """,
                (table_id,),
            )
            if cursor.rowcount != 1:
                raise ValueError(
                    f"Table {table_id} is unavailable. Select another table."
                )

        cursor.execute(
            """
            INSERT INTO orders
                (customer_id, employee_id, table_id, order_type,
                 order_date, order_status, total_amount)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s)
            """,
            (
                customer_id,
                employee_id,
                table_id,
                order_type,
                "pending",
                total,
            ),
        )
        order_id = cursor.lastrowid

        cursor.executemany(
            """
            INSERT INTO order_items
                (order_id, item_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
            """,
            [
                (
                    order_id,
                    item["item_id"],
                    item["quantity"],
                    item["price"],
                )
                for item in bill_items
            ],
        )

        cursor.execute(
            """
            INSERT INTO payments
                (order_id, payment_method, amount, payment_status, payment_date)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (order_id, payment_method, total, "completed"),
        )

        connection.commit()
        return order_id
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()


def display_menu(menu_items):
    """Display menu items in a formatted table."""
    if not menu_items:
        print("\nNo menu items are currently available.")
        return

    print("\n" + "=" * 65)
    print(f"{'ID':<6}{'ITEM NAME':<30}{'PRICE (INR)':>14}")
    print("-" * 65)

    for item in menu_items:
        print(
            f"{item['item_id']:<6}"
            f"{item['item_name'][:28]:<30}"
            f"{item['price']:>14.2f}"
        )

    print("=" * 65)


def get_item_by_id(item_id, menu_items):
    """Find an available item by its ID."""
    for item in menu_items:
        if item["item_id"] == item_id:
            return item

    return None


def build_order(menu_items):
    """Collect order items until the receptionist enters 'next'."""
    cart = []

    if not menu_items:
        return cart

    display_menu(menu_items)

    while True:
        choice = input(
            "\nEnter item ID or type 'next' to finish: "
        ).strip()

        if choice.lower() == "next":
            break

        try:
            item_id = int(choice)
        except ValueError:
            print("Invalid input. Enter a valid item ID or 'next'.")
            continue

        item = get_item_by_id(item_id, menu_items)

        if item is None:
            print("Invalid item ID or item is unavailable.")
            continue

        while True:
            quantity_input = input("Enter quantity: ").strip()

            try:
                quantity = int(quantity_input)

                if quantity > 0:
                    break

                print("Quantity must be greater than zero.")

            except ValueError:
                print("Please enter a valid whole number.")

        cart.append({
            "item_id": item["item_id"],
            "item_name": item["item_name"],
            "price": item["price"],
            "quantity": quantity,
        })

        print(
            f"Added {item['item_name']} x {quantity} "
            f"to the cart."
        )

    return cart


def calculate_bill(cart):
    """Calculate each line total and the overall total."""
    bill_items = []
    total = 0

    for item in cart:
        line_total = item["price"] * item["quantity"]
        total += line_total

        bill_items.append({
            **item,
            "line_total": line_total,
        })

    return bill_items, total


def display_bill(cart, order_id=None):
    """Display the final bill."""
    if not cart:
        print("\nCannot generate a bill for an empty cart.")
        return

    bill_items, total = calculate_bill(cart)

    print("\n" + "=" * 65)
    print("                    MAYURI CAFE BILL")
    if order_id is not None:
        print(f"Order ID: {order_id}")
    print("=" * 65)
    print(f"{'ITEM':<28}{'QTY':>7}{'PRICE':>12}{'AMOUNT':>14}")
    print("-" * 65)

    for item in bill_items:
        print(
            f"{item['item_name'][:26]:<28}"
            f"{item['quantity']:>7}"
            f"{item['price']:>12.2f}"
            f"{item['line_total']:>14.2f}"
        )

    print("-" * 65)
    print(f"{'TOTAL':>47}{total:>14.2f}")
    print("=" * 65)
