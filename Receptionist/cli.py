import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Receptionist.customers import get_customer_or_registration_details
from Receptionist.orders import (
    build_order,
    display_bill,
    get_active_employees,
    get_available_cafe_tables,
    get_available_menu_items,
    save_order,
)


def run_receptionist():
    """Run the customer registration, ordering, and billing workflow."""
    while True:
        phone = input("Enter customer phone number: ").strip()

        if phone:
            break

        print("Phone number cannot be empty. Please try again.")

    customer = get_customer_or_registration_details(phone)

    print(f"\nTaking order for {customer['customer_name']}.")
    menu_items = get_available_menu_items()
    cart = build_order(menu_items)

    if not cart:
        print("No order was saved because the cart is empty.")
        return

    while True:
        order_choice = input(
            "\nOrder type: [1] Dine-in or [2] Takeaway: "
        ).strip()

        if order_choice == "1":
            order_type = "dine_in"
            tables = get_available_cafe_tables()

            if not tables:
                print("No café tables are available. Choose takeaway instead.")
                continue

            print("\nAvailable tables:")
            for table in tables:
                print(
                    f"Table {table['table_number']} "
                    f"(capacity {table['capacity']})"
                )

            available_numbers = {str(table["table_number"]): table for table in tables}
            while True:
                table_number = input("Enter table number: ").strip()
                selected_table = available_numbers.get(table_number)

                if selected_table is not None:
                    table_id = selected_table["table_id"]
                    break

                print("That table is not available. Choose a listed table number.")
            break

        if order_choice == "2":
            order_type = "takeaway"
            table_id = None
            break

        print("Enter 1 for dine-in or 2 for takeaway.")

    employees = get_active_employees()
    if not employees:
        print("No active employees found. Add an active employee before saving orders.")
        return

    print("\nActive employees:")
    for employee in employees:
        print(f"{employee['employee_id']}: {employee['employee_name']}")

    employee_ids = {str(employee["employee_id"]) for employee in employees}
    while True:
        employee_id = input("Select employee ID from the list: ").strip()

        if employee_id in employee_ids:
            employee_id = int(employee_id)
            break

        print("Choose an employee ID from the list.")

    display_bill(cart)

    while True:
        payment_complete = input(
            "\nHas the payment been completed? (y/n): "
        ).strip().lower()

        if payment_complete in ("y", "n"):
            break

        print("Enter y for yes or n for no.")

    if payment_complete == "n":
        print("Order cancelled. No customer, order, or payment data was saved.")
        return

    while True:
        payment_method = input(
            "Payment method: [1] Cash, [2] UPI, [3] Card: "
        ).strip()
        payment_methods = {"1": "cash", "2": "upi", "3": "card"}

        if payment_method in payment_methods:
            payment_method = payment_methods[payment_method]
            break

        print("Choose 1 for cash, 2 for UPI, or 3 for card.")

    order_id = save_order(
        customer,
        employee_id,
        order_type,
        cart,
        payment_method,
        table_id,
    )
    print(
        f"\nOrder #{order_id} and completed {payment_method} payment saved successfully."
    )


if __name__ == "__main__":
    run_receptionist()