from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Create a router for CRUD operations
router = APIRouter()

# In-memory data store (replace with a database in a real application)
items = [
    {"id": 1, "name": "Item 1", "description": "This is item 1"},
    {"id": 2, "name": "Item 2", "description": "This is item 2"},
]

# Define the model for the data
class Item(BaseModel):
    id: int
    name: str
    description: str

# Create
@router.post("/items/")
async def create_item(item: Item):
    items.append(item.dict())
    return {"message": "Item created successfully"}

# Read all items
@router.get("/items/")
async def read_items():
    return items

# Read a single item
@router.get("/items/{item_id}")
async def read_item(item_id: int):
    for item in items:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

# Delete
@router.delete("/items/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(items):
        if item["id"] == item_id:
            del items[i]
            return {"message": "Item deleted successfully"}
    raise HTTPException(status_code=404, detail="Item not found")
