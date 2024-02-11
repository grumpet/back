from pydantic import BaseModel
from typing import List, Optional


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
    
    
class User(BaseModel):
    id: int
    username: str
    password: str
    lat: Optional[str] = None
    long: Optional[str] = None
    events: Optional [List[Event]] = []
