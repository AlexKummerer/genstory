from fastapi import Depends, FastAPI
from app.api import auth, characters, stories, users


app = FastAPI()

app.include_router(characters.router, prefix="/characters", tags=["characters"])
app.include_router(stories.router, prefix="/stories", tags=["stories"])
app.include_router(auth.router, prefix="", tags=["auth"])
app.include_router(users.router, prefix="", tags=["users"])


@app.get("/")
def read_root():
    return {"message": "Welcome to the API!"}
