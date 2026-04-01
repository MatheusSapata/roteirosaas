from app.services.finance import calculate_platform_fee


def test_calculate_platform_fee_thousand_reais() -> None:
    assert calculate_platform_fee(100_000) == 1_500


def test_calculate_platform_fee_decimal_rounding() -> None:
    assert calculate_platform_fee(123_750) == 1_856


def test_calculate_platform_fee_small_amount() -> None:
    assert calculate_platform_fee(999) == 15
