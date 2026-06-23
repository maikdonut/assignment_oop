from accounts import BankAccount, InsufficientFundsError, InvalidOperationError


class SavingsAccount(BankAccount):
    def __init__(self, account_id, owner_info, currency="RUB", min_balance=0, monthly_rate=0.05):
        if min_balance < 0:
            raise InvalidOperationError("Минимальный остаток не может быть отрицательным")
        if not (0 < monthly_rate < 1):
            raise InvalidOperationError("Ставка должна быть между 0 и 1")
        super().__init__(account_id, owner_info, currency)
        self.min_balance = min_balance
        self.monthly_rate = monthly_rate

    def apply_monthly_interest(self):
        self._check_status()
        self._balance += self._balance * self.monthly_rate

    def withdraw(self, amount: float) -> None:
        self._check_status()
        if self._balance - amount < self.min_balance:
            raise InsufficientFundsError("Нельзя снять ниже минимального остатка")
        super().withdraw(amount)

    def get_account_info(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return "\n".join([
            super().__str__(),
            f"Минимальный остаток: {self.min_balance} {self.currency}",
            f"Месячная ставка: {self.monthly_rate * 100}%"
        ])


# обратная совместимость
SavingAccount = SavingsAccount


class PremiumAccount(BankAccount):
    def __init__(self, account_id, owner_info, currency="RUB", overdraft_limit=0, transaction_limit=10000, commission=0):
        if transaction_limit < 0:
            raise InvalidOperationError("Лимит транзакций не может быть отрицательным")
        if commission < 0:
            raise InvalidOperationError("Комиссия не может быть отрицательной")
        super().__init__(account_id, owner_info, currency)
        self.overdraft_limit = overdraft_limit
        self.transaction_limit = transaction_limit
        self.commission = commission

    def withdraw(self, amount: float) -> None:
        self._check_status()
        if amount <= 0:
            raise InvalidOperationError("Сумма должна быть положительной")
        if amount > self.transaction_limit:
            raise InvalidOperationError(f"Превышен лимит транзакции: {self.transaction_limit}")
        total = amount + self.commission
        if total > self._balance + self.overdraft_limit:
            raise InsufficientFundsError("Недостаточно средств даже с овердрафтом")
        self._balance -= total

    def get_account_info(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return "\n".join([
            super().__str__(),
            f"Овердрафт: {'включен' if self.overdraft_limit else 'выключен'}",
            f"Лимит по транзакции: {self.transaction_limit}",
            f"Комиссия: {self.commission}"
        ])


class InvestmentAccount(BankAccount):
    def __init__(self, account_id, owner_info, currency="RUB", portfolio=None):
        if portfolio is None:
            portfolio = {"stocks": 0, "bonds": 0, "etf": 0}
        super().__init__(account_id, owner_info, currency)
        for asset, v in portfolio.items():
            self._check_asset(asset, v)
        self.portfolio = portfolio

    @staticmethod
    def _check_asset(asset_type, amount):
        if asset_type not in ["stocks", "bonds", "etf"]:
            raise InvalidOperationError("Недопустимый актив")
        if amount < 0:
            raise InvalidOperationError("Сумма не может быть отрицательной")

    def add_asset(self, asset_type, amount):
        self._check_asset(asset_type, amount)
        self.portfolio[asset_type] = self.portfolio.get(asset_type, 0) + amount

    def project_yearly_growth(self, rate: float):
        total = sum(self.portfolio.values())
        return total * (1 + rate)

    def withdraw(self, amount: float) -> None:
        super().withdraw(amount)

    def get_account_info(self) -> str:
        return str(self)

    def __str__(self) -> str:
        portfolio_items = ", ".join(f"{k}: {v}" for k, v in self.portfolio.items())
        return "\n".join([
            super().__str__(),
            f"Портфель: {portfolio_items}"
        ])
