import unittest
import runpy
from unittest.mock import patch

from Receptionist import cli, customers, orders


class ReceptionistFlowTests(unittest.TestCase):
    def test_get_active_orders_groups_items_and_excludes_closed_orders(self):
        rows = [
            {
                "order_id": 42,
                "order_date": None,
                "order_status": "pending",
                "order_type": "takeaway",
                "total_amount": 110,
                "customer_name": "Maya",
                "customer_phone": "9876543210",
                "employee_name": "Aarav",
                "table_number": None,
                "item_name": "Tea",
                "quantity": 2,
                "unit_price": 30,
            },
            {
                "order_id": 42,
                "order_date": None,
                "order_status": "pending",
                "order_type": "takeaway",
                "total_amount": 110,
                "customer_name": "Maya",
                "customer_phone": "9876543210",
                "employee_name": "Aarav",
                "table_number": None,
                "item_name": "Cake",
                "quantity": 1,
                "unit_price": 50,
            },
        ]
        cursor = unittest.mock.Mock()
        cursor.fetchall.return_value = rows
        database = unittest.mock.Mock()
        database.cursor.return_value = cursor

        with patch.object(orders, "get_connection", return_value=database):
            active_orders = orders.get_active_orders()

        query = cursor.execute.call_args.args[0]
        self.assertIn("order_status NOT IN ('completed', 'cancelled')", query)
        self.assertIn("LEFT JOIN order_items AS oi", query)
        self.assertEqual(len(active_orders), 1)
        self.assertEqual(active_orders[0]["order_id"], 42)
        self.assertEqual(
            [item["item_name"] for item in active_orders[0]["items"]],
            ["Tea", "Cake"],
        )
        self.assertEqual(database.commit.call_count, 2)
        cursor.close.assert_called_once_with()

    def test_get_completed_orders_returns_only_completed_status(self):
        cursor = unittest.mock.Mock()
        cursor.fetchall.return_value = []
        database = unittest.mock.Mock()
        database.cursor.return_value = cursor

        with patch.object(orders, "get_connection", return_value=database):
            result = orders.get_completed_orders()

        self.assertEqual(result, [])
        self.assertIn(
            "WHERE o.order_status = 'completed'",
            cursor.execute.call_args.args[0],
        )
        cursor.close.assert_called_once_with()

    def test_ensure_completed_order_status_adds_supported_status_once(self):
        cursor = unittest.mock.Mock()
        cursor.fetchone.return_value = (
            "(`order_status` in ('pending','preparing','served','cancelled'))",
        )
        database = unittest.mock.Mock()
        database.cursor.return_value = cursor

        with patch.object(orders, "get_connection", return_value=database):
            orders.ensure_completed_order_status()

        self.assertIn("DROP CHECK chk_order_status", cursor.execute.call_args.args[0])
        self.assertIn("'completed'", cursor.execute.call_args.args[0])
        self.assertEqual(database.commit.call_count, 2)

    def test_ensure_completed_order_status_is_idempotent(self):
        cursor = unittest.mock.Mock()
        cursor.fetchone.return_value = (
            "(`order_status` in ('pending','completed'))",
        )
        database = unittest.mock.Mock()
        database.cursor.return_value = cursor

        with patch.object(orders, "get_connection", return_value=database):
            orders.ensure_completed_order_status()

        cursor.execute.assert_called_once()
        database.commit.assert_called_once_with()

    def test_complete_order_updates_status_and_releases_assigned_table(self):
        cursor = unittest.mock.Mock()
        cursor.fetchone.return_value = {"table_id": 7}
        cursor.rowcount = 1
        database = unittest.mock.Mock()
        database.cursor.return_value = cursor

        with patch.object(orders, "get_connection", return_value=database):
            orders.complete_order(42)

        self.assertEqual(cursor.execute.call_count, 3)
        self.assertIn(
            "UPDATE orders",
            cursor.execute.call_args_list[1].args[0],
        )
        self.assertEqual(cursor.execute.call_args_list[1].args[1], (42,))
        self.assertIn(
            "UPDATE cafe_tables",
            cursor.execute.call_args_list[2].args[0],
        )
        self.assertEqual(cursor.execute.call_args_list[2].args[1], (7,))
        database.commit.assert_called_once_with()
        database.rollback.assert_not_called()
        cursor.close.assert_called_once_with()

    def test_complete_order_rolls_back_if_order_is_not_open(self):
        cursor = unittest.mock.Mock()
        cursor.fetchone.return_value = None
        database = unittest.mock.Mock()
        database.cursor.return_value = cursor

        with (
            patch.object(orders, "get_connection", return_value=database),
            self.assertRaisesRegex(ValueError, "missing, cancelled, or already completed"),
        ):
            orders.complete_order(42)

        database.rollback.assert_called_once_with()
        database.commit.assert_not_called()

    def test_app_launches_authentication_before_connecting_to_database(self):
        with (
            patch("PySide6.QtWidgets.QApplication") as application_class,
            patch("gui.main_window.MainWindow") as window_class,
            patch("Database_.connection.get_connection") as connect_database,
        ):
            application = application_class.return_value
            application.exec.return_value = 0
            with self.assertRaises(SystemExit) as exit_code:
                runpy.run_module("app", run_name="__main__")

        self.assertEqual(exit_code.exception.code, 0)
        application_class.assert_called_once_with([])
        application.setApplicationName.assert_called_once_with("MAYURICAFE")
        connect_database.assert_not_called()
        window_class.return_value.show_startup_video.assert_called_once_with()
        window_class.return_value.show.assert_called_once_with()
        application.exec.assert_called_once_with()

    def test_cli_runs_customer_order_and_billing_flow(self):
        customer = {"customer_id": 1, "customer_name": "Maya"}
        menu_items = [{"item_id": 1, "item_name": "Tea", "price": 30.0}]
        cart = [{"item_id": 1, "item_name": "Tea", "price": 30.0, "quantity": 2}]

        with (
            patch(
                "builtins.input",
                side_effect=["9876543210", "2", "12", "y", "1"],
            ),
            patch.object(
                cli,
                "get_customer_or_registration_details",
                return_value=customer,
            ) as get_customer,
            patch.object(cli, "get_available_menu_items", return_value=menu_items) as get_menu,
            patch.object(cli, "build_order", return_value=cart) as build_order,
            patch.object(
                cli,
                "get_active_employees",
                return_value=[{"employee_id": 12, "employee_name": "Aarav"}],
            ) as get_employees,
            patch.object(cli, "save_order", return_value=42) as save_order,
            patch.object(cli, "display_bill") as display_bill,
        ):
            cli.run_receptionist()

        get_customer.assert_called_once_with("9876543210")
        get_menu.assert_called_once_with()
        build_order.assert_called_once_with(menu_items)
        get_employees.assert_called_once_with()
        save_order.assert_called_once_with(
            customer, 12, "takeaway", cart, "cash", None
        )
        display_bill.assert_called_once_with(cart)

    def test_cli_cancel_does_not_save_any_data(self):
        new_customer = {
            "customer_name": "Maya",
            "phone": "9876543210",
            "email": None,
        }
        menu_items = [{"item_id": 1, "item_name": "Tea", "price": 30.0}]
        cart = [{"item_id": 1, "item_name": "Tea", "price": 30.0, "quantity": 2}]

        with (
            patch(
                "builtins.input",
                side_effect=["9876543210", "2", "12", "n"],
            ),
            patch.object(
                cli,
                "get_customer_or_registration_details",
                return_value=new_customer,
            ),
            patch.object(cli, "get_available_menu_items", return_value=menu_items),
            patch.object(cli, "build_order", return_value=cart),
            patch.object(
                cli,
                "get_active_employees",
                return_value=[{"employee_id": 12, "employee_name": "Aarav"}],
            ),
            patch.object(cli, "save_order") as save_order,
            patch.object(cli, "display_bill") as display_bill,
        ):
            cli.run_receptionist()

        save_order.assert_not_called()
        display_bill.assert_called_once_with(cart)

    def test_cli_does_not_save_order_without_active_employees(self):
        customer = {"customer_id": 1, "customer_name": "Maya"}
        menu_items = [{"item_id": 1, "item_name": "Tea", "price": 30.0}]
        cart = [{"item_id": 1, "item_name": "Tea", "price": 30.0, "quantity": 2}]

        with (
            patch("builtins.input", side_effect=["9876543210", "2"]),
            patch.object(cli, "get_customer_or_registration_details", return_value=customer),
            patch.object(cli, "get_available_menu_items", return_value=menu_items),
            patch.object(cli, "build_order", return_value=cart),
            patch.object(cli, "get_active_employees", return_value=[]),
            patch.object(cli, "save_order") as save_order,
        ):
            cli.run_receptionist()

        save_order.assert_not_called()

    def test_build_order_accepts_case_insensitive_next(self):
        menu_items = [{"item_id": 1, "item_name": "Tea", "price": 30.0}]

        with patch("builtins.input", side_effect=["1", "2", "NeXt"]):
            cart = orders.build_order(menu_items)

        self.assertEqual(
            cart,
            [{"item_id": 1, "item_name": "Tea", "price": 30.0, "quantity": 2}],
        )

    def test_next_proceeds_with_an_empty_cart(self):
        with patch("builtins.input", return_value="NEXT"):
            cart = orders.build_order([{"item_id": 1, "item_name": "Tea", "price": 30.0}])

        self.assertEqual(cart, [])

    def test_new_customer_is_registered_before_ordering(self):
        customer = {"customer_id": 1, "customer_name": "Maya"}

        with (
            patch.object(customers, "get_customer_by_phone", return_value=None) as find_customer,
            patch("builtins.input", side_effect=["Maya", "maya@example.com"]),
            patch.object(customers, "add_customer", return_value=customer) as add_customer,
        ):
            result = customers.get_or_create_customer("9876543210")

        find_customer.assert_called_once_with("9876543210")
        add_customer.assert_called_once_with(
            "Maya", "9876543210", "maya@example.com"
        )
        self.assertEqual(result, customer)

    def test_existing_customer_is_not_registered_again(self):
        customer = {"customer_id": 1, "customer_name": "Maya"}

        with (
            patch.object(customers, "get_customer_by_phone", return_value=customer),
            patch.object(customers, "add_customer") as add_customer,
        ):
            result = customers.get_or_create_customer("9876543210")

        add_customer.assert_not_called()
        self.assertEqual(result, customer)

    def test_save_order_writes_header_items_and_commits(self):
        cursor = unittest.mock.Mock()
        cursor.fetchone.return_value = (12,)
        cursor.lastrowid = 42
        connection = unittest.mock.Mock()
        connection.cursor.return_value = cursor
        cart = [
            {"item_id": 3, "item_name": "Tea", "price": 30, "quantity": 2},
            {"item_id": 5, "item_name": "Cake", "price": 50, "quantity": 1},
        ]

        with patch.object(orders, "get_connection", return_value=connection):
            order_id = orders.save_order(
                {"customer_id": 7}, 12, "takeaway", cart, "cash"
            )

        self.assertEqual(order_id, 42)
        self.assertEqual(cursor.execute.call_count, 3)
        header_query, header_values = cursor.execute.call_args_list[1].args
        self.assertIn("INSERT INTO orders", header_query)
        self.assertEqual(
            header_values,
            (7, 12, None, "takeaway", "pending", 110),
        )
        item_query, item_values = cursor.executemany.call_args.args
        self.assertIn("INSERT INTO order_items", item_query)
        self.assertNotIn("subtotal", item_query)
        self.assertEqual(
            item_values,
            [(42, 3, 2, 30), (42, 5, 1, 50)],
        )
        payment_query, payment_values = cursor.execute.call_args_list[2].args
        self.assertIn("INSERT INTO payments", payment_query)
        self.assertEqual(payment_values, (42, "cash", 110, "completed"))
        connection.commit.assert_called_once_with()
        connection.rollback.assert_not_called()
        connection.close.assert_not_called()

    def test_dine_in_order_occupies_table_in_same_transaction(self):
        cursor = unittest.mock.Mock()
        cursor.fetchone.return_value = (12,)
        cursor.rowcount = 1
        cursor.lastrowid = 43
        connection = unittest.mock.Mock()
        connection.cursor.return_value = cursor
        cart = [{"item_id": 3, "item_name": "Tea", "price": 30, "quantity": 1}]

        with patch.object(orders, "get_connection", return_value=connection):
            order_id = orders.save_order(
                {"customer_id": 7},
                12,
                "dine_in",
                cart,
                "upi",
                table_id=4,
            )

        self.assertEqual(order_id, 43)
        self.assertIn("UPDATE cafe_tables", cursor.execute.call_args_list[1].args[0])
        connection.commit.assert_called_once_with()

    def test_failed_order_rolls_back(self):
        cursor = unittest.mock.Mock()
        cursor.fetchone.return_value = (12,)
        cursor.lastrowid = 42
        cursor.executemany.side_effect = RuntimeError("item insert failed")
        connection = unittest.mock.Mock()
        connection.cursor.return_value = cursor
        cart = [{"item_id": 3, "item_name": "Tea", "price": 30, "quantity": 1}]

        with (
            patch.object(orders, "get_connection", return_value=connection),
            self.assertRaisesRegex(RuntimeError, "item insert failed"),
        ):
            orders.save_order(
                {"customer_id": 7}, 12, "takeaway", cart, "card"
            )

        connection.rollback.assert_called_once_with()
        connection.commit.assert_not_called()
        connection.close.assert_not_called()

    def test_payment_insert_failure_rolls_back_entire_sale(self):
        cursor = unittest.mock.Mock()
        cursor.lastrowid = 42
        cursor.fetchone.return_value = (12,)
        cursor.execute.side_effect = [None, None, RuntimeError("payment insert failed")]
        connection = unittest.mock.Mock()
        connection.cursor.return_value = cursor
        cart = [{"item_id": 3, "item_name": "Tea", "price": 30, "quantity": 1}]

        with (
            patch.object(orders, "get_connection", return_value=connection),
            self.assertRaisesRegex(RuntimeError, "payment insert failed"),
        ):
            orders.save_order(
                {"customer_id": 7}, 12, "takeaway", cart, "cash"
            )

        connection.rollback.assert_called_once_with()
        connection.commit.assert_not_called()

    def test_save_order_rejects_empty_cart(self):
        with self.assertRaisesRegex(ValueError, "no items"):
            orders.save_order(
                {"customer_id": 7}, 12, "takeaway", [], "cash"
            )

    def test_new_customer_is_inserted_as_part_of_paid_order_transaction(self):
        cursor = unittest.mock.Mock()
        cursor.lastrowid = 42
        cursor.fetchone.return_value = (12,)
        connection = unittest.mock.Mock()
        connection.cursor.return_value = cursor
        cart = [{"item_id": 3, "item_name": "Tea", "price": 30, "quantity": 1}]
        customer = {
            "customer_name": "Maya",
            "phone": "9876543210",
            "email": None,
        }

        with patch.object(orders, "get_connection", return_value=connection):
            orders.save_order(customer, 12, "takeaway", cart, "upi")

        customer_query, customer_values = cursor.execute.call_args_list[0].args
        self.assertIn("INSERT INTO customers", customer_query)
        self.assertEqual(customer_values, ("Maya", "9876543210", None))
        connection.commit.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()