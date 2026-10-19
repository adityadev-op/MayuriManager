# MAYURICAFE

MAYURICAFE is a PySide6 desktop application for managing cafe bookings, orders,
tables, menu items, and sales reports. It connects to a local MySQL database and
creates a PDF receipt for each successfully saved paid order.

## Features

- Role-based sign-in for employees and administrators.
- Guided dine-in and takeaway booking flow with guest, menu, table, and payment
  details. The signed-in employee is assigned automatically.
- Live view of active orders with item, guest, service, and employee details.
- Dedicated Order Manager sign-in with an order queue, completion action, and
  completed-order history.
- Table management with allocated and available table status, including manual
  table vacancy.
- Admin console with a sales dashboard, menu item creation, database browser,
  sales details, revenue reports, employee bill reports, and employee login
  history with session durations.
- MAYURICAFE opening video in the main app window, followed by the existing
  login page.
- Branded login page and shared MAYURICAFE logo.
- PDF bills saved to `bills/MAYURICAFE_bill_<order_id>.pdf`.

## Requirements

- Python 3.14 or newer.
- Qt Multimedia support for video and audio playback (provided by
  `PySide6-Addons` in the requirements).
- MySQL Server 8.0.16 or newer. Create the `MAYURICAFE` schema from
  [`database/schema.sql`](database/schema.sql) before launching.
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

For a fresh local installation, create the database and schema without
importing any application data:

```bash
mysql -u your_mysql_user -p < database/schema.sql
```

Add active employee records to `employees` and configure matching employee IDs
in `.env.employees`; credentials are intentionally not included in the
repository. Existing databases add support for completed orders when an Order
Manager signs in. The employee session-audit table is created automatically
when an employee signs in.

## Configuration

Create the following local files in the repository root. They are ignored by
Git and must not be uploaded:

`.env`:

```text
MAYURICAFE_MYSQL_PASSWORD=your-local-mysql-password
```

`.env.employees` contains credentials for the receptionist, cashier, and
manager accounts. Their IDs must correspond to active employee records in
MySQL. This includes the Order Manager account. `.env.admins` contains the
three administrator accounts. The supplied
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
MAYURICAFE_EMPLOYEE_ORDER_MANAGER_USERNAME=...
MAYURICAFE_EMPLOYEE_ORDER_MANAGER_PASSWORD=...
MAYURICAFE_EMPLOYEE_ORDER_MANAGER_ID=11
```

The administrator file uses `MAYURICAFE_ADMIN_<NAME>_USERNAME` and
`MAYURICAFE_ADMIN_<NAME>_PASSWORD` entries for `ADITYA`, `PUSHPRAJ`, and
`DEEPAK`.

## Run

From the repository root with the virtual environment active:

```bash
python app.py
```

The bundled `gui/assets/opening_video.mp4` plays in the main app window when
the app starts. When it finishes, the existing authentication page replaces
the video; press Escape or click the video to skip it. The database connection
is established after a successful sign-in. If playback is unavailable, the
error is logged and the app continues to authentication.

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
