from groq import Groq
import os
from typing import Optional

# Initialize Groq client with the API key from .env
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Global variable to store dynamic course content
course_modules = []

course_modules = []  # Updated structure to support nested content

def update_course_content(new_module: dict):
    """Update global course content dynamically by adding new modules."""
    global course_modules
    course_modules.append(new_module)

def get_all_content():
    """Return all the course content."""
    return course_modules

def delete_course_content(module_title: str, key: Optional[str] = None):
    """Delete a module or specific key-value content within a module."""
    global course_modules
    for module in course_modules:
        if module['module_title'] == module_title:
            if key:
                module['content_parts'] = [
                    item for item in module['content_parts'] if item['key'] != key
                ]
            else:
                course_modules = [mod for mod in course_modules if mod['module_title'] != module_title]
            return
    raise ValueError("Module or key not found")

def edit_course_content(module_title: str, key: str, new_value: str):
    """Edit specific content within a module by title and key."""
    global course_modules
    for module in course_modules:
        if module['module_title'] == module_title:
            for item in module['content_parts']:
                if item['key'] == key:
                    item['value'] = new_value
                    return module
    raise ValueError("Module or key not found")


def create_system_prompt():
    """Create a system prompt with the current course content."""
    if not course_modules:
        return "No course content available."
    
    # Combine all module contents
    combined_content = "\n\n".join([f"Module {i+1}: {module}" for i, module in enumerate(course_modules)])
    
    return f"You are a knowledgeable assistant. You can only answer questions based on the course content provided and take the whole content as correct. If the query is outside the content, respond with 'I cannot answer that as it is outside the scope of the provided content.' Here is the course content:\n\n{combined_content}"

def generate_response(user_query):
    # Ensure course content exists before generating responses
    if not course_modules:
        return "No course content available. Please update the content before asking questions."

    # Create a stream of completions based on the user's query and course content
    stream = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": create_system_prompt()
            },
            {
                "role": "user",
                "content": user_query
            }
        ],
        model="llama-3.1-70b-versatile",
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        stop=None,
        stream=True,
    )

    response = ""
    # Output the response as it streams in
    for chunk in stream:
        delta_content = chunk.choices[0].delta.content
        if delta_content is not None:
            response += delta_content

    return response
