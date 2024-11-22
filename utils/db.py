import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',  # Replace with your MySQL username
        password='Abinesh@2002',  # Replace with your MySQL password
        database='employee_details'
    )
