import os

import mysql.connector
from mysql.connector import Error


_database_connection = None


def connect_to_database():
    password = os.environ.get("MAYURICAFE_MYSQL_PASSWORD")
    if not password:
        raise ConnectionError(
            "Set MAYURICAFE_MYSQL_PASSWORD in the local .env file."
        )

    try:
        database = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="aditya",
            password=password,
            database="MAYURICAFE",
        )

        if database.is_connected():
            print("Successfully connected to MAYURICAFE!")
            cursor = database.cursor()
            try:
                cursor.execute("SELECT DATABASE()")
                selected_database = cursor.fetchone()
                print("Selected database:", selected_database[0])
            finally:
                cursor.close()
            database.commit()
            return database
    except Error as error:
        print("Database connection failed:", error)

    return None


def get_connection():
    """Return the application's reusable connection to the cafe database."""
    global _database_connection

    if _database_connection is not None:
        try:
            _database_connection.ping(reconnect=True, attempts=1, delay=0)
            if _database_connection.is_connected():
                return _database_connection
        except Error:
            _database_connection = None

    database = connect_to_database()

    if database is None:
        raise ConnectionError("Unable to connect to the MAYURICAFE database.")

    _database_connection = database
    return _database_connection


def close_database_connection():
    """Close the reusable application connection during orderly shutdown."""
    global _database_connection

    database = _database_connection
    _database_connection = None
    if database is not None and database.is_connected():
        database.close()
