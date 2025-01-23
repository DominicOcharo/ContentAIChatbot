from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chatbot
import os
from dotenv import load_dotenv
from prometheus_client import make_asgi_app  # Prometheus integration

# Load environment variables
load_dotenv()

app = FastAPI()

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

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
