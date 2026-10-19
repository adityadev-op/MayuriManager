# MAYURICAFE

MAYURICAFE is a PySide6 desktop application for managing cafe bookings, orders,
tables, menu items, and sales reports. It connects to a local MySQL database and
creates a PDF receipt for each successfully saved paid order.

## Features

- Role-based sign-in for employees and administrators.
- Guided dine-in and takeaway booking flow with guest, menu, table, and payment
  details. The signed-in employee is assigned automatically.
- Live view of active orders with item, guest, service, and employee details.
- Table management with allocated and available table status, including manual
  table vacancy.
- Admin console with a sales dashboard, menu item creation, database browser,
  sales details, revenue reports, employee bill reports, and employee login
  history with session durations.
- Branded login page and shared MAYURICAFE logo.
- PDF bills saved to `bills/MAYURICAFE_bill_<order_id>.pdf`.

## Requirements

- Python 3.14 or newer.
- MySQL Server with the `MAYURICAFE` database and application tables already
  created.
- The Python packages listed in [`requirements.txt`](requirements.txt).

The application connects to MySQL on `localhost:3306` using the `aditya`
database user and reads its password from a local dotenv file.

Employee sign-ins and sign-outs are recorded in the `employe_login` table,
which the application creates automatically. The admin console shows the most
recent 500 sessions and the elapsed duration of active sessions.

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

Create the following local files in the repository root. They are ignored by
Git and must not be uploaded:

`.env`:

```text
MAYURICAFE_MYSQL_PASSWORD=your-local-mysql-password
```

`.env.employees` contains credentials for the receptionist, cashier, and
manager accounts. Their IDs must correspond to active employee records in
MySQL. `.env.admins` contains the three administrator accounts. The supplied
local credentials are in these ignored files; replace them with private
passwords before sharing a machine or distributing the application.

```dotenv
MAYURICAFE_EMPLOYEE_RECEPTIONIST_USERNAME=...
MAYURICAFE_EMPLOYEE_RECEPTIONIST_PASSWORD=...
MAYURICAFE_EMPLOYEE_RECEPTIONIST_ID=1
MAYURICAFE_EMPLOYEE_CASHIER_USERNAME=...
MAYURICAFE_EMPLOYEE_CASHIER_PASSWORD=...
MAYURICAFE_EMPLOYEE_CASHIER_ID=2
MAYURICAFE_EMPLOYEE_MANAGER_USERNAME=...
MAYURICAFE_EMPLOYEE_MANAGER_PASSWORD=...
MAYURICAFE_EMPLOYEE_MANAGER_ID=10
```

The administrator file uses `MAYURICAFE_ADMIN_<NAME>_USERNAME` and
`MAYURICAFE_ADMIN_<NAME>_PASSWORD` entries for `ADITYA`, `PUSHPRAJ`, and
`DEEPAK`.

## Run

From the repository root with the virtual environment active:

```bash
python app.py
```

The authentication page opens first. The database connection is established
after a successful sign-in.

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
