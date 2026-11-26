from src.manager import Manager
from src.models import Parameters
from src.models import Bill


def test_apartment_costs_nonexistent_apartment():
    manager = Manager(Parameters())
    assert manager.get_apartment_costs('apart-nonexistent', 2025, 1) is None
    assert manager.get_apartment_costs('', 2025, 1) is None


def test_apartment_costs_no_bills_in_month():
    manager = Manager(Parameters())
    assert manager.get_apartment_costs('apart-polanka', 2025, 2) == 0.0
    assert manager.get_apartment_costs('apart-polanka', 2024, 1) == 0.0  # month matches, year doesn't
    assert manager.get_apartment_costs('apart-polanka', 2025, 12) == 0.0  # year matches, month doesn't


def test_apartment_costs_with_bills_in_month():
    manager = Manager(Parameters())
    assert manager.get_apartment_costs('apart-polanka', 2025, 1) == 910.0

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2025-04-10',
        settlement_year=2025,
        settlement_month=3,
        amount_pln=450.0,
        type='rent'
    ))
    assert manager.get_apartment_costs('apart-polanka', 2025, 3) == 450.0
    assert manager.get_apartment_costs('apart-polanka', 2025, 1) == 910.0  # other months unaffected


def test_apartment_costs_ignores_other_apartments_bills():
    manager = Manager(Parameters())
    manager.bills.append(Bill(
        apartment='apart-other',
        date_due='2025-02-15',
        settlement_year=2025,
        settlement_month=1,
        amount_pln=999.0,
        type='rent'
    ))
    assert manager.get_apartment_costs('apart-polanka', 2025, 1) == 910.0
