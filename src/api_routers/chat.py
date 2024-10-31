import logging

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.exceptions import WebSocketException
from fastapi.websockets import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from src.crud.chat import (
    check_active_chat,
    initialization_chat_db,
    save_first_chat_message_db,
    save_message_file_db,
    select_chat_db,
    select_new_chat_messages_db,
    update_chat_status_db,
    update_recipient_db
)
from src.enums import ChatStatusType, StaticFileType
from src.models import UserOrm
from src.schemas.chat import InitializationChat
from src.session import get_db
from src.utils.chat_manager import (
    ChatManager,
    serialize_messages,
)

from src.utils.exceptions import PermissionDeniedException
from src.utils.get_user import get_current_user
from src.utils.save_files import save_file
from src.utils.chat_commands import (
    NewMessageHandler,
    RejectMessageHandler,
    ApproveMessageHandler,
    CloseChatMessageHandler
)


router = APIRouter(prefix="/chat")
chat_manager = ChatManager()

logging.basicConfig()
logging.getLogger("Websocket").setLevel(logging.INFO)


@router.post("/initial-chat")
async def initialization_chat(
        data: InitializationChat,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if not user.is_student:
        raise PermissionDeniedException()

    student_id = user.student.id

    if data.chat_subject:
        chat = initialization_chat_db(
            db=db,
            initiator_id=student_id,
            chat_subject=data.chat_subject
        )

        message = save_first_chat_message_db(
            db=db,
            message=data.message,
            sender_id=user.id,
            chat_id=chat.id
        )

        if data.files:
            for file in data.files:
                save_message_file_db(
                    db=db,
                    message_id=message.id,
                    data=file
                )

        return {"id": chat.id, "status": chat.status, "chat_subject": chat.chat_subject}

    else:
        words = data.message.split()
        if len(words) < 3:
            chat = initialization_chat_db(
                db=db,
                initiator_id=student_id,
                chat_subject=' '.join(words[:len(words)])
            )

        else:
            chat = initialization_chat_db(
                db=db,
                initiator_id=user.id,
                chat_subject=' '.join(words[:3])
            )

        message = save_first_chat_message_db(
            db=db,
            message=data.message,
            sender_id=user.id,
            chat_id=chat.id
        )

        if data.files:
            for file in data.files:
                save_message_file_db(
                    db=db,
                    message_id=message.id,
                    data=file
                )

        return {"id": chat.id, "status": chat.status, "chat_subject": chat.chat_subject}


@router.post("/upload/file")
async def upload_chat_file(file: UploadFile = File(...)):
    file_path = save_file(
        file=file,
        file_type=StaticFileType.chat_file.value
    )

    return {
        "file_path": file_path,
        "file_name": file.filename,
        "file_type": "docs",
        "file_size": file.size
    }


@router.websocket("/user/{chat_id}/{token}")
async def user_chat(
        chat_id: int,
        token: str,
        websocket: WebSocket,
        db: Session = Depends(get_db)
):
    user = get_current_user(
        db=db,
        access_token=token
    )

    chat = select_chat_db(
        db=db,
        chat_id=chat_id
    )

    student_connection = chat_manager.create_student_connection(
        websocket=websocket,
        user_id=user.id
    )
    chat_manager.add_connection(
        chat_id=chat_id,
        user_connection=student_connection
    )

    try:
        await websocket.accept()

        messages = select_new_chat_messages_db(
            db=db,
            chat_id=chat_id
        )

        json_messages = serialize_messages(
            messages=messages,
            db=db
        )
        await websocket.send_json(json_messages)

        while True:
            data = await websocket.receive_json()

            if data.get("type") == "new-message":
                handler = NewMessageHandler(
                    connection_manager=chat_manager,
                    current_chat=chat,
                    data=data,
                    user=user,
                    db=db
                )

                await handler.handle_message()

            if data.get("type") == "approve":
                handler = ApproveMessageHandler(
                    connection_manager=chat_manager,
                    current_chat=chat,
                    data=data,
                    user=user,
                    db=db
                )

                await handler.handle_message()
                break

            if data.get("type") == "reject":
                handler = RejectMessageHandler(
                    connection_manager=chat_manager,
                    current_chat=chat,
                    data=data,
                    user=user,
                    db=db
                )

                await handler.handle_message()

    except WebSocketDisconnect as e:
        print(f"Except – {e}")
    finally:
        chat_manager.delete_student_connection(chat_id=chat_id)


@router.websocket("/admin/{chat_id}/{token}")
async def moder_chat(
        chat_id: int,
        token: str,
        websocket: WebSocket,
        db: Session = Depends(get_db)
):
    user = get_current_user(
        db=db,
        access_token=token
    )

    chat = select_chat_db(
        db=db,
        chat_id=chat_id
    )

    if chat.status == ChatStatusType.new.value:
        update_recipient_db(
            db=db,
            chat_id=chat_id,
            recipient_id=user.id
        )
        update_chat_status_db(
            db=db,
            chat_id=chat_id,
            status=ChatStatusType.active.value
        )

    moder_connection = chat_manager.create_moder_connection(
        websocket=websocket,
        user_id=user.id
    )

    chat_manager.add_connection(
        chat_id=chat_id,
        user_connection=moder_connection
    )

    try:
        await websocket.accept()

        if chat.status == ChatStatusType.active.value and check_active_chat(db=db, user_id=user.id):
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Other admin helping this student"
            )

        messages = select_new_chat_messages_db(db=db, chat_id=chat_id)
        json_messages = serialize_messages(messages=messages, db=db)
        await websocket.send_json(json_messages)

        while True:
            data = await websocket.receive_json()

            if data.get("type") == "new-message":
                handler = NewMessageHandler(
                    connection_manager=chat_manager,
                    current_chat=chat,
                    data=data,
                    user=user,
                    db=db
                )

                await handler.handle_message()

            if data.get("type") == "close-chat":
                handler = CloseChatMessageHandler(
                    connection_manager=chat_manager,
                    current_chat=chat,
                    data=data,
                    user=user,
                    db=db
                )

                await handler.handle_message()

    except WebSocketDisconnect as e:
        print(f"Except – {e.code}, {e.reason}")

    except RuntimeError as run_e:
        print(run_e)

    finally:
        chat_manager.delete_moder_connection(chat_id=chat_id)
