from fastapi import FastAPI, HTTPException, Depends, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import sqlite3
from typing import Dict

from pydantic import BaseModel
from models import User, Event, EventCreate




app = FastAPI()

# For password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for password
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

# Helper functions
def get_user(username: str):
    c_users.execute('SELECT * FROM users WHERE username=?', (username,))
    user_data = c_users.fetchone()
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
    return data

# Routes
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password ,form_data.lat, form_data.long)
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
    c_users.execute("INSERT INTO users (username, password) VALUES (?, ?)", (form_data.username, hashed_password))
    conn_users.commit()
    return {"message": "User created successfully"}

@app.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    return {"message": "This is a protected route"}


@app.put("/users_location_update/{user_id}")
async def update_user_location(user_id: int, lat: str = Form(...), long: str = Form(...)):
    c_users.execute("UPDATE users SET lat=?, long=? WHERE id=?", (lat, long, user_id))
    conn_users.commit()
    return {"message": "User location updated successfully"}




@app.put("/users/location_update/{user_id}")
async def update_user_location(user_id: int, lat: str = Form(...), long: str = Form(...)):
    c_users.execute("UPDATE users SET lat=?, long=? WHERE id=?", (lat, long, user_id))
    conn_users.commit()
    return {"message": "User location updated successfully"}


@app.get("/users")
async def get_users():
    c_users.execute('SELECT id, username, lat, long, events FROM users')
    users_data = c_users.fetchall()
    return users_data




@app.get("/events")
async def get_events():
    c_events.execute('SELECT * FROM events')
    events_data = c_events.fetchall()
    return events_data



@app.post("/events")
async def create_event(event_data: EventCreate):
    title = event_data.title
    description = event_data.description
    date = event_data.date
    user_id = event_data.user_id
    lata = event_data.lata
    longa = event_data.longa
    
    # Execute the SQL query
    c_events.execute("INSERT INTO events (title, description, date, user_id, lata, longa) VALUES (?, ?, ?, ?, ?, ?)", (title, description, date, user_id, lata, longa))
    conn_events.commit()
    
    return {"message": "Event created successfully"}











@app.get("/events/{event_id}")
async def get_event(event_id: int):
    c_events.execute('SELECT * FROM events WHERE id=?', (event_id,))
    event_data = c_events.fetchone()
    return event_data

@app.put("/events/{event_id}")
async def update_event(event_id: int, title: str = Form(...), description: str = Form(...), date: str = Form(...), user_id: int = Form(...), lata: str = Form(...), longa: str = Form(...)):
    c_events.execute("UPDATE events SET title=?, description=?, date=?, user_id=?, lata=?, longa=? WHERE id=?", (title, description, date, user_id, lata, longa, event_id))
    conn_events.commit()
    return {"message": "Event updated successfully"}

@app.delete("/events/{event_id}")
async def delete_event(event_id: int):
    c_events.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn_events.commit()
    return {"message": "Event deleted successfully"}

