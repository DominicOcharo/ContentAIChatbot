from fastapi import APIRouter, Form, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from detectors.groq_client import (
    update_course_content, 
    generate_response, 
    get_all_content, 
    delete_course_content, 
    edit_course_content
)

router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"],
)

# Pydantic model for adding or editing course content
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
    if not module_title.strip():
        raise HTTPException(status_code=400, detail="Module title must be provided.")

    # Find the module or create a new one
    all_content = get_all_content()
    new_module = next((m for m in all_content if m['module_title'] == module_title), None)
    
    if not new_module:
        new_module = {
            "module_title": module_title,
            "content_parts": []
        }
        update_course_content(new_module)

    # Create a dynamic key for the new content parts
    existing_keys = [item["key"] for item in new_module['content_parts']]
    if content_parts:
        for part in content_parts:
            # Determine the next index for the specific key_prefix
            matching_keys = [key for key in existing_keys if key.startswith(f"{key_prefix}_")]
            next_index = len(matching_keys) + 1
            key = f"{key_prefix}_{next_index}"
            new_module['content_parts'].append({"key": key, "value": part})

    return {"status": True, "message": "Module content updated successfully", "data": new_module}


@router.get("/get-content")
async def get_content(module_title: Optional[str] = None):
    """API to get all or specific module content."""
    content = get_all_content()
    if module_title:
        module = next((m for m in content if m['module_title'] == module_title), None)
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        return {"status": True, "message": "Module content fetched successfully", "data": module}
    return {"status": True, "message": "Content fetched successfully", "data": content}


@router.delete("/delete-content/{module_title}")
async def delete_content(module_title: str, key: Optional[str] = None):
    """API to delete a module or specific content by title and key."""
    try:
        delete_course_content(module_title, key)
        if key:
            return {"status": True, "message": f"Content with key '{key}' deleted successfully"}
        return {"status": True, "message": f"Module '{module_title}' deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/edit-content")
async def edit_content(
    module_title: str = Form(...),
    key: str = Form(...),
    new_value: str = Form(...),
):
    """API to edit specific content within a module."""
    try:
        edited_module = edit_course_content(module_title, key, new_value)
        return {"status": True, "message": "Content updated successfully", "data": edited_module}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/ask-question")
async def ask_question(
    query: str = Form(...)
):
    """API to ask a question based on the course content."""
    
    # Ensure the query is not empty
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    response = generate_response(query)
    if response:
        return {"status": True, "message": "Query answered", "data": {"response": response}}
    
    raise HTTPException(status_code=500, detail="Error generating response.")
