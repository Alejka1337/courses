from typing import List, Optional

from pydantic import BaseModel


class MessageFile(BaseModel):
    file_type: str
    file_name: str
    file_path: str
    file_size: int


class InitializationChat(BaseModel):
    chat_subject: Optional[str] = None
    message: str
    files: Optional[List[MessageFile]] = None
