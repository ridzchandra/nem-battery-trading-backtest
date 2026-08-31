from nem_trading.battery import Battery


def test_battery_never_exceeds_capacity():
    battery = Battery(capacity_mwh=10, max_power_mw=50, state_of_charge_mwh=9.9)
    battery.charge(price=20)
    assert battery.state_of_charge_mwh <= battery.capacity_mwh + 1e-9


def test_battery_never_goes_below_zero():
    battery = Battery(capacity_mwh=10, max_power_mw=50, state_of_charge_mwh=0.1)
    battery.discharge(price=200)
    assert battery.state_of_charge_mwh >= -1e-9


def test_negative_price_charge_creates_positive_cashflow():
    battery = Battery(state_of_charge_mwh=50)
    _, cashflow = battery.charge(price=-50)
    assert cashflow > 0
