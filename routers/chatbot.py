from fastapi import APIRouter, Form, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import time
from detectors.groq_client import (
    update_course_content, 
    generate_response, 
    get_all_content, 
    delete_course_content, 
    edit_course_content
)
from prometheus_client import Counter, Histogram  # Prometheus metrics

router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"],
)

# Prometheus Metrics 
CHATBOT_REQUESTS = Counter(
    'chatbot_requests_total',
    'Total chatbot requests',
    ['endpoint', 'status']
)

CONTENT_UPDATES = Counter(
    'content_updates_total',
    'Total course content updates'
)

RESPONSE_TIME = Histogram(
    'chatbot_response_time_seconds',
    'Chatbot response generation time',
    ['endpoint']
)

class ModuleContent(BaseModel):
    module_title: str
    content_parts: Optional[List[str]] = None

@router.post("/update-content")
async def update_content(
    module_title: str = Form(...),
    key_prefix: str = Form("content"),
    content_parts: Optional[List[str]] = Form(None),
):
    """API to add or update a module's content dynamically."""
    try:
        if not module_title.strip():
            raise HTTPException(status_code=400, detail="Module title must be provided.")

        all_content = get_all_content()
        new_module = next((m for m in all_content if m['module_title'] == module_title), None)
        
        if not new_module:
            new_module = {
                "module_title": module_title,
                "content_parts": []
            }
            update_course_content(new_module)

        if content_parts:
            existing_keys = [item["key"] for item in new_module['content_parts']]
            for part in content_parts:
                matching_keys = [key for key in existing_keys if key.startswith(f"{key_prefix}_")]
                next_index = len(matching_keys) + 1
                key = f"{key_prefix}_{next_index}"
                new_module['content_parts'].append({"key": key, "value": part})

        CONTENT_UPDATES.inc()  # Track content updates
        return {"status": True, "message": "Module content updated successfully", "data": new_module}
    
    except Exception as e:
        CHATBOT_REQUESTS.labels(endpoint="update-content", status="error").inc()
        raise

@router.get("/get-content")
async def get_content(module_title: Optional[str] = None):
    """API to get all or specific module content."""
    try:
        content = get_all_content()
        if module_title:
            module = next((m for m in content if m['module_title'] == module_title), None)
            if not module:
                raise HTTPException(status_code=404, detail="Module not found")
        return {"status": True, "message": "Content fetched successfully", "data": content}
    except Exception as e:
        CHATBOT_REQUESTS.labels(endpoint="get-content", status="error").inc()
        raise

@router.delete("/delete-content/{module_title}")
async def delete_content(module_title: str, key: Optional[str] = None):
    """API to delete a module or specific content by title and key."""
    try:
        delete_course_content(module_title, key)
        CONTENT_UPDATES.inc()  # Track deletions as updates
        if key:
            return {"status": True, "message": f"Content with key '{key}' deleted successfully"}
        return {"status": True, "message": f"Module '{module_title}' deleted successfully"}
    except Exception as e:
        CHATBOT_REQUESTS.labels(endpoint="delete-content", status="error").inc()
        raise

@router.put("/edit-content")
async def edit_content(
    module_title: str = Form(...),
    key: str = Form(...),
    new_value: str = Form(...),
):
    """API to edit specific content within a module."""
    try:
        edited_module = edit_course_content(module_title, key, new_value)
        CONTENT_UPDATES.inc()  # Track edits as updates
        return {"status": True, "message": "Content updated successfully", "data": edited_module}
    except Exception as e:
        CHATBOT_REQUESTS.labels(endpoint="edit-content", status="error").inc()
        raise

@router.post("/ask-question")
async def ask_question(
    query: str = Form(...)
):
    """API to ask a question based on the course content."""
    start_time = time.time()
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty.")
        
        response = generate_response(query)
        
        if response:
            # Track successful request and response time
            CHATBOT_REQUESTS.labels(endpoint="ask-question", status="success").inc()
            RESPONSE_TIME.labels(endpoint="ask-question").observe(time.time() - start_time)
            return {"status": True, "message": "Query answered", "data": {"response": response}}
        
        raise HTTPException(status_code=500, detail="Error generating response.")
    
    except Exception as e:
        # Track failed request
        CHATBOT_REQUESTS.labels(endpoint="ask-question", status="error").inc()
        raise
