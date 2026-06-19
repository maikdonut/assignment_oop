import _path  # noqa: F401
from bank import Bank, Client
from accounts import BankAccount, InvalidOperationError
from account_types import PremiumAccount
from datetime import datetime, timedelta
from transactions import Transaction, TransactionQueue, TransactionProcessor, TransactionType

# банк и клиенты
bank = Bank("MyBank")

client1 = Client(name="Иванов И.И.", client_id="c001", age=30, password="pass123")
client2 = Client(name="Петров П.П.", client_id="c002", age=25, password="pass456")
client3 = Client(name="Сидоров С.С.", client_id="c003", age=35, password="pass789")

bank.add_client(client1)
bank.add_client(client2)
bank.add_client(client3)

# счета
acc1 = BankAccount(account_id=None, owner_info="Иванов И.И.")
acc2 = BankAccount(account_id=None, owner_info="Петров П.П.", currency="USD")
acc3 = PremiumAccount(account_id=None, owner_info="Сидоров С.С.", overdraft_limit=5000, commission=50)

bank.open_account("c001", acc1)
bank.open_account("c002", acc2)
bank.open_account("c003", acc3)

# начальные балансы
bank.deposit(acc1.account_id, 10000)
bank.deposit(acc2.account_id, 5000)
bank.deposit(acc3.account_id, 8000)

# создаём транзакции
transactions = [
    Transaction(TransactionType.DEPOSIT,    1000,  "",              acc1.account_id),
    Transaction(TransactionType.DEPOSIT,    2000,  "",              acc2.account_id),
    Transaction(TransactionType.WITHDRAWAL, 500,   acc1.account_id, ""),
    Transaction(TransactionType.WITHDRAWAL, 300,   acc2.account_id, ""),
    Transaction(TransactionType.TRANSFER,   1000,  acc1.account_id, acc2.account_id),
    Transaction(TransactionType.TRANSFER,   2000,  acc2.account_id, acc3.account_id),
    Transaction(TransactionType.DEPOSIT,    500,   "",              acc3.account_id),
    Transaction(TransactionType.WITHDRAWAL, 99999, acc1.account_id, ""),   # упадёт
    Transaction(TransactionType.TRANSFER,   100,   acc3.account_id, acc1.account_id, commission=10),
    Transaction(
        TransactionType.TRANSFER, 500, acc1.account_id, "external-999",
        is_external=True,
    ),
]

# очередь
queue = TransactionQueue()
for t in transactions[:-2]:
    queue.add(t)

# отложенная транзакция (выполнится сразу — время в прошлом)
scheduled = Transaction(TransactionType.DEPOSIT, 3000, "", acc3.account_id)
queue.schedule(scheduled, datetime.now() - timedelta(seconds=1))

queue.add(transactions[-2])
queue.add(transactions[-1], priority=True)

print(f"Транзакций в очереди: {queue.pending_count}")

# обработка
processor = TransactionProcessor(bank, max_retries=2)
processor.process_queue(queue)

all_transactions = transactions + [scheduled]

# результаты
print("\nСтатусы транзакций:")
for t in all_transactions:
    print(f"  {t.transaction_id} | {t.transaction_type.value} | {t.amount} | {t.status.value} | {t.failure_reason or 'OK'}")

print(f"\nБалансы:")
print(f"  Иванов: {acc1.balance} {acc1.currency}")
print(f"  Петров: {acc2.balance} {acc2.currency}")
print(f"  Сидоров: {acc3.balance} {acc3.currency}")
print(f"\nОбщий баланс банка: {bank.get_total_balance()}")
