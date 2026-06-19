import uuid
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from accounts import (
    InvalidOperationError,
    AccountStatus,
    AccountFrozenError,
    InsufficientFundsError,
)


EXCHANGE_RATES = {
    ("RUB", "USD"): 0.011,
    ("RUB", "EUR"): 0.010,
    ("USD", "RUB"): 90.0,
    ("EUR", "RUB"): 100.0,
    ("USD", "EUR"): 0.92,
    ("EUR", "USD"): 1.08,
    ("RUB", "KZT"): 5.0,
    ("KZT", "RUB"): 0.2,
}

EXTERNAL_COMMISSION_RATE = 0.02


class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"


class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Transaction:
    transaction_type: TransactionType
    amount: float
    sender_id: str
    receiver_id: str
    status: TransactionStatus = TransactionStatus.PENDING
    currency: str = "RUB"
    commission: float = 0.0
    failure_reason: str = ""
    is_external: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


class TransactionQueue:
    def __init__(self):
        self._queue = []
        self._scheduled = []

    def add(self, transaction: Transaction, priority=False) -> None:
        if priority:
            self._queue.insert(0, transaction)
        else:
            self._queue.append(transaction)

    def schedule(self, transaction: Transaction, execute_at: datetime) -> None:
        self._scheduled.append((execute_at, transaction))
        self._scheduled.sort(key=lambda item: item[0])

    def cancel(self, transaction_id: str) -> None:
        for t in self._queue:
            if t.transaction_id == transaction_id:
                t.status = TransactionStatus.CANCELLED
                self._queue.remove(t)
                return
        for i, (_, t) in enumerate(self._scheduled):
            if t.transaction_id == transaction_id:
                t.status = TransactionStatus.CANCELLED
                self._scheduled.pop(i)
                return
        raise InvalidOperationError("Транзакция не найдена")

    def get_next(self) -> Transaction:
        now = datetime.now()
        ready = [(i, tx) for i, (at, tx) in enumerate(self._scheduled) if at <= now]
        if ready:
            index, transaction = ready[0]
            self._scheduled.pop(index)
            return transaction
        if not self._queue:
            return None
        return self._queue.pop(0)

    @property
    def pending_count(self) -> int:
        return len(self._queue) + len(self._scheduled)


class TransactionProcessor:
    def __init__(self, bank: "Bank", max_retries=3):
        self.bank = bank
        self.max_retries = max_retries

    def process(self, transaction: Transaction, attempt=1):
        try:
            self._validate_transaction(transaction)
            if attempt == 1:
                self._apply_commission(transaction)

            if transaction.transaction_type == TransactionType.DEPOSIT:
                self.bank.deposit(
                    transaction.receiver_id,
                    transaction.amount,
                    transaction.transaction_id,
                    transaction=transaction,
                )
            elif transaction.transaction_type == TransactionType.WITHDRAWAL:
                self.bank.withdraw(
                    transaction.sender_id,
                    transaction.amount,
                    transaction=transaction,
                )
            elif transaction.transaction_type == TransactionType.TRANSFER:
                self._process_transfer(transaction)
            else:
                transaction.status = TransactionStatus.FAILED
                return False

            transaction.status = TransactionStatus.COMPLETED
            return True

        except Exception as e:
            if attempt < self.max_retries:
                return self.process(transaction, attempt + 1)
            transaction.status = TransactionStatus.FAILED
            transaction.failure_reason = str(e)
            return False

    def process_queue(self, queue: TransactionQueue) -> None:
        while True:
            transaction = queue.get_next()
            if transaction is None:
                break
            self.process(transaction)

    def _validate_transaction(self, transaction: Transaction) -> None:
        from account_types import PremiumAccount

        if transaction.amount <= 0:
            raise InvalidOperationError("Сумма должна быть положительной")

        account_ids = []
        if transaction.sender_id:
            account_ids.append(transaction.sender_id)
        if transaction.receiver_id:
            account_ids.append(transaction.receiver_id)

        for account_id in account_ids:
            if account_id not in self.bank.accounts:
                if transaction.is_external and account_id == transaction.receiver_id:
                    continue
                raise InvalidOperationError(f"Счёт {account_id} не найден")
            account = self.bank.accounts[account_id]
            if account.status == AccountStatus.FROZEN:
                raise AccountFrozenError(f"Счёт {account_id} заморожен")
            if account.status == AccountStatus.CLOSED:
                raise InvalidOperationError(f"Счёт {account_id} закрыт")

        if transaction.transaction_type in (TransactionType.WITHDRAWAL, TransactionType.TRANSFER):
            sender = self.bank.accounts.get(transaction.sender_id)
            if sender and not isinstance(sender, PremiumAccount):
                total = transaction.amount + transaction.commission
                if total > sender.balance:
                    raise InsufficientFundsError("Недостаточно средств")

    def _process_transfer(self, transaction: Transaction) -> None:
        self.bank._evaluate_risk(transaction)

        sender = self.bank.accounts[transaction.sender_id]
        withdraw_amount = transaction.amount

        self.bank.withdraw(
            transaction.sender_id, withdraw_amount, transaction=transaction, skip_risk=True
        )

        if transaction.receiver_id in self.bank.accounts:
            receiver = self.bank.accounts[transaction.receiver_id]
            deposit_amount = self._convert_currency(
                withdraw_amount, sender.currency, receiver.currency
            )
            self.bank.deposit(
                transaction.receiver_id,
                deposit_amount,
                transaction.transaction_id,
                transaction=transaction,
                skip_risk=True,
                skip_record=True,
            )

        self.bank._finalize_operation(transaction)

    def _apply_commission(self, transaction: Transaction) -> None:
        if transaction.commission > 0:
            transaction.amount += transaction.commission
        elif transaction.is_external:
            fee = round(transaction.amount * EXTERNAL_COMMISSION_RATE, 2)
            transaction.commission = fee
            transaction.amount += fee

    def _convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        if from_currency == to_currency:
            return amount
        rate = EXCHANGE_RATES.get((from_currency, to_currency))
        if rate is None:
            raise InvalidOperationError(f"Курс {from_currency} -> {to_currency} не найден")
        return round(amount * rate, 2)
