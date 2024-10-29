from fastapi.websockets import WebSocket
from sqlalchemy.orm import Session

from src.crud.user import UserRepository
from src.enums import MessageSenderType
from src.models import ChatMessageOrm


class ChatManager:
    connections = {}

    @staticmethod
    def create_student_connection(websocket: WebSocket, user_id: int) -> dict:
        connection = {"student": "student", "student_websocket": websocket, "student_id": user_id}
        return connection

    @staticmethod
    def create_moder_connection(websocket: WebSocket, user_id: int) -> dict:
        connection = {"moder": "moder", "moder_websocket": websocket, "moder_id": user_id}
        return connection

    def add_connection(self, chat_id: int, user_connection: dict) -> None:
        if chat_id not in self.connections:
            self.connections[chat_id] = user_connection

        else:
            if "student" in user_connection:
                self.connections[chat_id].setdefault("student", user_connection["student"])
                self.connections[chat_id]["student_websocket"] = user_connection["student_websocket"]
                self.connections[chat_id]["student_id"] = user_connection["student_id"]

            elif "moder" in user_connection:
                self.connections[chat_id].setdefault("moder", user_connection["moder"])
                self.connections[chat_id]["moder_websocket"] = user_connection["moder_websocket"]
                self.connections[chat_id]["moder_id"] = user_connection["moder_id"]

    def check_moder_connection(self, chat_id: int) -> bool:
        return "moder" in self.connections.get(chat_id, {})

    def check_student_connection(self, chat_id: int) -> bool:
        return "student" in self.connections.get(chat_id, {})

    def get_moder_id(self, chat_id: int) -> int:
        chat = self.connections[chat_id]
        return chat["moder_id"]

    def get_student_id(self, chat_id: int) -> int:
        chat = self.connections[chat_id]
        return chat["student_id"]

    async def send_message(self, message: dict, chat_id: int, recipient: str) -> None:
        chat = self.connections[chat_id]
        if recipient == "student" and "student_websocket" in chat:
            await chat["student_websocket"].send_json(message)

        if recipient == "moder" and "moder_websocket" in chat:
            await chat["moder_websocket"].send_json(message)

    async def disconnect_chat(self, chat_id: int) -> None:
        chat = self.connections[chat_id]

        if chat.get("student_websocket"):
            await chat["student_websocket"].close()

        if chat.get("moder_websocket"):
            await chat["moder_websocket"].close()

    def delete_moder_connection(self, chat_id: int) -> None:
        chat = self.connections[chat_id]
        chat.pop("moder")
        chat.pop("moder_id")
        chat.pop("moder_websocket")

    def delete_student_connection(self, chat_id: int) -> None:
        chat = self.connections[chat_id]
        chat.pop("student")
        chat.pop("student_id")
        chat.pop("student_websocket")


def serialize_messages(db: Session, messages: list[ChatMessageOrm]):
    result = []
    user_repository = UserRepository(db=db)

    for message in messages:
        message_data = get_message_data(message)

        user_avatar = user_repository.select_student_image_db(user_id=message.sender_id)
        message_data["user_image"] = user_avatar.path if user_avatar else None

        if message.sender_type == MessageSenderType.student.value:
            fullname = user_repository.select_student_fullname_db(user_id=message.sender_id)
            message_data["fullname"] = fullname
        else:
            fullname = user_repository.select_moder_fullname_db(user_id=message.sender_id)
            message_data["fullname"] = fullname

        result.append(message_data)

    return {"data": result, "type": "chat-history"}


def serialize_new_message(db: Session, message: ChatMessageOrm):
    message_data = get_message_data(message)
    user_repository = UserRepository(db=db)

    user_avatar = user_repository.select_student_image_db(user_id=message.sender_id)
    message_data["user_image"] = user_avatar.path if user_avatar else None

    if message.sender_type == MessageSenderType.student.value:
        fullname = user_repository.select_student_fullname_db(user_id=message.sender_id)
        message_data["fullname"] = fullname
    else:
        fullname = user_repository.select_moder_fullname_db(user_id=message.sender_id)
        message_data["fullname"] = fullname

    return {"data": message_data, "type": "new-message"}


def get_message_data(message: ChatMessageOrm) -> dict:
    message_data = {
        "id": message.id,
        "message": message.message,
        "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "sender_id": message.sender_id,
        "sender_type": message.sender_type.value,
        "recipient_id": message.recipient_id,
        "recipient_type": message.recipient_type.value,
        "files": [
            {
                "file_path": file.file_path,
                "file_type": file.file_type,
                "file_name": file.file_name,
                "file_size": file.file_size
            }
            for file in message.files if message.files
        ]
    }

    return message_data
