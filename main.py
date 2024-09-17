from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Define the model for the data
class Item(BaseModel):
    id: int
    name: str
    description: str

# In-memory data store (replace with a database in a real application)
items = [
    {"id": 1, "name": "Item 1", "description": "This is item 1"},
    {"id": 2, "name": "Item 2", "description": "This is item 2"},
]
# Root
@app.get("/")
async def root():
    return "working"

# Create
@app.post("/items/")
async def create_item(item: Item):
    items.append(item.dict())
    return {"message": "Item created successfully"}

# Read
@app.get("/items/")
async def read_items():
    return items

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    for item in items:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

# Update
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    for i, existing_item in enumerate(items):
        if existing_item["id"] == item_id:
            items[i] = item.dict()
            return {"message": "Item updated successfully"}
    raise HTTPException(status_code=404, detail="Item not found")

# Delete
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(items):
        if item["id"] == item_id:
            del items[i]
            return {"message": "Item deleted successfully"}
    raise HTTPException(status_code=404, detail="Item not found")