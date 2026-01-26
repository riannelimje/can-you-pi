from fastapi import FastAPI
from .routes import router

app = FastAPI(title ="Can You Pi?")
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Can You Pi?"}

