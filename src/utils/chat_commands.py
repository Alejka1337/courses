import asyncio
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.utils.chat_manager import (
    ChatManager,
    serialize_new_message
)

from src.models import ChatOrm, UserOrm
from src.enums import ChatStatusType
from src.crud.chat import (
    save_chat_message_db,
    save_message_files_db,
    save_moder_message_db,
    select_last_message_db,
    select_recipient_id,
    select_student_recipient_db,
    update_chat_status_db,
    select_chat_db
)


class ChatMessageHandler(ABC):
    def __init__(
            self,
            connection_manager: ChatManager,
            current_chat: ChatOrm,
            data: dict,
            user: UserOrm,
            db: Session
    ):
        self._conn_manager = connection_manager
        self._chat = current_chat
        self._data = data
        self._user = user
        self._db = db

    @abstractmethod
    async def handle_message(self):
        pass


class NewMessageHandler(ChatMessageHandler):

    async def handle_message(self):
        if self._user.is_student:
            await self.handle_student_message()
        else:
            await self.handle_moderator_message()

    async def handle_student_message(self):
        chat = select_chat_db(
            db=self._db,
            chat_id=self._chat.id
        )

        if chat.status == ChatStatusType.new.value and chat.messages[0].recipient_id is None:
            new_message = save_chat_message_db(
                db=self._db,
                message=self._data["message"],
                sender_id=self._user.id,
                chat_id=self._chat.id
            )

        else:
            moder_conn = self._conn_manager.check_moder_connection(chat_id=self._chat.id)

            if moder_conn:
                moder_id = self._conn_manager.get_moder_id(chat_id=self._chat.id)
            else:
                moder_id = select_recipient_id(
                    db=self._db,
                    chat_id=self._chat.id
                )

            new_message = save_chat_message_db(
                db=self._db,
                message=self._data["message"],
                sender_id=self._user.id,
                chat_id=self._chat.id,
                recipient_id=moder_id
            )

        if self._data.get("files"):
            save_message_files_db(
                db=self._db,
                files=self._data["files"],
                message_id=new_message.id
            )

        last_message = select_last_message_db(
            db=self._db,
            message_id=new_message.id
        )

        json_message = serialize_new_message(
            db=self._db,
            message=last_message
        )

        await self._conn_manager.send_message(
            message=json_message,
            chat_id=self._chat.id,
            recipient="student"
        )

        moder_conn = self._conn_manager.check_moder_connection(chat_id=self._chat.id)

        if moder_conn:
            await self._conn_manager.send_message(
                message=json_message,
                chat_id=self._chat.id,
                recipient="moder"
            )

    async def handle_moderator_message(self):
        student_conn = self._conn_manager.check_student_connection(chat_id=self._chat.id)

        if student_conn:
            student_id = self._conn_manager.get_student_id(chat_id=self._chat.id)

        else:
            student_id = select_student_recipient_db(
                db=self._db,
                chat_id=self._chat.id
            )

        new_message = save_moder_message_db(
            db=self._db,
            message=self._data["message"],
            sender_id=self._user.id,
            chat_id=self._chat.id,
            recipient_id=student_id
        )

        if self._data.get("files"):
            save_message_files_db(
                db=self._db,
                files=self._data["files"],
                message_id=new_message.id
            )

        last_message = select_last_message_db(
            db=self._db,
            message_id=new_message.id
        )

        json_message = serialize_new_message(
            db=self._db,
            message=last_message
        )

        await self._conn_manager.send_message(
            message=json_message,
            chat_id=self._chat.id,
            recipient="moder"
        )

        if student_conn:
            await self._conn_manager.send_message(
                message=json_message,
                chat_id=self._chat.id,
                recipient="student"
            )


class ApproveMessageHandler(ChatMessageHandler):

    async def handle_message(self):
        message = {"data": {"message": "chat closed"}, "type": "approve"}

        update_chat_status_db(
            db=self._db,
            chat_id=self._chat.id,
            status=ChatStatusType.archive.value
        )

        moder_conn = self._conn_manager.check_moder_connection(chat_id=self._chat.id)

        if moder_conn:
            await self._conn_manager.send_message(
                message=message,
                chat_id=self._chat.id,
                recipient="moder"
            )

        await self._conn_manager.send_message(
            message=message,
            chat_id=self._chat.id,
            recipient="student"
        )

        await self._conn_manager.disconnect_chat(chat_id=self._chat.id)


class RejectMessageHandler(ChatMessageHandler):

    async def handle_message(self):
        message = {"data": {"message": "chat staying active"}, "type": "reject"}

        await self._conn_manager.send_message(
            message=message,
            chat_id=self._chat.id,
            recipient="student"
        )

        moder_conn = self._conn_manager.check_moder_connection(chat_id=self._chat.id)

        if moder_conn:
            await self._conn_manager.send_message(
                message=message,
                chat_id=self._chat.id,
                recipient="moder"
            )


class CloseChatMessageHandler(ChatMessageHandler):

    async def handle_message(self):
        message = {"data": None, "type": "close-chat"}

        await self._conn_manager.send_message(
            message=message,
            chat_id=self._chat.id,
            recipient="moder"
        )

        student_conn = self._conn_manager.check_student_connection(chat_id=self._chat.id)

        if student_conn:
            await self._conn_manager.send_message(
                message=message,
                chat_id=self._chat.id,
                recipient="student"
            )

        else:
            await asyncio.sleep(10)

            update_chat_status_db(
                db=self._db,
                chat_id=self._chat.id,
                status=ChatStatusType.archive.value
            )

            await self._conn_manager.disconnect_chat(chat_id=self._chat.id)
