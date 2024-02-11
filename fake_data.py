from faker import Faker
from models import User, Event ,EventCreate ,UserEvent
from main import register ,create_event
import sqlite3
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import FastAPI, HTTPException, Depends, status, Form
import random
from passlib.context import CryptContext
import os
import shutil

def del_database(path):
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"DELETE FROM {table[0]};")
    conn.commit()
    conn.close()
    
    
    
# Delete the databases and the users.txt file
if os.path.exists("users.txt"):
    os.remove("users.txt")
if os.path.exists("users.db"):
    del_database("users.db")
if os.path.exists("events.db"):
    del_database("events.db")
if os.path.exists("user_events.db"):
    del_database("user_events.db")



fake = Faker()

conn_users = sqlite3.connect('users.db')
c_users = conn_users.cursor()
c_users.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, username TEXT, password TEXT, lat TEXT, long TEXT, events TEXT)''')
conn_users.commit()

# Database connection for events
conn_events = sqlite3.connect('events.db')
c_events = conn_events.cursor()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

c_events.execute('''CREATE TABLE IF NOT EXISTS events
             (id INTEGER PRIMARY KEY, title TEXT, description TEXT, date TEXT, user_id INTEGER, lata TEXT, longa TEXT)''')
conn_events.commit()

# Database connection for user events
conn_user_events = sqlite3.connect('user_events.db')
c_user_events = conn_user_events.cursor()
c_user_events.execute('''CREATE TABLE IF NOT EXISTS user_events
             (id INTEGER PRIMARY KEY, user_id INTEGER, event_id INTEGER)''')
conn_user_events.commit()





def fake_user_event(event_id, user_id):
    c_user_events.execute("INSERT INTO user_events (user_id, event_id) VALUES (?, ?)", (event_id,user_id))
    conn_user_events.commit()



def fake_register():
    pas=fake.password()
    user=fake.user_name()
    text  = user + " -- " +pas
    print(text)
    with open("users.txt", "a") as file:
        file.write(text + "\n")

    c_users.execute("INSERT INTO users (username, password, lat, long) VALUES (?, ?,?,?)", (user, pwd_context.hash(pas),random.randint(1, 1000),random.randint(1, 1000)))
    id = c_users.lastrowid
    conn_users.commit()
    return id
    
def fake_event():
    c_events.execute("INSERT INTO events (title, description, date, user_id, lata, longa) VALUES (?, ?, ?, ?, ?, ?)", (fake.sentence(),fake.text(),fake.date(),random.randint(1, 1000),str(random.randint(1, 1000)),str(random.randint(1, 1000))))
    id = c_events.lastrowid
    conn_events.commit()
    return id
    
users_id = []
event_id = []
for i in range(random.randint(1, 100)):
    u = fake_register()
    e = fake_event()
    users_id.append(u)
    event_id.append(e)
    
random.shuffle(users_id)
random.shuffle(event_id)

for i in range(len(users_id)):
    fake_user_event(users_id[i],event_id[i])
    
conn_users.close()

conn_events.close()

conn_user_events.close()
