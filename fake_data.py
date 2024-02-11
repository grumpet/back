from faker import Faker
from models import User, Event ,EventCreate
from main import register ,create_event
import sqlite3
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import FastAPI, HTTPException, Depends, status, Form
import random

fake = Faker()
conn_users = sqlite3.connect('users.db')
c_users = conn_users.cursor()
c_users.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, username TEXT, password TEXT, lat TEXT, long TEXT, events TEXT)''')
conn_users.commit()

# Database connection for events
conn_events = sqlite3.connect('events.db')
c_events = conn_events.cursor()
c_events.execute('''CREATE TABLE IF NOT EXISTS events
             (id INTEGER PRIMARY KEY, title TEXT, description TEXT, date TEXT, user_id INTEGER, lata TEXT, longa TEXT)''')
conn_events.commit()

def fake_register():
    c_users.execute("INSERT INTO users (username, password, lat, long) VALUES (?, ?,?,?)", (fake.user_name(), fake.password(),random.randint(1, 1000),random.randint(1, 1000)))
    conn_users.commit()
    
def fake_event():
    c_events.execute("INSERT INTO events (title, description, date, user_id, lata, longa) VALUES (?, ?, ?, ?, ?, ?)", (fake.sentence(),fake.text(),fake.date(),random.randint(1, 1000),str(random.randint(1, 1000)),str(random.randint(1, 1000))))
    conn_events.commit()
    
for i in range(random.randint(1, 100)):
    fake_register()
    fake_event()

    
conn_users.close()

conn_events.close()
