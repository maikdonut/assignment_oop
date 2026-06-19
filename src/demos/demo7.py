from bank import Bank, Client
from accounts import BankAccount
from account_types import SavingsAccount, PremiumAccount, InvestmentAccount
from transactions import Transaction, TransactionQueue, TransactionProcessor, TransactionType
from reports import ReportBuilder


bank = Bank("PyBank")

clients_data = [
    ("Иванов И.И.",   "c001", 35, "pass001"),
    ("Петров П.П.",   "c002", 28, "pass002"),
    ("Сидоров С.С.",  "c003", 45, "pass003"),
    ("Козлова А.А.",  "c004", 31, "pass004"),
    ("Морозова Е.Е.", "c005", 50, "pass005"),
]

for name, cid, age, pwd in clients_data:
    bank.add_client(Client(name=name, client_id=cid, age=age, password=pwd))

acc1 = BankAccount(account_id=None, owner_info="Иванов И.И.")
acc2 = SavingsAccount(account_id=None, owner_info="Петров П.П.", monthly_rate=0.08)
acc3 = PremiumAccount(account_id=None, owner_info="Сидоров С.С.", overdraft_limit=10000, commission=50)
acc4 = SavingsAccount(account_id=None, owner_info="Козлова А.А.", monthly_rate=0.05, min_balance=1000)
acc5 = InvestmentAccount(account_id=None, owner_info="Морозова Е.Е.")

bank.open_account("c001", acc1)
bank.open_account("c002", acc2)
bank.open_account("c003", acc3)
bank.open_account("c004", acc4)
bank.open_account("c005", acc5)

# начальные депозиты
for acc_id, amount in [
    (acc1.account_id, 50000),
    (acc2.account_id, 30000),
    (acc3.account_id, 80000),
    (acc4.account_id, 15000),
    (acc5.account_id, 60000),
]:
    bank.deposit(acc_id, amount)

# транзакции
transactions = [
    Transaction(TransactionType.DEPOSIT,    5000,  "",              acc1.account_id),
    Transaction(TransactionType.DEPOSIT,    3000,  "",              acc2.account_id),
    Transaction(TransactionType.WITHDRAWAL, 2000,  acc1.account_id, ""),
    Transaction(TransactionType.WITHDRAWAL, 5000,  acc3.account_id, ""),
    Transaction(TransactionType.TRANSFER,   10000, acc1.account_id, acc2.account_id),
    Transaction(TransactionType.TRANSFER,   5000,  acc5.account_id, acc4.account_id),
    Transaction(TransactionType.TRANSFER,   3000,  acc2.account_id, acc1.account_id),
    Transaction(TransactionType.DEPOSIT,    2000,  "",              acc4.account_id),
    Transaction(TransactionType.WITHDRAWAL, 1000,  acc4.account_id, ""),
    Transaction(TransactionType.TRANSFER,   4000,  acc3.account_id, acc1.account_id),
    Transaction(TransactionType.WITHDRAWAL, 999999, acc1.account_id, ""),  # ошибочная
    Transaction(TransactionType.DEPOSIT,    200000, "",             acc3.account_id),  # подозрительная
]

queue = TransactionQueue()
for t in transactions:
    queue.add(t)

processor = TransactionProcessor(bank, max_retries=1)
processor.process_queue(queue)

# отчеты
builder = ReportBuilder(bank, transactions, output_dir="reports")

print(builder.client_report("c001"))
print()
print(builder.bank_report())
print()
print(builder.risk_report())

builder.export_to_json("report.json")
builder.export_to_csv("transactions.csv")
builder.save_charts()