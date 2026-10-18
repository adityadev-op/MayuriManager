import getpass
from collections.abc import Callable

import mysql.connector
from mysql.connector import Error


_database_password = None
_password_prompt = getpass.getpass
_database_connection = None


def set_password_prompt(prompt: Callable[[str], str]) -> None:
    """Set the password prompt used for future database connections."""
    global _password_prompt
    _password_prompt = prompt


def connect_to_database():
    global _database_password

    try:
        password = _database_password

        if password is None:
            password = _password_prompt("MySQL password for aditya: ")

        connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="aditya",
            password=password,
            database="MAYURICAFE"
        )

        if connection.is_connected():
            _database_password = password
            print("Successfully connected to MAYURICAFE!")

            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE()")
            print("Selected database:", cursor.fetchone()[0])

            cursor.close()
            connection.commit()
            return connection

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

    connection = connect_to_database()

    if connection is None:
        raise ConnectionError("Unable to connect to the MAYURICAFE database.")

    _database_connection = connection
    return _database_connection


def close_database_connection():
    """Close the reusable application connection during orderly shutdown."""
    global _database_connection, _database_password

    connection = _database_connection
    _database_connection = None
    _database_password = None
    if connection is not None and connection.is_connected():
        connection.close()