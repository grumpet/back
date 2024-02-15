from pydantic import BaseModel
from typing import List, Optional
import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()

class Event(BaseModel):
    def __init__(self, id: int, title: str, description: str, date: str , user_id: int,lata: str, longa: str):
        self.id = id
        self.title = title
        self.description = description
        self.date = date
        self.user_id = user_id
        self.lata = lata
        self.longa = longa

class EventCreate(BaseModel):
    title: str
    description: str
    date: str
    user_id: int
    lata: float
    longa: str


class Message(BaseModel):
    id : int
    message : str
    sender : int
    reciver : int
class User(BaseModel):
    id: int
    username: str
    password: str
    phone : str
    lat: Optional[str] = None
    long: Optional[str] = None
    token: Optional[str] = None

    
class UserEvent(BaseModel):
    user_id: int
    event_id: int
    




