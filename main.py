from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chatbot
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

# Include the chatbot router
app.include_router(chatbot.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the course chatbot API"}
