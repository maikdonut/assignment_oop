import _path  # noqa: F401
from bank import Bank, Client
from accounts import BankAccount, AccountStatus, InvalidOperationError
from account_types import SavingsAccount, PremiumAccount, InvestmentAccount
from transactions import Transaction, TransactionQueue, TransactionProcessor, TransactionType
from audit import AuditReport, AuditLevel
from datetime import datetime, timedelta
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ===========================
# 1. ИНИЦИАЛИЗАЦИЯ
# ===========================
print("=" * 50)
print("🏦 БАНКОВСКАЯ СИСТЕМА — ПОЛНАЯ ДЕМОНСТРАЦИЯ")
print("=" * 50)

bank = Bank("PyBank")

clients_data = [
    ("Иванов И.И.",   "c001", 35, "pass001"),
    ("Петров П.П.",   "c002", 28, "pass002"),
    ("Сидоров С.С.",  "c003", 45, "pass003"),
    ("Козлова А.А.",  "c004", 31, "pass004"),
    ("Новиков Д.Д.",  "c005", 22, "pass005"),
    ("Морозова Е.Е.", "c006", 50, "pass006"),
    ("Волков А.А.",   "c007", 40, "pass007"),
    ("Лебедева О.О.", "c008", 33, "pass008"),
]

for name, cid, age, pwd in clients_data:
    bank.add_client(Client(name=name, client_id=cid, age=age, password=pwd))

print(f"\n✅ Добавлено клиентов: {len(bank.clients)}")

# 12 счетов
acc_ivanov    = BankAccount(account_id=None, owner_info="Иванов И.И.")
acc_ivanov2   = SavingsAccount(account_id=None, owner_info="Иванов И.И.", monthly_rate=0.08)
acc_petrov    = BankAccount(account_id=None, owner_info="Петров П.П.")
acc_petrov2   = PremiumAccount(account_id=None, owner_info="Петров П.П.", overdraft_limit=3000, commission=20)
acc_sidorov   = PremiumAccount(account_id=None, owner_info="Сидоров С.С.", overdraft_limit=10000, commission=50)
acc_kozlova   = SavingsAccount(account_id=None, owner_info="Козлова А.А.", monthly_rate=0.05, min_balance=1000)
acc_novikov   = BankAccount(account_id=None, owner_info="Новиков Д.Д.")
acc_morozova  = InvestmentAccount(account_id=None, owner_info="Морозова Е.Е.")
acc_morozova2 = PremiumAccount(account_id=None, owner_info="Морозова Е.Е.", overdraft_limit=5000, commission=30)
acc_volkov    = BankAccount(account_id=None, owner_info="Волков А.А.", currency="USD")
acc_lebedeva  = SavingsAccount(account_id=None, owner_info="Лебедева О.О.", monthly_rate=0.06)
acc_lebedeva2 = BankAccount(account_id=None, owner_info="Лебедева О.О.")

accounts_map = [
    ("c001", acc_ivanov), ("c001", acc_ivanov2),
    ("c002", acc_petrov), ("c002", acc_petrov2),
    ("c003", acc_sidorov),
    ("c004", acc_kozlova),
    ("c005", acc_novikov),
    ("c006", acc_morozova), ("c006", acc_morozova2),
    ("c007", acc_volkov),
    ("c008", acc_lebedeva), ("c008", acc_lebedeva2),
]

for cid, acc in accounts_map:
    bank.open_account(cid, acc)

print(f"✅ Открыто счетов: {len(bank.accounts)}")

# ===========================
# 2. НАЧАЛЬНЫЕ ДЕПОЗИТЫ
# ===========================
print("\n" + "=" * 50)
print("💰 НАЧАЛЬНЫЕ ДЕПОЗИТЫ")
print("=" * 50)

initial_deposits = [
    (acc_ivanov.account_id,    50000),
    (acc_ivanov2.account_id,   30000),
    (acc_petrov.account_id,    20000),
    (acc_petrov2.account_id,   15000),
    (acc_sidorov.account_id,   80000),
    (acc_kozlova.account_id,   15000),
    (acc_novikov.account_id,   10000),
    (acc_morozova.account_id,  60000),
    (acc_morozova2.account_id, 40000),
    (acc_volkov.account_id,    5000),
    (acc_lebedeva.account_id,  25000),
    (acc_lebedeva2.account_id, 10000),
]

for acc_id, amount in initial_deposits:
    bank.deposit(acc_id, amount)
    print(f"  Депозит {amount} → счёт {acc_id[-4:]}")

print(f"\n💎 Общий баланс банка: {bank.get_total_balance():,.0f} RUB")

# ===========================
# 3. СИМУЛЯЦИЯ ТРАНЗАКЦИЙ (35+)
# ===========================
print("\n" + "=" * 50)
print("🔄 СИМУЛЯЦИЯ ТРАНЗАКЦИЙ")
print("=" * 50)

queue = TransactionQueue()

transactions = [
    # обычные операции
    Transaction(TransactionType.DEPOSIT,    5000,  "",                      acc_petrov.account_id),
    Transaction(TransactionType.DEPOSIT,    3000,  "",                      acc_novikov.account_id),
    Transaction(TransactionType.WITHDRAWAL, 2000,  acc_ivanov.account_id,   ""),
    Transaction(TransactionType.WITHDRAWAL, 5000,  acc_sidorov.account_id,  ""),
    Transaction(TransactionType.TRANSFER,   10000, acc_ivanov.account_id,   acc_petrov.account_id),
    Transaction(TransactionType.TRANSFER,   5000,  acc_morozova.account_id, acc_kozlova.account_id),
    Transaction(TransactionType.TRANSFER,   3000,  acc_petrov.account_id,   acc_novikov.account_id),
    Transaction(TransactionType.DEPOSIT,    2000,  "",                      acc_kozlova.account_id),
    Transaction(TransactionType.WITHDRAWAL, 1000,  acc_novikov.account_id,  ""),
    Transaction(TransactionType.TRANSFER,   4000,  acc_sidorov.account_id,  acc_ivanov.account_id),
    Transaction(TransactionType.TRANSFER,   2500,  acc_lebedeva.account_id,   acc_lebedeva2.account_id),
    Transaction(TransactionType.TRANSFER,   1500,  acc_ivanov2.account_id,  acc_kozlova.account_id),
    Transaction(TransactionType.DEPOSIT,    1000,  "",                      acc_volkov.account_id),
    Transaction(TransactionType.WITHDRAWAL, 800,   acc_petrov2.account_id,  ""),
    Transaction(TransactionType.TRANSFER,   2000,  acc_morozova2.account_id, acc_novikov.account_id),
    Transaction(TransactionType.TRANSFER,   1200,  acc_petrov.account_id,   acc_lebedeva.account_id),
    Transaction(TransactionType.DEPOSIT,    3500,  "",                      acc_sidorov.account_id),
    Transaction(TransactionType.WITHDRAWAL, 600,   acc_lebedeva2.account_id, ""),
    Transaction(TransactionType.TRANSFER,   700,   acc_novikov.account_id,  acc_petrov.account_id),
    Transaction(TransactionType.TRANSFER,   900,   acc_kozlova.account_id,  acc_ivanov2.account_id),
    Transaction(TransactionType.DEPOSIT,    4500,  "",                      acc_morozova2.account_id),
    Transaction(TransactionType.WITHDRAWAL, 1100,  acc_ivanov.account_id,   ""),
    Transaction(TransactionType.TRANSFER,   1800,  acc_sidorov.account_id,  acc_morozova2.account_id),
    Transaction(TransactionType.TRANSFER,   2200,  acc_lebedeva.account_id, acc_petrov2.account_id),
    Transaction(TransactionType.DEPOSIT,    800,   "",                      acc_novikov.account_id),
    Transaction(TransactionType.WITHDRAWAL, 400,   acc_petrov.account_id,   ""),
    Transaction(TransactionType.TRANSFER,   600,   acc_ivanov.account_id,   acc_morozova.account_id),
    Transaction(TransactionType.TRANSFER,   500,   acc_kozlova.account_id,  acc_novikov.account_id),
    Transaction(TransactionType.DEPOSIT,    1500,  "",                      acc_ivanov2.account_id),
    # ошибочные
    Transaction(TransactionType.WITHDRAWAL, 999999, acc_novikov.account_id, ""),
    Transaction(TransactionType.WITHDRAWAL, 500,    acc_kozlova.account_id, ""),
    # подозрительные
    Transaction(TransactionType.DEPOSIT,    200000, "",                     acc_sidorov.account_id),
    Transaction(TransactionType.DEPOSIT,    150000, "",                     acc_morozova.account_id),
    # внешний перевод с комиссией
    Transaction(TransactionType.TRANSFER, 1000, acc_petrov.account_id, "ext-001", is_external=True),
    # приоритетная
    Transaction(TransactionType.DEPOSIT,    1000,   "",                     acc_ivanov.account_id),
]

for t in transactions[:-1]:
    queue.add(t)

scheduled = Transaction(TransactionType.DEPOSIT, 500, "", acc_novikov.account_id)
queue.schedule(scheduled, datetime.now() - timedelta(seconds=1))
transactions.append(scheduled)

queue.add(transactions[-2])
queue.add(transactions[-1], priority=True)

print(f"📋 Транзакций в очереди: {queue.pending_count}")

processor = TransactionProcessor(bank, max_retries=2)
processor.process_queue(queue)

print("\nСтатусы транзакций:")
for t in transactions:
    status_icon = "✅" if t.status.value == "completed" else "❌"
    reason = f" — {t.failure_reason}" if t.failure_reason else ""
    print(f"  {status_icon} {t.transaction_id[-4:]} | {t.transaction_type.value:10} | {t.amount:>10.0f} | {t.status.value}{reason}")

# ===========================
# 4. ИНВЕСТИЦИОННЫЙ СЧЁТ
# ===========================
print("\n" + "=" * 50)
print("📈 ИНВЕСТИЦИОННЫЙ ПОРТФЕЛЬ")
print("=" * 50)

acc_morozova.add_asset("stocks", 20000)
acc_morozova.add_asset("bonds",  15000)
acc_morozova.add_asset("etf",    10000)
growth = acc_morozova.project_yearly_growth(0.15)
print(f"  Портфель Морозовой: {acc_morozova.portfolio}")
print(f"  Прогноз роста (15%): {growth:,.0f} RUB")

# ===========================
# 5. ПОЛЬЗОВАТЕЛЬСКИЕ СЦЕНАРИИ
# ===========================
print("\n" + "=" * 50)
print("👤 СЧЕТА КЛИЕНТА — Иванов")
print("=" * 50)

for acc in bank.search_accounts("c001"):
    print(acc.get_account_info())
    print()

print("=" * 50)
print("📜 ИСТОРИЯ ТРАНЗАКЦИЙ — Иванов")
print("=" * 50)
for t in bank.get_client_transaction_history("c001")[-8:]:
    print(f"  {t.created_at.strftime('%H:%M:%S')} | {t.transaction_type.value:10} | {t.amount:>8.0f} | {t.status.value}")

# аутентификация
print("\n" + "=" * 50)
print("🔒 АУТЕНТИФИКАЦИЯ")
print("=" * 50)
print(f"  Верный пароль:   {bank.authenticate_client('c002', 'pass002')}")
print(f"  Неверный пароль: {bank.authenticate_client('c002', 'wrongpass')}")
print(f"  Неверный пароль: {bank.authenticate_client('c002', 'wrongpass')}")
print(f"  Неверный пароль: {bank.authenticate_client('c002', 'wrongpass')}")
try:
    bank.authenticate_client("c002", "pass002")
except InvalidOperationError as e:
    print(f"  Заблокирован: {e}")

# заморозка
print("\n" + "=" * 50)
print("❄️  ЗАМОРОЗКА СЧЁТА")
print("=" * 50)
bank.freeze_account("c005", acc_novikov.account_id)
print(f"  Статус счёта Новикова: {acc_novikov.status.value}")
try:
    bank.deposit(acc_novikov.account_id, 1000)
except Exception as e:
    print(f"  Попытка депозита: {e}")
bank.unfreeze_account("c005", acc_novikov.account_id)
print(f"  После разморозки: {acc_novikov.status.value}")

# ===========================
# 6. ОТЧЁТЫ
# ===========================
print("\n" + "=" * 50)
print("📊 ОТЧЁТЫ")
print("=" * 50)

print("\n🏆 Топ-3 клиентов по балансу:")
for i, client in enumerate(bank.get_clients_ranking(top_k=3), 1):
    total = sum(
        bank.accounts[acc_id].balance
        for acc_id in client.account_ids
        if acc_id in bank.accounts
    )
    print(f"  {i}. {client.name}: {total:,.0f} RUB")

completed = sum(1 for t in transactions if t.status.value == "completed")
failed    = sum(1 for t in transactions if t.status.value == "failed")
print(f"\n📊 Статистика транзакций:")
print(f"  Всего:     {len(transactions)}")
print(f"  Успешных:  {completed}")
print(f"  Неудачных: {failed}")

print(f"\n💎 Итоговый баланс банка: {bank.get_total_balance():,.0f} RUB")

report = AuditReport(bank.audit_log)
print(f"\n⚠️  Подозрительных операций: {len(report.get_suspicious_operations())}")
print(f"\n📋 Риск-профиль клиента c003:")
for entry in report.get_client_risk_profile("c003")[:5]:
    print(f"  [{entry.level.value}] {entry.message} | {entry.details}")

print(f"\n📋 Статистика аудита:")
for level, count in report.get_error_stats().items():
    print(f"  {level.value}: {count}")

bank.audit_log.save_to_file("demo6_audit.json")
print("\n✅ Лог сохранён в logs/demo6_audit.json")
