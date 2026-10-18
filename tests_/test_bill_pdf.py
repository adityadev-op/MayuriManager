import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from services.bill_pdf import create_bill_pdf


class BillPdfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_creates_order_bill_pdf_in_requested_directory(self):
        customer = {"customer_name": "Maya Guest", "phone": "9876543210"}
        cart = [
            {
                "item_name": "Masala Tea",
                "quantity": 2,
                "price": 30.0,
            }
        ]

        with tempfile.TemporaryDirectory() as directory:
            pdf_path = create_bill_pdf(
                42,
                customer,
                "Aarav",
                "dine_in",
                101,
                "cash",
                cart,
                directory,
            )

            self.assertEqual(pdf_path.name, "MAYURICAFE_bill_42.pdf")
            self.assertEqual(pdf_path.parent.as_posix(), directory)
            self.assertTrue(pdf_path.read_bytes().startswith(b"%PDF-"))
            self.assertIn(b"/Subtype /Image", pdf_path.read_bytes())
            self.assertGreater(pdf_path.stat().st_size, 0)

    def test_rejects_empty_order(self):
        with self.assertRaisesRegex(ValueError, "empty order"):
            create_bill_pdf(
                42,
                {"customer_name": "Maya"},
                "Aarav",
                "takeaway",
                None,
                "upi",
                [],
            )


if __name__ == "__main__":
    unittest.main()
