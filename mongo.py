from fastapi import FastAPI, HTTPException, Body
from typing import List
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from pydantic import BaseModel, Field, HttpUrl, conlist, confloat

app = FastAPI()

# MongoDB connection
client = MongoClient("mongodb+srv://admin:asdfqwer1234@map.xkbb8us.mongodb.net/?retryWrites=true&w=majority")
db = client["Events"]
events_collection: Collection = db["events"]

# Model for the Event
class Event(BaseModel):
    name: str = Field(title="Name of the event")
    description: str = Field(title="Description of the event")

# CRUD Operations

# Create
@app.post("/events/", response_model=Event)
async def create_event(event: Event = Body(...)):
    try:
        event_dict = event.dict()
        events_collection.insert_one(event_dict)
        return event
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Event with this location already exists")

# Read
@app.get("/events/", response_model=List[Event])
async def read_events():
    events = list(events_collection.find())
    return events

@app.get("/events/{event_id}", response_model=Event)
async def read_event(event_id: str):
    event = events_collection.find_one({"_id": event_id})
    if event:
        return event
    raise HTTPException(status_code=404, detail="Event not found")

# Update
@app.put("/events/{event_id}", response_model=Event)
async def update_event(event_id: str, event: Event = Body(...)):
    updated_event = event.dict()
    result = events_collection.update_one({"_id": event_id}, {"$set": updated_event})
    if result.modified_count == 1:
        return event
    raise HTTPException(status_code=404, detail="Event not found")

# Delete
@app.delete("/events/{event_id}", response_model=dict)
async def delete_event(event_id: str):
    result = events_collection.delete_one({"_id": event_id})
    if result.deleted_count == 1:
        return {"message": "Event deleted successfully"}
    raise HTTPException(status_code=404, detail="Event not found")
