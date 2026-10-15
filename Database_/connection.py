import getpass
import mysql.connector
from mysql.connector import Error



def connect_to_database():
    try:
        password = getpass.getpass("MySQL password for aditya: ")

        connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="aditya",
            password=password,
            database="MAYURICAFE"
        )

        if connection.is_connected():
            print("Successfully connected to MAYURICAFE!")

            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE()")
            print("Selected database:", cursor.fetchone()[0])

            cursor.close()
            return connection

    except Error as error:
        print("Database connection failed:", error)

    return None