from stripe._util import convert_to_dict
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request, Header, HTTPException

from src.session import get_db
from src.utils.stripe_logic import (
    create_checkout,
    create_metadata,
    webhook_event,
    create_payment_intent,
    get_customer,
    create_ephemeral_key,
    retrieve_session,
    retrieve_payment_intent,
    retrieve_checkout_session
)
from src.celery_tasks import tasks
from src.crud.stripe import StripeCourseRepository
from src.crud.course import CourseRepository
from src.schemas.course import CourseCart
from src.crud.student_course import subscribe_student_to_course_db, create_student_lesson
from src.utils.check_discount import WebDiscount, MobileDiscount


router = APIRouter(prefix="/stripe")


@router.post("/cart")
async def change_card(
        data: CourseCart,
        db: Session = Depends(get_db)
):

    stripe_repository = StripeCourseRepository(db=db)
    price_ids = stripe_repository.select_price_ids(data.payment_items)

    coupon = None

    discount_manager = WebDiscount(db=db, cart=data.payment_items, student_id=data.student_id)
    result = discount_manager.check_discount()

    if result is not None and result.get("type") == "coupon":
        coupon = result["coupon"]

    metadata = create_metadata(
        student_id=data.student_id,
        payment_items=data.payment_items
    )

    checkout_link = create_checkout(
        price_ids=price_ids,
        metadata=metadata,
        coupon=coupon,
        success_url=data.success_url,
        cancel_url=data.cancel_url
    )

    return {"link": checkout_link}

@router.post("/course-subscribe/desktop")
async def course_subscribe_desktop(
        session_id: str,
        db: Session = Depends(get_db),
):
    metadata = retrieve_checkout_session(session_id)
    student_id = int(metadata["student_id"])
    items_id = []

    for key, value in metadata.items():
        if key.startswith("item"):
            course_id = int(value)
            items_id.append(course_id)

            subscribe_student_to_course_db(
                db=db,
                student_id=student_id,
                course_id=course_id
            )

            create_student_lesson(
                db=db,
                student_id=student_id,
                course_id=course_id
            )

    return {"status": "Successfully subscribed", "items": items_id}


@router.post("/course-subscribe/app")
async def course_subscribe_app(
        payment_intent: str,
        db: Session = Depends(get_db),
):
    metadata = retrieve_payment_intent(payment_intent)
    student_id = int(metadata["student_id"])
    items_id = []

    for key, value in metadata.items():
        if key.startswith("item"):
            course_id = int(value)
            items_id.append(course_id)

            subscribe_student_to_course_db(
                db=db,
                student_id=student_id,
                course_id=course_id
            )

            create_student_lesson(
                db=db,
                student_id=student_id,
                course_id=course_id
            )

    return {"status": "Successfully subscribed", "items": items_id}

@router.post("/mobile/cart")
async def change_cart_mobile(
        data: CourseCart,
        db: Session = Depends(get_db)
):
    course_repo = CourseRepository(db)
    cart_total = course_repo.select_cart_total_sum(data.payment_items)

    discount_manager = MobileDiscount(
        db=db,
        cart=data.payment_items,
        student_id=data.student_id
    )
    discount = discount_manager.check_discount()

    if discount:
        cart_total = cart_total - (cart_total * discount)

    customer_id = get_customer()

    metadata = create_metadata(
        student_id=data.student_id,
        payment_items=data.payment_items
    )

    intent_secret = create_payment_intent(
        amount=cart_total,
        metadata=metadata,
        customer_id=customer_id
    )

    ephemeral_key = create_ephemeral_key(customer_id)

    return {
        "paymentIntent": intent_secret,
        "customer": customer_id,
        "ephemeralKey": ephemeral_key
    }


@router.get("/success")
async def stripe_success(
        session_id: str
):
    return retrieve_session(session_id)


@router.post("/webhook")
async def stripe_webhook(
        event: dict,
        request: Request,
        stripe_signature=Header(None),
        db: Session = Depends(get_db)
):
    raw_body = await request.body()

    try:
        event = webhook_event(body=raw_body, stripe_signature=stripe_signature)
    except Exception as e:
        raise HTTPException(422, detail=str(e))

    # data = event["data"]["object"]
    # if event["type"] == "checkout.session.completed":
    #     metadata = convert_to_dict(data["metadata"])
    #     student_id = int(metadata["student_id"])
    #
    #     for key, value in metadata.items():
    #         if key.startswith("item"):
    #             course_id = int(value)
    #             subscribe_student_to_course_db(
    #                 db=db,
    #                 student_id=student_id,
    #                 course_id=course_id
    #             )
    #
    #             tasks.create_student_lesson.delay(
    #                 student_id=student_id,
    #                 course_id=course_id
    #             )
