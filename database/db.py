import mysql.connector
import os

def get_db():
    return mysql.connector.connect(
        host="switchback.proxy.rlwy.net",
        port=24248,
        user="root",
        password="uibnigOljguaWILElKepIdbRPyxjKesp",
        database="railway"
    )