from decimal import Decimal


def convert_float_to_price(number: float) -> int:
    price = Decimal(str(number))
    return int(price * 100)
