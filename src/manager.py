import calendar
from datetime import date

from src.models import Apartment, ApartmentSettlement, Bill, Parameters, Tenant, TenantSettlement, Transfer


class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters 

        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []
       
        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)

    def check_tenants_apartment_keys(self) -> bool:
        for tenant in self.tenants.values():
            if tenant.apartment not in self.apartments:
                return False
        return True

    def get_apartment_costs(self, apartment_key: str, year: int | None = None, month: int | None = None) -> float | None:
        if month is not None:
            if year is None:
                raise ValueError("Month given without year")
            if not 1 <= month <= 12:
                raise ValueError(f"Invalid month: {month}")
        if apartment_key not in self.apartments:
            return None
        total = 0.0
        for bill in self.bills:
            if bill.apartment != apartment_key:
                continue
            if year is not None and bill.settlement_year != year:
                continue
            if month is not None and bill.settlement_month != month:
                continue
            total += bill.amount_pln
        return total

    def create_apartment_settlement(self, apartment_key: str, year: int, month: int) -> ApartmentSettlement | None:
        total_bills = self.get_apartment_costs(apartment_key, year, month)
        if total_bills is None:
            return None
        total_transfers = 0.0  # transfers will be included in a later step
        return ApartmentSettlement(
            apartment=apartment_key,
            year=year,
            month=month,
            total_rent_pln=total_transfers,
            total_bills_pln=total_bills,
            total_due_pln=total_transfers - total_bills,
        )

    def get_current_tenants(self, apartment_key: str, year: int, month: int) -> dict[str, Tenant]:
        month_start = date(year, month, 1)
        month_end = date(year, month, calendar.monthrange(year, month)[1])
        return {
            key: tenant for key, tenant in self.tenants.items()
            if tenant.apartment == apartment_key
            and date.fromisoformat(tenant.date_agreement_from) <= month_end
            and date.fromisoformat(tenant.date_agreement_to) >= month_start
        }

    def create_tenant_settlements(self, apartment_settlement: ApartmentSettlement) -> list[TenantSettlement]:
        tenants = self.get_current_tenants(
            apartment_settlement.apartment, apartment_settlement.year, apartment_settlement.month
        )
        if not tenants:
            return []
        bills_share = apartment_settlement.total_bills_pln / len(tenants)
        rent_share = 0.0  # transfers will be included in a later step
        return [
            TenantSettlement(
                tenant=tenant_key,
                apartment_settlement=apartment_settlement.apartment,
                year=apartment_settlement.year,
                month=apartment_settlement.month,
                rent_pln=rent_share,
                bills_pln=bills_share,
                total_due_pln=rent_share - bills_share,
                balance_pln=rent_share - bills_share,
            )
            for tenant_key in tenants
        ]
