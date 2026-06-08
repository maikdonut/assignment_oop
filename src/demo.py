from accounts import AccountStatus, BankAccount, InsufficientFundsError, AccountFrozenError


# активный счёт
acc1 = BankAccount(account_id=None, owner_info="Иванов И.И.", currency="RUB")

# операции с активным счётом
acc1.deposit(500) 
acc1.withdraw(200)
try:
    acc1.withdraw(400)
except InsufficientFundsError as e:
    print(e)
print(f"Активный счет:\n{acc1}\n")

# замороженный счёт
acc2 = BankAccount(account_id=None, owner_info="Иванова А.А.", currency="EUR")
acc2.status = AccountStatus.FROZEN
print(f"Замороженный счет:\n{acc2}\n")

# операции с замороженным счётом
try:
    acc2.deposit(100)
except AccountFrozenError as e:
    print(e)

try:
    acc2.withdraw(100)
except AccountFrozenError as e:
    print(e)

