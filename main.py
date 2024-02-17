from fastapi import FastAPI, HTTPException, Depends, status, Form ,WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import sqlite3
from typing import Dict , List
from pydantic import BaseModel
from models import User, Event, EventCreate ,UserEvent  , Message , UpdateUserData
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Form, HTTPException, status
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles

from fastapi.responses import HTMLResponse

from fastapi.middleware.cors import CORSMiddleware

import secrets








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


# chat websocket functionality --------------------------------------------------------------------------------

def create_message_table():
    conn_messages, c_messages = connect_messages_db()
    c_messages.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY, sender_id INTEGER, recipient_id INTEGER, content TEXT, timestamp TEXT)''')
    conn_messages.commit()
    conn_messages.close()

def connect_messages_db():
    conn_messages = sqlite3.connect('messages.db')
    c_messages = conn_messages.cursor()
    return conn_messages, c_messages

create_message_table()

async def save_message(content: str, sender_id: int):
    conn_messages, c_messages = connect_messages_db()
    timestamp = datetime.utcnow()
    c_messages.execute("INSERT INTO messages (sender_id, content, timestamp) VALUES (?, ?, ?)", (sender_id, content, timestamp))
    conn_messages.commit()
    conn_messages.close()

connected_users = {}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(user_id: str, websocket: WebSocket):
    await websocket.accept()
    connected_users[user_id] = websocket
    print(connected_users)
    try:
        while True:
            data = await websocket.receive_text()
            for user, user_ws in connected_users.items():
                if user != user_id:
                    await user_ws.send_text(data)
    except:
        del connected_users[user_id]
        await websocket.close()


# Database connection for users --------------------------------------------------------------------------------

# For password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for password
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def create_users_table():
    conn_users, c_users = connect_users_db()
    c_users.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT, lat TEXT, long TEXT, phone TEXT ,token TEXT)''')
    conn_users.commit()
    conn_users.close()
    
def connect_users_db():
    conn_users = sqlite3.connect('users.db')
    c_users = conn_users.cursor()
    return conn_users, c_users

create_users_table()

def get_user(username: str):
    conn_users, c_users = connect_users_db()  # Get the connection and cursor
    c_users.execute('SELECT * FROM users WHERE username=?', (username,))
    user_data = c_users.fetchone()
    conn_users.close()  # Close the connection after fetching the user data
    if user_data:
        return user_data

def authenticate_user(username: str, password: str):
    user = get_user(username)
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


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

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
    if get_user(form_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
    access_token = create_access_token(form_data.username)
    c_users.execute("INSERT INTO users (username, password,token) VALUES (?, ?, ?)", (form_data.username, hashed_password , access_token["access_token"]))
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
    c_users.execute('SELECT id, username, lat, long, phone , token FROM users')
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


