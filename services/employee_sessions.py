from Database_.connection import get_connection


def ensure_employee_login_table():
    database = get_connection()
    cursor = None
    try:
        cursor = database.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS employe_login (
                login_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                employee_id INT NOT NULL,
                employee_name VARCHAR(100) NOT NULL,
                job_role VARCHAR(50) NOT NULL,
                login_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                logout_time DATETIME NULL,
                INDEX idx_employe_login_time (login_time),
                INDEX idx_employe_login_employee (employee_id)
            )
            """
        )
        database.commit()
    except Exception:
        database.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()


def start_employee_login(employee_id, employee_name, job_role):
    if employee_id is None or not employee_name or not job_role:
        raise ValueError("A valid employee identity is required to start a login session.")

    ensure_employee_login_table()
    database = get_connection()
    cursor = None
    try:
        cursor = database.cursor()
        cursor.execute(
            """
            INSERT INTO employe_login
                (employee_id, employee_name, job_role, login_time)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (employee_id, employee_name, job_role),
        )
        login_id = cursor.lastrowid
        if login_id is None:
            raise RuntimeError("The employee login session was not recorded.")
        database.commit()
        return int(login_id)
    except Exception:
        database.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()


def end_employee_login(login_id):
    if login_id is None:
        raise ValueError("A login session ID is required to end an employee session.")

    database = get_connection()
    cursor = None
    try:
        cursor = database.cursor()
        cursor.execute(
            """
            UPDATE employe_login
            SET logout_time = CURRENT_TIMESTAMP
            WHERE login_id = %s AND logout_time IS NULL
            """,
            (login_id,),
        )
        if cursor.rowcount != 1:
            raise RuntimeError(
                f"Employee login session {login_id} is missing or already closed."
            )
        database.commit()
    except Exception:
        database.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()


def get_employee_login_history(limit=500):
    if limit < 1:
        raise ValueError("The employee login history limit must be positive.")

    ensure_employee_login_table()
    database = get_connection()
    cursor = None
    try:
        cursor = database.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                login_id,
                employee_id,
                employee_name,
                job_role,
                login_time,
                logout_time,
                TIMESTAMPDIFF(
                    SECOND,
                    login_time,
                    COALESCE(logout_time, CURRENT_TIMESTAMP)
                ) AS duration_seconds
            FROM employe_login
            ORDER BY login_time DESC, login_id DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        database.commit()
        return rows
    finally:
        if cursor is not None:
            cursor.close()
