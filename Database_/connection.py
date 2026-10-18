import getpass
import mysql.connector
from mysql.connector import Error


_database_password = None


def connect_to_database():
    global _database_password

    try:
        password = _database_password

        if password is None:
            password = getpass.getpass("MySQL password for aditya: ")

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
            return connection

    except Error as error:
        print("Database connection failed:", error)

    return None


def get_connection():
    """Return a database connection or raise if the connection failed."""
    connection = connect_to_database()

    if connection is None:
        raise ConnectionError("Unable to connect to the MAYURICAFE database.")

    return connection