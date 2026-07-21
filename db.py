# import os
import pymysql
# from dotenv import load_dotenv
from config import Config

# load_dotenv()

def get_connection():
    connection = pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        port=Config.MYSQL_PORT
    )
    return connection



print("Database connection established successfully.")
print(get_connection())