import mysql.connector
from mysql.connector import Error

def getDataBase():
    try:
        connection = mysql.connector.connect(host='local.cjqrtgktufb4.us-east-1.rds.amazonaws.com',
                                         database='store',
                                         user='admin',
                                         password='Trabajo-1',
                                         autocommit=True)
        return connection

    except Error as e:
        print("Error while connecting to MySQL", e)