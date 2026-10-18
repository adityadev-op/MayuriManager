# MAYURICAFE

MAYURICAFE is a PySide6 desktop application for managing cafe bookings, orders,
tables, menu items, and sales reports. It connects to a local MySQL database and
creates a PDF receipt for each successfully saved paid order.

## Features

- Guided dine-in and takeaway booking flow with guest, menu, table, employee,
  and payment details.
- Live view of active orders with item, guest, service, and employee details.
- Table management with allocated and available table status, including manual
  table vacancy.
- Admin console with a sales dashboard, menu item creation, database browser,
  sales details, revenue reports, and employee bill reports.
- Separate admin password gate.
- Branded startup animation and shared MAYURICAFE logo.
- PDF bills saved to `bills/MAYURICAFE_bill_<order_id>.pdf`.

## Requirements

- Python 3.14 or newer.
- MySQL Server with the `MAYURICAFE` database and application tables already
  created.
- The Python packages listed in [`requirements.txt`](requirements.txt).

The application connects to MySQL on `localhost:3306` using the `aditya`
database user. At startup, it asks for that MySQL user's password; the password
is held only for the current application session.

## Installation

Create and activate a virtual environment from the repository root:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
```

On Windows, activate it with:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

The project does not include SQL migrations or database schema setup. Create
and populate the `MAYURICAFE` database and its expected tables in MySQL before
launching the application.

## Configuration

The admin console is disabled unless `MAYURICAFE_ADMIN_PASSWORD` is configured.
Create a `.env` file in the repository root (it is ignored by Git) with:

```dotenv
MAYURICAFE_ADMIN_PASSWORD=choose-a-private-password
```

The MySQL password is requested separately in the application at startup.

## Run

From the repository root with the virtual environment active:

```bash
python app.py
```

After a successful database connection, the logo splash animation plays and
then the welcome screen opens.

## PDF bills

After an order and its payment are saved, the app writes a receipt PDF to the
`bills/` directory. The folder is created automatically and ignored by Git.
Each filename includes the order ID. Receipts contain the guest, date and time,
service/table, assigned employee, payment method, ordered items, and total paid.

## Tests

Run the test suite from the repository root:

```bash
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests_ -v
```

The offscreen Qt platform allows the PySide6 UI tests to run without opening
application windows.
