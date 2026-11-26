import pytest

from src.manager import Manager
from src.models import Parameters
from src.models import Bill, ApartmentSettlement


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


def test_apartment_costs_with_optional_parameters():
    manager = Manager(Parameters())
    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2025-03-15',
        settlement_year=2025,
        settlement_month=2,
        amount_pln=1250.0,
        type='rent'
    ))

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2024-03-15',
        settlement_year=2024,
        settlement_month=2,
        amount_pln=1150.0,
        type='rent'
    ))

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2024-02-02',
        settlement_year=2024,
        settlement_month=1,
        amount_pln=222.0,
        type='electricity'
    ))

    costs = manager.get_apartment_costs('apartment-1', 2024, 1)
    assert costs is None

    costs = manager.get_apartment_costs('apart-polanka', 2024, 3)
    assert costs == 0.0

    costs = manager.get_apartment_costs('apart-polanka', 2024, 1)
    assert costs == 222.0

    costs = manager.get_apartment_costs('apart-polanka', 2025, 1)
    assert costs == 910.0

    costs = manager.get_apartment_costs('apart-polanka', 2024)
    assert costs == 1372.0

    costs = manager.get_apartment_costs('apart-polanka')
    assert costs == 3532.0


def test_apartment_costs_invalid_month():
    manager = Manager(Parameters())
    with pytest.raises(ValueError):
        manager.get_apartment_costs('apart-polanka', 2025, 13)
    with pytest.raises(ValueError):
        manager.get_apartment_costs('apart-polanka', 2025, 0)
    with pytest.raises(ValueError):
        manager.get_apartment_costs('apart-polanka', 2025, -1)


def test_apartment_costs_month_without_year():
    manager = Manager(Parameters())
    with pytest.raises(ValueError):
        manager.get_apartment_costs('apart-polanka', None, 1)


def test_apartment_costs_boundary_months_are_valid():
    manager = Manager(Parameters())
    assert manager.get_apartment_costs('apart-polanka', 2025, 1) == 910.0
    assert manager.get_apartment_costs('apart-polanka', 2025, 12) == 0.0


def test_create_apartment_settlement():
    manager = Manager(Parameters())
    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2025-03-15',
        settlement_year=2025,
        settlement_month=2,
        amount_pln=1250.0,
        type='rent'
    ))

    # apartment with bills in the given month
    settlement = manager.create_apartment_settlement('apart-polanka', 2025, 1)
    assert isinstance(settlement, ApartmentSettlement)
    assert settlement.apartment == 'apart-polanka'
    assert settlement.year == 2025
    assert settlement.month == 1
    assert settlement.total_bills_pln == 910.0
    assert settlement.total_rent_pln == 0.0  # transfers not included yet
    assert settlement.total_due_pln == -910.0  # balance = transfers - bills

    settlement = manager.create_apartment_settlement('apart-polanka', 2025, 2)
    assert settlement.month == 2
    assert settlement.total_bills_pln == 1250.0
    assert settlement.total_due_pln == -1250.0

    # apartment without bills in the given month
    settlement = manager.create_apartment_settlement('apart-polanka', 2024, 6)
    assert isinstance(settlement, ApartmentSettlement)
    assert settlement.apartment == 'apart-polanka'
    assert settlement.year == 2024
    assert settlement.month == 6
    assert settlement.total_bills_pln == 0.0
    assert settlement.total_due_pln == 0.0

    # nonexistent apartment
    assert manager.create_apartment_settlement('apart-nonexistent', 2025, 1) is None
