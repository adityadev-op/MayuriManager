from mysql.connector import Error
from Database_ import connection


def add_category(connection, category_name, description=None):
    cursor = None

    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO categories (category_name, description)
            VALUES (%s, %s)
        """

        values = (category_name, description)

        cursor.execute(query, values)
        connection.commit()

        print(f"Category '{category_name}' added successfully!")

    except Error as error:
        connection.rollback()
        print("Failed to add category:", error)

    finally:
        if cursor is not None:
            cursor.close()


def add_menu_item(
    connection,
    category_id,
    item_name,
    description,
    price,
    is_available=True
):
    cursor = None

    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO menu_items
                (category_id, item_name, description, price, is_available)
            VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            category_id,
            item_name,
            description,
            price,
            is_available
        )

        cursor.execute(query, values)
        connection.commit()

        print(f"Menu item '{item_name}' added successfully!")

    except Error as error:
        connection.rollback()
        print(f"Failed to add '{item_name}':", error)

    finally:
        if cursor is not None:
            cursor.close()



def add_sample_menu(connection):
    menu_items = [
        # category_id, name, description, price
        (1, "Masala Tea", "Indian spiced tea", 30.00),
        (1, "Cappuccino", "Espresso with steamed milk", 100.00),
        (1, "Hot Chocolate", "Rich chocolate drink", 120.00),
        (1, "Black Coffee", "Freshly brewed black coffee", 60.00),

        (2, "Fresh Lime Soda", "Fresh lime soda", 60.00),
        (2, "Lemon Iced Tea", "Chilled lemon tea", 80.00),
        (2, "Cola", "Chilled cola", 40.00),
        (2, "Fresh Lime Water", "Fresh lime water", 40.00),

        (3, "Chocolate Shake", "Chocolate milkshake", 120.00),
        (3, "Banana Smoothie", "Banana smoothie", 100.00),
        (3, "Strawberry Shake", "Strawberry milkshake", 130.00),
        (3, "Oreo Shake", "Oreo cookie shake", 150.00),

        (4, "Garlic Bread", "Toasted garlic bread", 100.00),
        (4, "Veg Spring Rolls", "Crispy vegetable rolls", 120.00),
        (4, "Chilli Paneer", "Spicy paneer starter", 180.00),
        (4, "Crispy Corn", "Crispy seasoned corn", 150.00),

        (5, "French Fries", "Crispy potato fries", 90.00),
        (5, "Samosa", "Two vegetable samosas", 40.00),
        (5, "Nachos", "Nachos with cheese", 130.00),
        (5, "Masala Maggi", "Spiced instant noodles", 70.00),

        (6, "Veg Grilled Sandwich", "Grilled vegetable sandwich", 100.00),
        (6, "Paneer Wrap", "Paneer-filled wrap", 140.00),
        (6, "Cheese Corn Sandwich", "Cheese and corn sandwich", 130.00),
        (6, "Mexican Veg Wrap", "Mexican-style vegetable wrap", 150.00),

        (7, "Classic Veg Burger", "Classic vegetable burger", 100.00),
        (7, "Cheese Burger", "Vegetable burger with cheese", 130.00),
        (7, "Paneer Burger", "Burger with paneer patty", 160.00),
        (7, "Double Patty Burger", "Burger with double patty", 180.00),

        (8, "Margherita Pizza", "Classic cheese pizza", 180.00),
        (8, "Farm Fresh Pizza", "Mixed vegetable pizza", 250.00),
        (8, "Paneer Tikka Pizza", "Pizza topped with paneer tikka", 280.00),
        (8, "Four Cheese Pizza", "Four-cheese pizza", 300.00),

        (9, "White Sauce Pasta", "Creamy white sauce pasta", 180.00),
        (9, "Red Sauce Pasta", "Tomato sauce pasta", 170.00),
        (9, "Veg Hakka Noodles", "Vegetable hakka noodles", 140.00),
        (9, "Chilli Garlic Noodles", "Spicy garlic noodles", 160.00),

        (10, "Paneer Butter Masala", "Paneer in creamy tomato gravy", 220.00),
        (10, "Dal Tadka", "Yellow lentils with tempering", 160.00),
        (10, "Veg Fried Rice", "Vegetable fried rice", 150.00),
        (10, "Chole Rice Bowl", "Chickpeas served with rice", 140.00),

        (11, "Chocolate Brownie", "Chocolate brownie", 100.00),
        (11, "Chocolate Cake", "Chocolate cake slice", 120.00),
        (11, "Blueberry Cheesecake", "Blueberry cheesecake slice", 180.00),
        (11, "Chocolate Lava Cake", "Warm chocolate lava cake", 150.00),

        (12, "Burger Fries Cola Combo", "Burger, fries and cola", 220.00),
        (12, "Sandwich Cold Coffee Combo", "Sandwich with cold coffee", 200.00),
        (12, "Pizza Garlic Bread Combo", "Pizza with garlic bread", 300.00),
        (12, "Pasta Iced Tea Combo", "Pasta with iced tea", 230.00),
    ]

    for category_id, name, description, price in menu_items:
        add_menu_item(
            connection,
            category_id,
            name,
            description,
            price
        )



def add_cafe_table(connection, table_number, capacity,
                   table_status="available"):
    cursor = None

    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO cafe_tables
                (table_number, capacity, table_status)
            VALUES (%s, %s, %s)
        """

        values = (table_number, capacity, table_status)

        cursor.execute(query, values)
        connection.commit()

        print(f"Cafe table {table_number} added successfully!")

    except Error as error:
        connection.rollback()
        print(f"Failed to add cafe table {table_number}:", error)

    finally:
        if cursor is not None:
            cursor.close()


def add_sample_cafe_tables(connection):
    tables = [
        (101, 2), (102, 2), (103, 2), (104, 2), (105, 2),
        (106, 2), (107, 2), (108, 2), (109, 2), (110, 2),

        (111, 4), (112, 4), (113, 4), (114, 4), (115, 4),
        (116, 4), (117, 4), (118, 4), (119, 4), (120, 4),
        (121, 4), (122, 4), (123, 4), (124, 4), (125, 4),

        (126, 6), (127, 6), (128, 6), (129, 6), (130, 6),

        (131, 8), (132, 8), (133, 8), (134, 8), (135, 8)
    ]

    for table_number, capacity in tables:
        add_cafe_table(connection, table_number, capacity)


if __name__ == "__main__":
    connection = connection.connect_to_database()
    


    if connection is not None:
        try:
            add_sample_cafe_tables(connection)
        finally:
            connection.close()
            print("Connection closed.")