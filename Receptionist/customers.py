
from Database_.connection import get_connection


def get_customer_by_phone(phone):
    """Return a customer record if the phone number exists."""
    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT customer_id, customer_name, phone, email
            FROM customers
            WHERE phone = %s
            LIMIT 1
        """

        cursor.execute(query, (phone,))
        customer = cursor.fetchone()

        return customer

    finally:
        cursor.close()
        connection.close()


def add_customer(customer_name, phone, email):
    """Insert a new customer and return the inserted customer record."""
    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        query = """
            INSERT INTO customers (customer_name, phone, email)
            VALUES (%s, %s, %s)
        """

        cursor.execute(query, (customer_name, phone, email))
        connection.commit()

        customer_id = cursor.lastrowid

        cursor.execute(
            """
            SELECT customer_id, customer_name, phone, email
            FROM customers
            WHERE customer_id = %s
            """,
            (customer_id,)
        )

        return cursor.fetchone()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_customer_or_registration_details(phone):
    """Find a customer or collect details without persisting a new one."""
    customer = get_customer_by_phone(phone)

    if customer:
        print(f"\nWelcome back, {customer['customer_name']}!")
        return customer

    print("\nNew customer! Let's register you.")

    while True:
        customer_name = input("Enter customer name: ").strip()

        if customer_name:
            break

        print("Name cannot be empty. Please try again.")

    email = input("Enter email (press Enter to skip): ").strip() or None

    return {
        "customer_name": customer_name,
        "phone": phone,
        "email": email,
    }


def get_or_create_customer(phone):
    """Find a customer or register them immediately."""
    customer = get_customer_or_registration_details(phone)
    if customer.get("customer_id") is not None:
        return customer

    customer = add_customer(
        customer["customer_name"],
        customer["phone"],
        customer["email"],
    )
    print("\nCustomer registered successfully!")
    print(f"Customer ID: {customer['customer_id']}")
    return customer
