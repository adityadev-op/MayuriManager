from Database_.connection import get_connection


def get_cafe_tables():
    """Return every café table ordered by its visible table number."""
    connection = get_connection()
    cursor = None
    try:
        connection.commit()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT table_id, table_number, capacity, table_status
            FROM cafe_tables
            ORDER BY table_number
            """
        )
        tables = cursor.fetchall()
        connection.commit()
        return tables
    finally:
        if cursor is not None:
            cursor.close()


def vacate_cafe_table(table_id):
    """Mark an occupied café table available, rejecting stale requests."""
    if table_id is None:
        raise ValueError("Choose an allocated table to vacate.")

    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE cafe_tables
            SET table_status = 'available'
            WHERE table_id = %s AND table_status = 'occupied'
            """,
            (table_id,),
        )
        if cursor.rowcount != 1:
            raise ValueError(
                "This table is no longer marked allocated. Refresh the seat list."
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()