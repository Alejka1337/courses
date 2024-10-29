import stripe

from src.config import STRIPE_SECRET_KEY, DOMAIN, STRIPE_WEBHOOK
from src.utils.course_price_convert import convert_float_to_price

stripe.api_key = STRIPE_SECRET_KEY


def create_new_product(name, image_path):
    if image_path:
        image = f"{DOMAIN}/{image_path}"
        stripe_product = stripe.Product.create(name=name, images=[image,])
    else:
        stripe_product = stripe.Product.create(name=name)

    return stripe_product.id


def create_new_price(price, stripe_product_id):
    price = convert_float_to_price(price)
    stripe_price = stripe.Price.create(product=stripe_product_id, currency="usd", unit_amount=price)

    return {"stripe_product_id": stripe_product_id, "stripe_price_id": stripe_price.id}


def update_product(stripe_product_id, new_name: str | None = None, new_image_path: str | None = None):
    if new_name:
        stripe.Product.modify(id=stripe_product_id, name=new_name)

    if new_image_path:
        image = f"{DOMAIN}/{new_image_path}"
        stripe.Product.modify(id=stripe_product_id, images=[image])


def update_product_price(stripe_product_id, stripe_price_id):
    stripe.Product.modify(
        id=stripe_product_id,
        default_price=stripe_price_id
    )


def update_price(stripe_price_id):
    stripe.Price.modify(id=stripe_price_id, active=False)


def create_metadata(student_id: int, payment_items: list[int]):
    metadata = {"student_id": student_id}
    for i, item in enumerate(payment_items, start=1):
        key = f"item{i}"
        metadata[key] = item

    return metadata


def create_checkout(
        price_ids: list[str],
        metadata: dict,
        coupon: str = None
):
    line_items = [{"price": price_id, "quantity": 1} for price_id in price_ids]

    discounts = []

    if coupon:
        discounts.append({'coupon': coupon})
        checkout = stripe.checkout.Session.create(
            # success_url=f"{DOMAIN}?status=success_payment&items=5_6",
            success_url="http://localhost:3000/learning-platform-commerce",
            line_items=line_items,
            metadata=metadata,
            mode="payment",
            customer_email="dmitrjialekseev16@gmail.com",
            discounts=discounts,
        )

    else:
        checkout = stripe.checkout.Session.create(
            # success_url=f"{DOMAIN}?status=success_payment&items=5_6",
            success_url="http://localhost:3000/learning-platform-commerce",
            line_items=line_items,
            metadata=metadata,
            mode="payment",
            customer_email="dmitrjialekseev16@gmail.com",
            allow_promotion_codes=True
            # discounts=discounts,
        )

    return checkout.url


def webhook_event(body, stripe_signature):
    event = stripe.Webhook.construct_event(
        payload=body,
        sig_header=stripe_signature,
        secret=STRIPE_WEBHOOK,
    )
    return event


def create_payment_intent(amount, customer_id, metadata):
    amount = round(amount * 100)

    intent = stripe.PaymentIntent.create(
        amount=amount,
        customer=customer_id,
        currency="usd",
        metadata=metadata
    )

    return intent.client_secret


def create_coupon(percent):
    coupon = stripe.Coupon.create(percent_off=percent, duration="once")
    return coupon.id


def create_promotion_code(coupon_id):
    promotion_code = stripe.PromotionCode.create(coupon=coupon_id)
    return promotion_code


def get_customer():
    customer = stripe.Customer.list(limit=1)
    return customer.data[0].id


def create_ephemeral_key(customer):
    key = stripe.EphemeralKey.create(
        customer=customer,
        stripe_version="2024-09-30.acacia"
    )

    return key.secret
