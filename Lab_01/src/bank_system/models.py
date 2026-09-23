from dataclasses import dataclass


@dataclass
class Account:
    account_number: str
    client_name: str
    balance: float = 0.0

    @property
    def masked_number(self) -> str:
        """Номер рахунку з прихованими першими символами (для друку)."""
        return f"***{self.account_number[-4:]}"