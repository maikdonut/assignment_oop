from datetime import datetime
from dataclasses import dataclass, field
from accounts import InvalidOperationError, BankAccount, AccountStatus
from audit import AuditLog, RiskAnalyzer, RiskLevel, AuditLevel
from transactions import Transaction, TransactionType, TransactionStatus


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
        self.audit_log = AuditLog()
        self.risk_analyzer = RiskAnalyzer(self.audit_log, frequent_ops_limit=20)
        self.transaction_history = []
        self._balance_snapshots = []

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

    def _ensure_account_owned(self, client_id: str, account_id: str) -> None:
        if account_id not in self.clients[client_id].account_ids:
            raise InvalidOperationError("Счёт не принадлежит клиенту")

    def close_account(self, client_id: str, account_id: str) -> None:
        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден")
        if account_id not in self.accounts:
            raise InvalidOperationError("Аккаунт не существует")
        self._ensure_account_owned(client_id, account_id)
        self.accounts[account_id].status = AccountStatus.CLOSED

    def freeze_account(self, client_id: str, account_id: str) -> None:
        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден")
        if account_id not in self.accounts:
            raise InvalidOperationError("Аккаунт не существует")
        self._ensure_account_owned(client_id, account_id)
        if self.accounts[account_id].status == AccountStatus.CLOSED:
            raise InvalidOperationError("Счет закрыт")
        self.accounts[account_id].status = AccountStatus.FROZEN

    def unfreeze_account(self, client_id: str, account_id: str) -> None:
        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден")
        if account_id not in self.accounts:
            raise InvalidOperationError("Аккаунт не существует")
        self._ensure_account_owned(client_id, account_id)
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
        self._failed_attempts[client_id] += 1
        if self._failed_attempts[client_id] >= 3:
            self.clients[client_id].status = False
            self.audit_log.log_message(
                AuditLevel.CRITICAL,
                "Клиент заблокирован после неверных попыток входа",
                {"client_id": client_id},
            )
        return False

    def search_accounts(self, client_id: str) -> list:
        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден")
        return [self.accounts[acc_id] for acc_id in self.clients[client_id].account_ids]

    def get_client_id_for_account(self, account_id: str) -> str:
        if not account_id:
            return ""
        for client_id, client in self.clients.items():
            if account_id in client.account_ids:
                return client_id
        return ""

    def get_client_transaction_history(self, client_id: str) -> list:
        if client_id not in self.clients:
            raise InvalidOperationError("Клиент не найден")
        account_ids = set(self.clients[client_id].account_ids)
        return [
            t for t in self.transaction_history
            if t.sender_id in account_ids or t.receiver_id in account_ids
        ]

    def get_balance_snapshots(self) -> list:
        return list(self._balance_snapshots)

    def get_total_balance(self):
        return sum(account._balance for account in self.accounts.values())

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

    def deposit(self, account_id: str, amount: float, transaction_id: str = "",
                transaction: Transaction = None, skip_risk: bool = False,
                skip_record: bool = False) -> None:
        self._check_operating_hours()
        if account_id not in self.accounts:
            raise InvalidOperationError("Счёт не найден")
        self.accounts[account_id]._check_status()

        t = transaction or Transaction(TransactionType.DEPOSIT, amount, "", account_id)
        if transaction_id:
            t.transaction_id = transaction_id

        if not skip_risk:
            self._evaluate_risk(t)
        self.accounts[account_id].deposit(amount)
        if not skip_record:
            self._finalize_operation(t)

    def withdraw(self, account_id: str, amount: float, transaction: Transaction = None,
                 skip_risk: bool = False) -> None:
        self._check_operating_hours()
        if account_id not in self.accounts:
            raise InvalidOperationError("Счёт не найден")
        self.accounts[account_id]._check_status()

        t = transaction or Transaction(TransactionType.WITHDRAWAL, amount, account_id, "")
        if not skip_risk:
            self._evaluate_risk(t)
        self.accounts[account_id].withdraw(amount)
        if skip_risk:
            return
        self._finalize_operation(t)

    def _evaluate_risk(self, transaction: Transaction) -> None:
        risk = self.risk_analyzer.analyze(transaction, self)
        client_id = self.get_client_id_for_account(
            transaction.sender_id or transaction.receiver_id
        )
        if risk.value >= RiskLevel.MEDIUM.value:
            self.audit_log.log_message(
                AuditLevel.WARNING,
                "Подозрительная операция",
                {
                    "client_id": client_id,
                    "transaction_id": transaction.transaction_id,
                    "risk_level": risk.name,
                    "amount": transaction.amount,
                },
            )
        if risk == RiskLevel.HIGH:
            raise InvalidOperationError("Операция заблокирована: высокий риск")

    def _finalize_operation(self, transaction: Transaction) -> None:
        transaction.status = TransactionStatus.COMPLETED
        if transaction not in self.transaction_history:
            self.transaction_history.append(transaction)
        self._balance_snapshots.append((datetime.now(), self.get_total_balance()))

    def _check_operating_hours(self):
        current_hour = datetime.now().hour
        if 0 <= current_hour < 5:
            raise InvalidOperationError("Операции запрещены с 00:00 до 05:00")
