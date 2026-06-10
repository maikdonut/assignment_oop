import uuid
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from accounts import InvalidOperationError, BankAccount, AccountStatus


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

    def cancel(self, transaction_id: str) -> None:
        for t in self._queue:
            if t.transaction_id == transaction_id:
                t.status = TransactionStatus.CANCELLED
                self._queue.remove(t)
                return
        raise InvalidOperationError("Транзакция не найдена")

    def get_next(self) -> Transaction:
        if not self._queue:
            return None
        return self._queue.pop(0)


class TransactionProcessor:
    def __init__(self, bank: "Bank", max_retries=3):
        self.bank = bank
        self.max_retries = max_retries 

    def process(self, transaction: Transaction, attempt=1):
        try:
            self._apply_commission(transaction)
            if transaction.transaction_type == TransactionType.DEPOSIT:
                self.bank.deposit(transaction.receiver_id, transaction.amount)
            elif transaction.transaction_type == TransactionType.WITHDRAWAL:
                self.bank.withdraw(transaction.sender_id, transaction.amount)
            elif transaction.transaction_type == TransactionType.TRANSFER:
                self.bank.withdraw(transaction.sender_id, transaction.amount)
                self.bank.deposit(transaction.receiver_id, transaction.amount)
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

    def _apply_commission(self, transaction: Transaction) -> None:
        transaction.amount += transaction.commission

    def _convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        if from_currency == to_currency:
            return amount
        rate = EXCHANGE_RATES.get((from_currency, to_currency))
        if rate is None:
            raise InvalidOperationError(f"Курс {from_currency} -> {to_currency} не найден")
        return amount * rate

