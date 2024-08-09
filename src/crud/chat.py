from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from src.enums import ChatStatusType, MessageSenderType
from src.models import ChatMessageOrm, ChatOrm, MessageFilesOrm
from src.schemas.chat import MessageFile


def initialization_chat_db(db: Session, chat_subject: str, initiator_id: int):
    new_chat = ChatOrm(chat_subject=chat_subject, status=ChatStatusType.new.value, initiator_id=initiator_id)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat


def save_first_chat_message_db(db: Session, message: str, sender_id: int, chat_id: int):
    new_message = ChatMessageOrm(
        message=message,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        chat_id=chat_id,
        sender_id=sender_id,
        sender_type=MessageSenderType.student.value,
        recipient_type=MessageSenderType.admin.value
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message


def save_chat_message_db(db: Session, message: str, sender_id: int, chat_id: int, recipient_id: int):
    new_message = ChatMessageOrm(
        message=message,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        chat_id=chat_id,
        sender_id=sender_id,
        sender_type=MessageSenderType.student.value,
        recipient_id=recipient_id,
        recipient_type=MessageSenderType.admin.value
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message


def save_moder_message_db(db: Session, message: str, sender_id: int, chat_id: int, recipient_id: int):
    new_message = ChatMessageOrm(
        message=message,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        chat_id=chat_id,
        sender_id=sender_id,
        sender_type=MessageSenderType.admin.value,
        recipient_id=recipient_id,
        recipient_type=MessageSenderType.student.value
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message


def save_message_file_db(db: Session, data: MessageFile, message_id: int):
    new_file = MessageFilesOrm(
        file_type=data.file_type,
        file_name=data.file_name,
        file_path=data.file_path,
        file_size=data.file_size,
        message_id=message_id
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return new_file


def save_message_files_db(db: Session, files: list, message_id: int):
    for file in files:
        new_file = MessageFilesOrm(
            file_type=file["file_type"],
            file_name=file["file_name"],
            file_path=file["file_path"],
            file_size=file["file_size"],
            message_id=message_id
        )
        db.add(new_file)
    db.commit()


def select_new_chat_messages_db(db: Session, chat_id: int):
    return (db.query(ChatMessageOrm)
            .filter(ChatMessageOrm.chat_id == chat_id)
            .options(joinedload(ChatMessageOrm.files))
            .order_by(desc(ChatMessageOrm.timestamp))
            .all())


def select_chat_db(db: Session, chat_id: int):
    return db.query(ChatOrm).filter(ChatOrm.id == chat_id).first()


def select_recipient_id(db: Session, chat_id: int):
    res = (db.query(ChatMessageOrm)
           .filter(ChatMessageOrm.chat_id == chat_id,
                   ChatMessageOrm.recipient_type == MessageSenderType.admin.value,
                   ChatMessageOrm.recipient_id.is_(not None))
           .first())
    return res.recipient_id


def select_student_recipient_db(db: Session, chat_id: int):
    res = (db.query(ChatMessageOrm)
           .filter(ChatMessageOrm.chat_id == chat_id,
                   ChatMessageOrm.recipient_type == MessageSenderType.admin.value)
           .first())
    return res.sender_id


def select_last_message_db(db: Session, message_id: int):
    return (db.query(ChatMessageOrm)
            .filter(ChatMessageOrm.id == message_id)
            .options(joinedload(ChatMessageOrm.files))
            .first())


def select_chats_for_moderator(db: Session, user_id: int):
    common_chats = (db.query(ChatOrm)
                    .filter(ChatOrm.status.in_([ChatStatusType.new.value, ChatStatusType.archive.value]))
                    .all())

    personal_chats = (db.query(ChatOrm)
                      .join(ChatMessageOrm, ChatMessageOrm.chat_id == ChatOrm.id)
                      .filter(ChatMessageOrm.recipient_id == user_id)
                      .filter(ChatOrm.status == ChatStatusType.active)
                      .all())

    return common_chats + personal_chats


def check_active_chat(db: Session, user_id: int):
    result = (db.query(ChatOrm)
              .join(ChatMessageOrm, ChatMessageOrm.chat_id == ChatOrm.id)
              .filter(ChatMessageOrm.recipient_id == user_id)
              .all())

    return False if result else True


def update_recipient_db(db: Session, chat_id: int, recipient_id: int):
    messages = (db.query(ChatMessageOrm)
                .filter(ChatMessageOrm.chat_id == chat_id,
                        ChatMessageOrm.sender_type == MessageSenderType.student.value,
                        ChatMessageOrm.recipient_id.is_(None))
                .all())

    for message in messages:
        message.recipient_id = recipient_id
    db.commit()


def update_chat_status_db(db: Session, chat_id: int, status: ChatStatusType):
    chat = db.query(ChatOrm).filter(ChatOrm.id == chat_id).first()
    chat.status = status
    db.commit()
    db.refresh(chat)
