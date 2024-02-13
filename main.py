from fastapi import FastAPI, HTTPException, Depends, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import sqlite3
from typing import Dict
from pydantic import BaseModel
from models import User, Event, EventCreate ,UserEvent , Token

import jwt
#from jwt.exceptions import PyJWTError
#fix in nxt deployment
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles

from fastapi.responses import HTMLResponse

from fastapi.middleware.cors import CORSMiddleware



ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = "ani-lo-kamtzan"
encoded = jwt.encode({'some': 'payload'}, SECRET_KEY, algorithm='HS256')



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin (replace with specific origins as needed)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# Database connection for users --------------------------------------------------------------------------------

# For password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for password
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def create_users_table():
    conn_users, c_users = connect_users_db()
    c_users.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT, lat TEXT, long TEXT, events TEXT)''')
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

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except TypeError:
        return None


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return username
    except TypeError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")




@app.post("/token")
async def login_for_access_token(username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"sub": user[1]})
    return {"access_token": access_token, "token_type": "bearer"}



@app.post("/register")
async def register(form_data: OAuth2PasswordRequestForm = Depends()):
    hashed_password = pwd_context.hash(form_data.password)
    conn_users , c_users = connect_users_db()
    c_users.execute("INSERT INTO users (username, password) VALUES (?, ?)", (form_data.username, hashed_password))
    conn_users.commit()
    conn_users.close()
    return {"message": "User created successfully"}

@app.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    print(payload)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
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
    c_users.execute('SELECT id, username, lat, long, events FROM users')
    users_data = c_users.fetchall()
    conn_users.close()
    return users_data




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


