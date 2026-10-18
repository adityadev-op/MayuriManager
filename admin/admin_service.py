from datetime import date

from Database_.connection import get_connection


def get_database_tables():
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
        tables = sorted(row[0] for row in cursor.fetchall())
        connection.commit()
        return tables
    finally:
        if cursor is not None:
            cursor.close()


def get_table_rows(table_name):
    """Fetch all rows from a table returned by get_database_tables."""
    if not isinstance(table_name, str) or not table_name:
        raise ValueError("Choose a database table.")

    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        escaped_name = table_name.replace("`", "``")
        cursor.execute(f"SELECT * FROM `{escaped_name}`")
        rows = cursor.fetchall()
        columns = [entry[0] for entry in cursor.description]
        connection.commit()
        return columns, rows
    finally:
        if cursor is not None:
            cursor.close()


def get_menu_categories():
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT category_id, category_name
            FROM categories
            ORDER BY category_name
            """
        )
        rows = cursor.fetchall()
        connection.commit()
        return rows
    finally:
        if cursor is not None:
            cursor.close()


def create_menu_item(category_id, item_name, description, price, is_available=True):
    name = item_name.strip()
    if not name:
        raise ValueError("Enter a menu item name.")
    if category_id is None:
        raise ValueError("Choose a menu category.")
    if price <= 0:
        raise ValueError("Price must be greater than zero.")

    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO menu_items
                (category_id, item_name, description, price, is_available)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                category_id,
                name,
                description.strip() or None,
                price,
                is_available,
            ),
        )
        item_id = cursor.lastrowid
        connection.commit()
        return item_id
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()


def get_sales_details(start_date: date, end_date: date):
    if start_date > end_date:
        raise ValueError("Start date must be on or before end date.")

    connection = get_connection()
    cursor = None
    try:
        # Start a new read transaction so this refresh sees recently committed sales.
        connection.commit()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                o.order_id,
                o.order_date,
                c.customer_name,
                c.phone AS customer_phone,
                e.employee_name,
                o.order_type,
                COALESCE(mi.item_name, CONCAT('Item #', oi.item_id)) AS item_name,
                oi.quantity,
                oi.unit_price,
                oi.quantity * oi.unit_price AS item_total,
                payment_summary.payment_methods,
                payment_summary.payment_statuses
            FROM orders AS o
            LEFT JOIN customers AS c ON c.customer_id = o.customer_id
            LEFT JOIN employees AS e ON e.employee_id = o.employee_id
            INNER JOIN order_items AS oi ON oi.order_id = o.order_id
            LEFT JOIN menu_items AS mi ON mi.item_id = oi.item_id
            LEFT JOIN (
                SELECT
                    order_id,
                    GROUP_CONCAT(DISTINCT payment_method ORDER BY payment_method) AS payment_methods,
                    GROUP_CONCAT(DISTINCT payment_status ORDER BY payment_status) AS payment_statuses
                FROM payments
                GROUP BY order_id
            ) AS payment_summary ON payment_summary.order_id = o.order_id
            WHERE DATE(o.order_date) BETWEEN %s AND %s
            ORDER BY o.order_date DESC, o.order_id DESC, item_name
            """,
            (start_date, end_date),
        )
        rows = cursor.fetchall()
        connection.commit()
        return rows
    finally:
        if cursor is not None:
            cursor.close()


def get_revenue_by_day(start_date: date, end_date: date):
    if start_date > end_date:
        raise ValueError("Start date must be on or before end date.")

    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                DATE(p.payment_date) AS revenue_date,
                COUNT(DISTINCT p.order_id) AS bill_count,
                SUM(p.amount) AS revenue
            FROM payments AS p
            WHERE p.payment_status = 'completed'
              AND DATE(p.payment_date) BETWEEN %s AND %s
            GROUP BY DATE(p.payment_date)
            ORDER BY revenue_date DESC
            """,
            (start_date, end_date),
        )
        rows = cursor.fetchall()
        connection.commit()
        return rows
    finally:
        if cursor is not None:
            cursor.close()


def get_category_sales(start_date: date, end_date: date):
    if start_date > end_date:
        raise ValueError("Start date must be on or before end date.")

    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                COALESCE(c.category_name, 'Uncategorized') AS category_name,
                COALESCE(SUM(oi.quantity), 0) AS items_sold,
                COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS category_revenue
            FROM orders AS o
            INNER JOIN order_items AS oi ON oi.order_id = o.order_id
            LEFT JOIN menu_items AS mi ON mi.item_id = oi.item_id
            LEFT JOIN categories AS c ON c.category_id = mi.category_id
            WHERE DATE(o.order_date) BETWEEN %s AND %s
              AND o.order_status != 'cancelled'
            GROUP BY c.category_id, c.category_name
            ORDER BY category_revenue DESC, category_name
            """,
            (start_date, end_date),
        )
        rows = cursor.fetchall()
        connection.commit()
        return rows
    finally:
        if cursor is not None:
            cursor.close()


def get_employee_bill_counts(start_date: date, end_date: date):
    if start_date > end_date:
        raise ValueError("Start date must be on or before end date.")

    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                e.employee_id,
                e.employee_name,
                COUNT(DISTINCT o.order_id) AS bill_count,
                COALESCE(SUM(o.total_amount), 0) AS total_billed
            FROM employees AS e
            LEFT JOIN orders AS o
              ON o.employee_id = e.employee_id
             AND DATE(o.order_date) BETWEEN %s AND %s
             AND o.order_status != 'cancelled'
            GROUP BY e.employee_id, e.employee_name
            ORDER BY bill_count DESC, e.employee_name
            """,
            (start_date, end_date),
        )
        rows = cursor.fetchall()
        connection.commit()
        return rows
    finally:
        if cursor is not None:
            cursor.close()
