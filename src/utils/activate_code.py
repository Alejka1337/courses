from random import randint


def generate_activation_code():
    code = randint(1_000_000,  9_999_999)
    return str(code)


def generate_reset_code():
    code = randint(100_000, 999_999)
    return str(code)
