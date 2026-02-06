from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Request body schema
class Item(BaseModel):
    name: str
    price: float

# POST endpoint
@app.post("/obstacles")
def create_item(item: Item):
    return {
        "message": "Item received",
        "data": item
    }
