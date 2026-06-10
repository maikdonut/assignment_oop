from bank import Bank, Client
from accounts import BankAccount, InvalidOperationError
from audit import AuditReport, AuditLevel

# банк и клиенты
bank = Bank("MyBank")

client1 = Client(name="Иванов И.И.", client_id="c001", age=30, password="pass123")
client2 = Client(name="Петров П.П.", client_id="c002", age=25, password="pass456")

bank.add_client(client1)
bank.add_client(client2)

# счета
acc1 = BankAccount(account_id=None, owner_info="Иванов И.И.")
acc2 = BankAccount(account_id=None, owner_info="Петров П.П.")

bank.open_account("c001", acc1)
bank.open_account("c002", acc2)

# обычные операции
print("=== Обычные операции ===")
bank.deposit(acc1.account_id, 5000)
bank.deposit(acc2.account_id, 3000)
bank.withdraw(acc1.account_id, 1000)
print(f"Баланс Иванов: {acc1.balance}")
print(f"Баланс Петров: {acc2.balance}")

# подозрительная операция — крупная сумма
print("\n=== Подозрительные операции ===")
try:
    bank.deposit(acc1.account_id, 200000)
except InvalidOperationError as e:
    print(f"Заблокировано: {e}")

# много операций подряд
print("\n=== Частые операции ===")
for i in range(12):
    try:
        bank.deposit(acc2.account_id, 100)
    except InvalidOperationError as e:
        print(f"Заблокировано на операции {i+1}: {e}")
        break

# тестовые логи
bank.audit_log.log_message(AuditLevel.WARNING, "Тестовая подозрительная операция", {"client_id": "c001", "amount": 99999})
bank.audit_log.log_message(AuditLevel.CRITICAL, "Тестовая критическая операция", {"client_id": "c002", "amount": 500000})

# отчёт аудита
report = AuditReport(bank.audit_log)

print("\n=== Подозрительные записи ===")
for entry in report.get_suspicious_operations():
    print(f"  [{entry.level.value}] {entry.timestamp.strftime('%H:%M:%S')} — {entry.message} | {entry.details}")

print("\n=== Статистика ошибок ===")
for level, count in report.get_error_stats().items():
    print(f"  {level.value}: {count}")

# сохранить лог
bank.audit_log.save_to_file("audit.json")
print("\nЛог сохранён в logs/audit.json")
