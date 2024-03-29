from fastapi import FastAPI, HTTPException, Depends, status, Form ,WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import sqlite3
from typing import Dict , List
from pydantic import BaseModel
from models import User, Event, EventCreate ,UserEvent   , UpdateUserData , Message
from fastapi import FastAPI, Form, HTTPException, status
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles

from fastapi.responses import HTMLResponse

from fastapi.middleware.cors import CORSMiddleware

import secrets

from dataclasses import dataclass

import json

import uuid

import re
from fastapi import Form



app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the map application"}
# Cors middleware for enabling cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin (replace with specific origins as needed)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    
)





# Database messages for users --------------------------------------------------------------------------------
# create a table for messages that will be used to store messages the users send to each other the colomns are id, user_1_id, user_2_id , message, current_date_time 
def create_messages_table():
    conn_messages ,c_messages =  connect_messages_db()
    c_messages.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY, user_1_id INTEGER,text TEXT , user_2_id INTEGER, current_date_time TEXT , avatar TEXT )''')
    conn_messages.commit()
    conn_messages.close()

def connect_messages_db():
    conn_messages = sqlite3.connect('messages.db')
    c_messages = conn_messages.cursor()
    return conn_messages, c_messages

create_messages_table()


@app.get("/messages/{user_1_id}/{user_2_id}")
async def get_messages(user_1_id: int, user_2_id: int):
    conn_messages, c_messages = connect_messages_db()
    c_messages.execute('SELECT user_1_id, user_2_id, message, current_date_time FROM messages WHERE (user_1_id=? AND user_2_id=?) OR (user_1_id=? AND user_2_id=?)', (user_1_id, user_2_id, user_2_id, user_1_id))
    messages_data = c_messages.fetchall()
    conn_messages.close()
    return messages_data

@app.post("/messages/{user_1_id}/{user_2_id}")
async def create_message(message_data: Message):
    conn_messages ,c_messages = connect_messages_db()
    user_1_id=message_data.user_id_1
    text = message_data.text
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    avatar = message_data.avatar
    
    user_2_id = message_data.user_id_2
    c_messages.execute("INSERT INTO messages (user_1_id, user_2_id, text, current_date_time ,avatar) VALUES (?, ?, ?, ? , ?)", (user_1_id, user_2_id, text, current_date_time , avatar))
    conn_messages.commit()
    conn_messages.close()
    return {"message": "Message created successfully"}

# For password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for password
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def create_users_table():
    conn_users, c_users = connect_users_db()
    c_users.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT, lat TEXT, long TEXT, phone TEXT ,token TEXT ,token_expiry TEXT)''')
    conn_users.commit()
    conn_users.close()
    
def connect_users_db():
    conn_users = sqlite3.connect('users.db')
    c_users = conn_users.cursor()
    return conn_users, c_users

create_users_table()

async def get_user(username: str):
    conn_users, c_users = connect_users_db()  
    c_users.execute('SELECT * FROM users WHERE username=?', (username,))
    user_data = c_users.fetchone()
    conn_users.close()
    if user_data:
        return user_data
    
def check_user_token_equals(token: str, user_id: int):
    conn_users, c_users = connect_users_db()  
    c_users.execute('SELECT * FROM users WHERE id=?', (user_id,))
    user_data = c_users.fetchone()
    conn_users.close()  
    if user_data[6] == token:
        return True
    return False
    
def check_user(username: str):
    conn_users, c_users = connect_users_db()  
    c_users.execute('SELECT * FROM users WHERE username=?', (username,))
    user_data = c_users.fetchone()
    conn_users.close()  
    if user_data:
        return True
    return False

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    print(user)
    if not user:
        return False
    if not verify_password(password, user[2]):
        return False
    return user


def authenticate_user_token(token: str):
    conn_users, c_users = connect_users_db()
    c_users.execute('SELECT * FROM users WHERE token=?', (token,))
    token_data = c_users.fetchone()
    conn_users.close()
    return token_data


def is_safe_password(password):
    # Check length
    if len(password) < 8:
        return "password must be at least 8 characters long"
    # Check for at least one uppercase letter
    if not re.search(r"[A-Z]", password):
        return "password must contain at least one uppercase letter"
    # Check for at least one lowercase letter
    if not re.search(r"[a-z]", password):
        return "password must contain at least one lowercase letter"
    # Check for at least one digit
    if not re.search(r"\d", password):
        return "password must contain at least one digit"
    # Check for at least one special character
    if not re.search(r"[ !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~]", password):
        return "password must contain at least one special character"    
    return True


# Token generation function
def create_access_token(username: str):
    token_expiry = datetime.utcnow() + timedelta(days=90)  # Set token expiry to 30 minutes
    token = secrets.token_hex(32)  # Generate a random token
    return {"access_token": token, "token_type": "bearer", "expires_at": token_expiry}




def hash_access_token(token: str):
    return pwd_context.hash(token)


@app.post("/token")
async def login_for_access_token(username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(username)
    return access_token

@app.post("/login_token")
async def login_using_access_token(token: str):
    user = authenticate_user_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"message": "Token is valid" ,  "username": user[1] , "id": user[0], "phone": user[5], "lat": user[3], "long": user[4]}


@app.post("/register")
async def register(form_data: OAuth2PasswordRequestForm = Depends()):
    hashed_password = pwd_context.hash(form_data.password)
    conn_users , c_users = connect_users_db()
    access_token = create_access_token(form_data.username)
    if check_user(form_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    c_users.execute("INSERT INTO users (username, password,token ,token_expiry ) VALUES (?, ?, ? , ?)", (form_data.username, hashed_password , access_token["access_token"], access_token["expires_at"]))
    conn_users.commit()
    conn_users.close()
    return access_token

@app.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    return {"message": "Access granted"}


@app.put("/users_location_update/{user_id}")
async def update_user_location(user_id: int, lat: str = Form(...), long: str = Form(...)):
    conn_users , c_users = connect_users_db()

    c_users.execute("UPDATE users SET lat=?, long=? WHERE id=?", (lat, long, user_id))
    conn_users.commit()
    conn_users.close()
    return {"message": "User location updated successfully"}





@app.get("/users")
async def get_users():
    conn_users , c_users = connect_users_db()
    c_users.execute('SELECT id, username, lat, long, phone FROM users')
    users_data = c_users.fetchall()
    conn_users.close()
    return users_data

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    conn_users , c_users = connect_users_db()
    c_users.execute('SELECT id , username, lat, long, phone , token FROM users WHERE id=?', (user_id,))
    user_data = c_users.fetchone()
    conn_users.close()
    return user_data


@app.put("/users/{user_id}")
async def update_user(user_id: int, data: UpdateUserData):
    fields_to_update = {k: v for k, v in data.dict().items() if v is not None}
    if not fields_to_update:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    conn_users, c_users = connect_users_db()
    try:
        query = "UPDATE users SET "
        query += ", ".join(f"{field} = ?" for field in fields_to_update.keys())
        query += " WHERE id = ?"
        c_users.execute(query, list(fields_to_update.values()) + [user_id])
        conn_users.commit()
    finally:
        conn_users.close()

    return {"message": "User updated successfully"}



# Database connection for events  --------------------------------------------------------------------------------
def create_events_table():
    conn_events ,c_events = connect_events_db()
   
    c_events.execute('''CREATE TABLE IF NOT EXISTS events
                 (id INTEGER PRIMARY KEY, title TEXT, description TEXT, date TEXT, user_id INTEGER, lata TEXT, longa TEXT)''')
    conn_events.commit()
    conn_events.close()

def connect_events_db():
    conn_events = sqlite3.connect('events.db')
    c_events = conn_events.cursor()
    return conn_events, c_events

create_events_table()



@app.get("/events/{event_id}")
async def get_event(event_id: int):
    conn_events ,c_events = connect_events_db()

    c_events.execute('SELECT * FROM events WHERE id=?', (event_id,))
    event_data = c_events.fetchone()
    conn_events.close()
    return event_data

@app.put("/events/{event_id}")
async def update_event(event_id: int, title: str = Form(...), description: str = Form(...), date: str = Form(...), user_id: int = Form(...), lata: str = Form(...), longa: str = Form(...)):
    conn_events ,c_events = connect_events_db()

    c_events.execute("UPDATE events SET title=?, description=?, date=?, user_id=?, lata=?, longa=? WHERE id=?", (title, description, date, user_id, lata, longa, event_id))
    conn_events.commit()
    conn_events.close()
    return {"message": "Event updated successfully"}

@app.delete("/events/{event_id}")
async def delete_event(event_id: int):
    conn_events ,c_events = connect_events_db()
    c_events.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn_events.commit()
    conn_events.close()
    return {"message": "Event deleted successfully"}


@app.get("/events")
async def get_events():
    conn_events ,c_events = connect_events_db()
    c_events.execute('SELECT * FROM events')
    events_data = c_events.fetchall()
    conn_events.close()
    return events_data



@app.post("/events")
async def create_event(event_data: EventCreate):
    title = event_data.title
    description = event_data.description
    date = event_data.date
    user_id = event_data.user_id
    lata = event_data.lata
    longa = event_data.longa
    conn_events ,c_events = connect_events_db()

    # Execute the SQL query
    c_events.execute("INSERT INTO events (title, description, date, user_id, lata, longa) VALUES (?, ?, ?, ?, ?, ?)", (title, description, date, user_id, lata, longa))
    conn_events.commit()
    conn_events.close()
    return {"message": "Event created successfully"}




# Database connection for user events --------------------------------------------------------------------------------
def create_user_events():
    conn_user_events,c_user_events =  connect_user_events()
    c_user_events.execute('''CREATE TABLE IF NOT EXISTS user_events (id INTEGER PRIMARY KEY, user_id INTEGER, event_id INTEGER)''')
    conn_user_events.commit()
    conn_user_events.close()

def connect_user_events():
    conn_user_events = sqlite3.connect('user_events.db')
    c_user_events = conn_user_events.cursor()
    return conn_user_events , c_user_events

create_user_events()


@app.get("/user_events_using_user/{user_id}")
async def get_user_events(user_id: int):
    conn_events ,c_events = connect_events_db()
    conn_user_events,c_user_events =  connect_user_events()
    event_list = []
    c_user_events.execute('SELECT event_id FROM user_events WHERE user_id=?', (user_id,))
    user_events = c_user_events.fetchall()
    for event in user_events:
        c_events.execute('SELECT * FROM events WHERE id=?', (event[0],))
        event_data = c_events.fetchone()
        event_list.append(event_data)
    conn_events.close()
    conn_user_events.close()
    return event_list


@app.get("/user_events_using_event/{event_id}")
async def get_event_users(event_id: int):
    conn_user_events,c_user_events =  connect_user_events()
    conn_users , c_users = connect_users_db()
    user_list = []
    c_user_events.execute('SELECT user_id FROM user_events WHERE event_id=?', (event_id,))
    event_users = c_user_events.fetchall()
    for user in event_users:
        c_users.execute('SELECT id , username FROM users WHERE id=?', (user[0],))
        user_data = c_users.fetchone()
        user_list.append(user_data)
    conn_users.close()
    conn_user_events.close()
    return user_list


