from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.websockets import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from src.crud.chat import (initialization_chat_db, save_chat_message_db, save_first_chat_message_db,
                           save_message_file_db, save_message_files_db, save_moder_message_db, select_chat_db,
                           select_last_message_db, select_new_chat_messages_db, select_recipient_id,
                           select_student_recipient_db, update_chat_status_db, update_recipient_db)
from src.enums import ChatStatusType, StaticFileType, UserType
from src.models import UserOrm
from src.schemas.chat import InitializationChat
from src.session import get_db
from src.utils.chat_manager import ChatManager, serialize_messages, serialize_new_message
from src.utils.exceptions import PermissionDeniedException
from src.utils.get_user import get_current_user
from src.utils.save_files import save_file

router = APIRouter(prefix="/chat")
chat_manager = ChatManager()


@router.post("/initial-chat")
async def initialization_chat(
        data: InitializationChat,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.student.value:
        student_id = user.student.id
        if data.chat_subject:
            chat = initialization_chat_db(db=db, initiator_id=student_id, chat_subject=data.chat_subject)
            message = save_first_chat_message_db(db=db, message=data.message, sender_id=user.id, chat_id=chat.id)
            if data.files:
                for file in data.files:
                    save_message_file_db(db=db, message_id=message.id, data=file)

            return {"id": chat.id, "status": chat.status, "chat_subject": chat.chat_subject}

        else:
            words = data.message.split()
            if len(words) < 3:
                chat = initialization_chat_db(db=db, initiator_id=student_id, chat_subject=' '.join(words[:len(words)]))
            else:
                chat = initialization_chat_db(db=db, initiator_id=user.id, chat_subject=' '.join(words[:3]))

            message = save_first_chat_message_db(db=db, message=data.message, sender_id=user.id, chat_id=chat.id)

            if data.files:
                for file in data.files:
                    save_message_file_db(db=db, message_id=message.id, data=file)

            return {"id": chat.id, "status": chat.status, "chat_subject": chat.chat_subject}

    else:
        raise PermissionDeniedException()


@router.post("/upload/file")
async def upload_chat_file(file: UploadFile = File(...)):
    file_path = save_file(file=file, file_type=StaticFileType.chat_file.value)
    return {"file_path": file_path, "file_name": file.filename, "file_type": "docs", "file_size": file.size}


@router.websocket("/{chat_id}/{token}")
async def user_chat(
        chat_id: int,
        token: str,
        websocket: WebSocket,
        db: Session = Depends(get_db)
):
    user = get_current_user(db=db, access_token=token)
    chat = select_chat_db(db=db, chat_id=chat_id)

    if user.usertype == UserType.student.value:

        student_connection = chat_manager.create_student_connection(websocket=websocket, user_id=user.id)
        chat_manager.add_connection(chat_id=chat_id, user_connection=student_connection)
        try:
            await websocket.accept()

            messages = select_new_chat_messages_db(db=db, chat_id=chat_id)
            json_messages = serialize_messages(messages=messages, db=db)
            await websocket.send_json(json_messages)

            while True:
                data = await websocket.receive_json()

                if data.get("type") == "new-message":

                    if chat.status == ChatStatusType.new.value:
                        new_message = save_first_chat_message_db(
                            db=db, message=data["message"], sender_id=user.id, chat_id=chat_id
                        )

                        if data.get("files"):
                            save_message_files_db(db=db, files=data["files"], message_id=new_message.id)

                        last_message = select_last_message_db(db=db, message_id=new_message.id)
                        json_message = serialize_new_message(db=db, message=last_message)
                        await chat_manager.send_message(message=json_message, chat_id=chat_id, recipient="student")

                    if chat.status == ChatStatusType.active.value:
                        flag = chat_manager.check_moder_connection(chat_id=chat_id)

                        if flag:
                            moder_id = chat_manager.get_moder_id(chat_id=chat_id)
                            new_message = save_chat_message_db(
                                db=db, message=data["message"], sender_id=user.id,
                                chat_id=chat_id, recipient_id=moder_id
                            )

                            if data.get("files"):
                                save_message_files_db(db=db, files=data["files"], message_id=new_message.id)

                            last_message = select_last_message_db(db=db, message_id=new_message.id)
                            json_message = serialize_new_message(db=db, message=last_message)
                            await chat_manager.send_message(message=json_message, chat_id=chat_id, recipient="student")
                            await chat_manager.send_message(message=json_message, chat_id=chat_id, recipient="moder")

                        else:
                            moder_id = select_recipient_id(db=db, chat_id=chat_id)
                            new_message = save_chat_message_db(db=db, message=data["message"], sender_id=user.id,
                                                               chat_id=chat_id, recipient_id=moder_id)
                            if data.get("files"):
                                save_message_files_db(db=db, files=data["files"], message_id=new_message.id)

                            last_message = select_last_message_db(db=db, message_id=new_message.id)
                            json_message = serialize_new_message(db=db, message=last_message)
                            await chat_manager.send_message(message=json_message, chat_id=chat_id, recipient="student")

                elif data.get("type") == "approve":
                    message = {"data": {"message": "chat closed"}, "type": "approve"}
                    update_chat_status_db(db=db, chat_id=chat_id, status=ChatStatusType.archive.value)
                    await chat_manager.send_message(message=message, chat_id=chat_id, recipient="student")

                    flag = chat_manager.check_moder_connection(chat_id=chat_id)

                    if flag:
                        await chat_manager.send_message(message=message, chat_id=chat_id, recipient="moder")

                    await chat_manager.disconnect_chat(chat_id=chat_id)
                    break

                elif data.get("type") == "reject":
                    message = {"data": {"message": "chat staying active"}, "type": "reject"}
                    await chat_manager.send_message(message=message, chat_id=chat_id, recipient="student")
                    flag = chat_manager.check_moder_connection(chat_id=chat_id)

                    if flag:
                        await chat_manager.send_message(message=message, chat_id=chat_id, recipient="moder")

        except WebSocketDisconnect as e:
            print(f"Except – {e}")
        finally:
            chat_manager.delete_student_connection(chat_id=chat_id)

    else:
        moder_connection = chat_manager.create_moder_connection(websocket=websocket, user_id=user.id)
        chat_manager.add_connection(chat_id=chat_id, user_connection=moder_connection)
        try:
            if chat.status == ChatStatusType.new.value:
                update_recipient_db(db=db, chat_id=chat_id, recipient_id=user.id)
                update_chat_status_db(db=db, chat_id=chat_id, status=ChatStatusType.active.value)

            await websocket.accept()

            messages = select_new_chat_messages_db(db=db, chat_id=chat_id)
            json_messages = serialize_messages(messages=messages, db=db)
            await websocket.send_json(json_messages)

            while True:
                data = await websocket.receive_json()

                if data.get("type") == "new-message":
                    flag = chat_manager.check_student_connection(chat_id=chat_id)

                    if flag:
                        student_id = chat_manager.get_student_id(chat_id=chat_id)
                        new_message = save_moder_message_db(
                            db=db, message=data["message"], sender_id=user.id, chat_id=chat_id, recipient_id=student_id
                        )

                        if data.get("files"):
                            save_message_files_db(db=db, files=data["files"], message_id=new_message.id)

                        last_message = select_last_message_db(db=db, message_id=new_message.id)
                        json_message = serialize_new_message(db=db, message=last_message)
                        await chat_manager.send_message(message=json_message, chat_id=chat_id, recipient="moder")
                        await chat_manager.send_message(message=json_message, chat_id=chat_id, recipient="student")

                    else:
                        student_id = select_student_recipient_db(db=db, chat_id=chat_id)
                        new_message = save_moder_message_db(
                            db=db, message=data["message"], sender_id=user.id, chat_id=chat_id, recipient_id=student_id
                        )

                        if data.get("files"):
                            save_message_files_db(db=db, files=data["files"], message_id=new_message.id)

                        last_message = select_last_message_db(db=db, message_id=new_message.id)
                        json_message = serialize_new_message(db=db, message=last_message)
                        await chat_manager.send_message(message=json_message, chat_id=chat_id, recipient="moder")

                elif data.get("type") == "close-chat":
                    message = {"data": None, "type": "close-chat"}
                    await chat_manager.send_message(message=message, chat_id=chat_id, recipient="moder")

                    flag = chat_manager.check_student_connection(chat_id=chat_id)
                    if flag:
                        await chat_manager.send_message(message=message, chat_id=chat_id, recipient="student")

        except WebSocketDisconnect as e:
            print(f"Except – {e}")
        finally:
            chat_manager.delete_moder_connection(chat_id=chat_id)
