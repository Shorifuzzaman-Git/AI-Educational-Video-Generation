from fastapi import FastAPI,HTTPException
import mysql.connector
from mysql.connector import Error

app=FastAPI()

def get_connection():
    #setup information
    return mysql.connector.connect(
        host="localhost",
        user="shuvo",
        password="Shuvo1009@",
        database="fastapi"
        )

@app.get("/users")
def get_users():
    try:
        conn=get_connection()
        cursor=conn.cursor(dictionary=True)
        cursor.execute("select * from student")
        rows=cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


