import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from gui.booking import BookingWidget


class BookingWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.widget = BookingWidget()

    def test_booking_flow_saves_order_without_terminal_input(self):
        customer = {
            "customer_id": 7,
            "customer_name": "Maya",
            "phone": "9876543210",
            "email": None,
        }
        menu_items = [
            {"item_id": 3, "item_name": "Masala Tea", "price": 30.0}
        ]
        tables = [{"table_id": 4, "table_number": 101, "capacity": 2}]
        employees = [{"employee_id": 12, "employee_name": "Aarav"}]
        completed_orders = []

        with (
            patch("gui.booking.get_customer_by_phone", return_value=customer),
            patch("gui.booking.get_available_menu_items", return_value=menu_items),
            patch("gui.booking.get_available_cafe_tables", return_value=tables),
            patch("gui.booking.get_active_employees", return_value=employees),
            patch("gui.booking.save_order", return_value=42) as save_order,
            patch("builtins.input", side_effect=AssertionError("terminal input used")),
        ):
            self.widget.order_completed.connect(completed_orders.append)
            self.widget.phone_input.setText("9876543210")
            self.widget._lookup_customer()
            self.widget._continue_from_customer()
            self.widget.quantity_input.setValue(2)
            self.widget._add_item()
            self.widget._continue_from_menu()
            self.widget.order_type_combo.setCurrentIndex(1)
            self.widget.table_combo.setCurrentIndex(1)
            self.widget._continue_from_service()
            self.widget.employee_combo.setCurrentIndex(1)
            self.widget._continue_from_employee()
            self.widget.payment_method_combo.setCurrentIndex(1)
            self.widget.payment_complete.setChecked(True)
            self.widget._save_booking()

        save_order.assert_called_once_with(
            customer,
            12,
            "dine_in",
            [
                {
                    "item_id": 3,
                    "item_name": "Masala Tea",
                    "price": 30.0,
                    "quantity": 2,
                }
            ],
            "cash",
            4,
        )
        self.assertEqual(completed_orders, [42])

    def test_new_customer_is_collected_in_form_before_ordering(self):
        menu_items = [
            {"item_id": 3, "item_name": "Masala Tea", "price": 30.0}
        ]
        with (
            patch("gui.booking.get_customer_by_phone", return_value=None),
            patch("gui.booking.get_available_menu_items", return_value=menu_items),
        ):
            self.widget.phone_input.setText("9876543210")
            self.widget._lookup_customer()
            self.widget.name_input.setText("Maya")
            self.widget.email_input.setText("maya@example.com")
            self.widget._continue_from_customer()

        self.assertEqual(
            self.widget.customer,
            {
                "customer_name": "Maya",
                "phone": "9876543210",
                "email": "maya@example.com",
            },
        )
        self.assertEqual(self.widget.stage_stack.currentIndex(), 1)

    def test_stepper_and_order_summary_track_current_booking(self):
        self.widget.customer = {"customer_name": "Maya"}
        self.widget.cart = [
            {"item_id": 3, "item_name": "Masala Tea", "price": 30, "quantity": 2}
        ]
        self.widget.order_type_combo.setCurrentIndex(2)
        self.widget._show_stage(2)

        self.assertEqual(self.widget.step_progress.value(), 3)
        self.assertEqual(self.widget.summary_guest.text(), "Maya")
        self.assertEqual(self.widget.summary_items.text(), "2 items")
        self.assertEqual(self.widget.summary_service.text(), "Takeaway")
        self.assertEqual(self.widget.summary_total.text(), "₹60.00")
        self.assertEqual(self.widget.step_labels[2].property("active"), True)
        self.assertEqual(self.widget.step_labels[1].property("complete"), True)

    def test_order_summary_updates_when_guest_identity_changes(self):
        self.widget.customer = {"customer_name": "Maya"}
        self.widget._refresh_order_summary()
        self.assertEqual(self.widget.summary_guest.text(), "Maya")

        self.widget._invalidate_customer()

        self.assertEqual(self.widget.summary_guest.text(), "Not selected")

    def test_unpaid_order_cancels_without_saving(self):
        cancelled = []
        self.widget.customer = {"customer_id": 7}
        self.widget.cart = [
            {"item_id": 3, "item_name": "Tea", "price": 30, "quantity": 1}
        ]
        self.widget.order_type = "takeaway"
        self.widget.employee_combo.addItem("Aarav", 12)
        self.widget.payment_method_combo.setCurrentIndex(1)
        self.widget.flow_cancelled.connect(lambda: cancelled.append(True))

        with (
            patch(
                "gui.booking.QMessageBox.question",
                return_value=QMessageBox.StandardButton.No,
            ),
            patch("gui.booking.save_order") as save_order,
        ):
            self.widget._save_booking()

        save_order.assert_not_called()
        self.assertEqual(cancelled, [True])
        self.assertEqual(self.widget.stage_stack.currentIndex(), 0)


if __name__ == "__main__":
    unittest.main()
