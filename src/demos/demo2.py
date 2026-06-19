import _path  # noqa: F401
from accounts import AccountStatus, BankAccount, InsufficientFundsError, AccountFrozenError, InvalidOperationError
from account_types import SavingsAccount, PremiumAccount, InvestmentAccount


# SavingAccount
acc1 = SavingsAccount(account_id=None, owner_info="Иванов И.И.", currency="RUB", monthly_rate=0.12)
acc1.deposit(1000) 
prev_balance = acc1.balance
acc1.apply_monthly_interest() # добавляем %
print(f"Прошлый месяц: {prev_balance}, след. месяц: {acc1.balance}")
acc1.withdraw(200) # снимаем 
print(f"\nSavingAccount:\n{acc1}\n")

# вызов ошибок
print("Ошибки 1")
try:
    acc1.withdraw(4000)
except InsufficientFundsError as e:
    print(e)

try:
    bad_acc = SavingsAccount(account_id=None, owner_info="Иванов И.И.", currency="RUB", min_balance=-50, monthly_rate=0.12)
except InvalidOperationError as e:
    print(e)


# PremiumAccount
acc2 = PremiumAccount(account_id=None, owner_info="Петров П.П.", currency="USD", overdraft_limit=500, transaction_limit=10000, commission=10)
acc2.deposit(1000)
acc2.withdraw(200)
print(f"\nPremiumAccount:\n{acc2}\n")

# вызов ошибок
print("Ошибки 2")
try:
    acc2.withdraw(20000)  # превышен лимит транзакции
except InvalidOperationError as e:
    print(e)

try:
    acc2.withdraw(2000)  # превышен баланс + овердрафт
except InsufficientFundsError as e:
    print(e)


# InvestmentAccount
acc3 = InvestmentAccount(account_id=None, owner_info="Сидоров С.С.", currency="RUB")
acc3.deposit(5000)
acc3.add_asset("stocks", 2000)
acc3.add_asset("bonds", 1000)
acc3.add_asset("etf", 500)
growth = acc3.project_yearly_growth(0.15)
print(f"Прогноз роста портфеля за год (15%): {growth}")
print(f"\nInvestmentAccount:\n{acc3}\n")

# вызов ошибок
print("Ошибки 3")
try:
    acc3.add_asset("crypto", 1000)  # недопустимый актив
except InvalidOperationError as e:
    print(e)

try:
    bad_acc = InvestmentAccount(account_id=None, owner_info="Сидоров С.С.", portfolio={"stocks": -100})
except InvalidOperationError as e:
    print(e)