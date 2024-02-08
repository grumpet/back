from pydantic import BaseModel
class User(BaseModel):
    def __init__(self, id: int, username: str, password: str):
        self.id = id
        self.username = username
        self.password = password


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
    lata: str
    longa: str