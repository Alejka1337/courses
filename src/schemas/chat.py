from typing import List, Optional

from pydantic import BaseModel, PositiveInt


class MessageFile(BaseModel):
    file_type: str
    file_name: str
    file_path: str
    file_size: PositiveInt


class InitializationChat(BaseModel):
    chat_subject: Optional[str] = None
    message: str
    files: Optional[List[MessageFile]] = None
