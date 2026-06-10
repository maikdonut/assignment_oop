from dataclasses import dataclass, field
from accounts import InvalidOperationError, BankAccount, AccountStatus
from datetime import datetime


@dataclass
class Client:
    name: str
    client_id: str
    age: int
    status: bool = True
    password: str = ""
    phone: str = ""
    account_ids: list = field(default_factory=list)

    def __post_init__(self):
        if self.age < 18:
            raise InvalidOperationError("Клиент должен быть старше 18 лет")

class Bank:
    def __init__(self, name):
        self.name = name
        self.clients = {}
        self.accounts = {}
        self._failed_attempts = {}

    def add_client(self, client: Client) -> None:
        if client.client_id in self.clients:
            raise InvalidOperationError("Клиент уже существует")
        self.clients[client.client_id] = client

    def open_account(self, client_id: str, account: BankAccount) -> None:
        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден")
        if account.account_id in self.accounts:
            raise InvalidOperationError("Аккаунт уже существует")
        self.accounts[account.account_id] = account
        self.clients[client_id].account_ids.append(account.account_id)

    def close_account(self, client_id: str, account_id: str) -> None:
        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден")
        if account_id not in self.accounts:
            raise InvalidOperationError("Аккаунт не существует")
        self.accounts[account_id].status = AccountStatus.CLOSED

    def freeze_account(self, client_id: str, account_id: str) -> None:
        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден")
        if account_id not in self.accounts:
            raise InvalidOperationError("Аккаунт не существует")
        if self.accounts[account_id].status == AccountStatus.CLOSED:
            raise InvalidOperationError("Счет закрыт")
        self.accounts[account_id].status = AccountStatus.FROZEN

    def unfreeze_account(self, client_id: str, account_id: str) -> None:
        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден")
        if account_id not in self.accounts:
            raise InvalidOperationError("Аккаунт не существует")
        if self.accounts[account_id].status == AccountStatus.CLOSED:
            raise InvalidOperationError("Счет закрыт")
        self.accounts[account_id].status = AccountStatus.ACTIVE

    def authenticate_client(self, client_id: str, password: str):
        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден")
        if not self.clients[client_id].status:
            raise InvalidOperationError("Клиент заблокирован")
        self._failed_attempts.setdefault(client_id, 0)
        if password == self.clients[client_id].password:
            self._failed_attempts[client_id] = 0
            return True
        else:
            self._failed_attempts[client_id] += 1
            if self._failed_attempts[client_id] >= 3:
                self.clients[client_id].status = False
            return False

    def search_accounts(self, client_id: str) -> list:
        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден")
        return [self.accounts[acc_id] for acc_id in self.clients[client_id].account_ids]

    def get_total_balance(self):
        total_balance = 0
        for account in self.accounts.values():
            total_balance += account._balance
        return total_balance

    def get_clients_ranking(self, top_k=None) -> list:
        ranking = sorted(
            self.clients.values(),
            key=lambda client: sum(
                self.accounts[acc_id]._balance 
                for acc_id in client.account_ids 
                if acc_id in self.accounts
            ),
            reverse=True
        )
        return ranking[:top_k]

    def deposit(self, account_id: str, amount: float) -> None:
        self._check_operating_hours()
        self._check_suspicious(account_id, amount)
        if account_id not in self.accounts:
            raise InvalidOperationError("Счёт не найден")
        self.accounts[account_id].deposit(amount)

    def withdraw(self, account_id: str, amount: float) -> None:
        self._check_operating_hours()
        self._check_suspicious(account_id, amount)
        if account_id not in self.accounts:
            raise InvalidOperationError("Счёт не найден")
        self.accounts[account_id].withdraw(amount)

    def _check_operating_hours(self):
        current_hour = datetime.now().hour
        if 0 <= current_hour < 5:
            raise InvalidOperationError("Операции запрещены с 00:00 до 05:00")
    
    def _check_suspicious(self, account_id: str, amount: float) -> None:
        if amount > 100000:
            print(f"Подозрительная операция: счёт {account_id}, сумма {amount}")

