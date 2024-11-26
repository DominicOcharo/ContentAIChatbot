from pydantic import BaseModel
from typing import List, Dict

class CourseContent(BaseModel):
    module_title: str
    content_parts: List[Dict[str, str]]  # key-value pairs for modular content
