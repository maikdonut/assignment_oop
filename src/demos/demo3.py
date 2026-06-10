from bank import Bank, Client
from accounts import BankAccount, AccountStatus, InvalidOperationError
from account_types import SavingAccount

# создание банка
bank = Bank("MyBank")

# создание клиентов
client1 = Client(name="Иванов И.И.", client_id="c001", age=30, password="pass123", phone="+7900000001")
client2 = Client(name="Петров П.П.", client_id="c002", age=25, password="pass456", phone="+7900000002")

bank.add_client(client1)
bank.add_client(client2)

# открытие счетов
acc1 = BankAccount(account_id=None, owner_info="Иванов И.И.")
acc2 = SavingAccount(account_id=None, owner_info="Петров П.П.", monthly_rate=0.1)

bank.open_account("c001", acc1)
bank.open_account("c002", acc2)

# операции
bank.deposit(acc1.account_id, 5000)
bank.deposit(acc2.account_id, 3000)
bank.withdraw(acc1.account_id, 1000)

# аутентификация
print("Аутентификация:")
print(bank.authenticate_client("c001", "pass123"))   # True
print(bank.authenticate_client("c001", "wrongpass")) # False
print(bank.authenticate_client("c001", "wrongpass")) # False
print(bank.authenticate_client("c001", "wrongpass")) # False — блокировка

try:
    bank.authenticate_client("c001", "pass123")
except InvalidOperationError as e:
    print(e)

# заморозка
bank.freeze_account("c002", acc2.account_id)
try:
    bank.deposit(acc2.account_id, 100)
except Exception as e:
    print(e)
bank.unfreeze_account("c002", acc2.account_id)

# закрытие счёта
bank.close_account("c001", acc1.account_id)
try:
    bank.deposit(acc1.account_id, 100)
except Exception as e:
    print(e)

# общий баланс и рейтинг
print(f"\nОбщий баланс банка: {bank.get_total_balance()}")
print(f"\nРейтинг клиентов:")
for client in bank.get_clients_ranking():
    print(f"  {client.name}: {sum(bank.accounts[acc_id]._balance for acc_id in client.account_ids if acc_id in bank.accounts)}")

# подозрительная операция
bank.deposit(acc2.account_id, 200000)
