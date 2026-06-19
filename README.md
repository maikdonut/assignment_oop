# Banking System OOP Project


## Структура

```
src/
  accounts.py       — базовые счета и исключения
  account_types.py  — Savings, Premium, Investment
  bank.py           — банк и клиенты
  transactions.py   — транзакции, очередь, процессор
  audit.py          — аудит и риск-анализ
  reports.py        — отчёты и графики
  demos/            — демонстрации по дням 1–7
reports/            — JSON, CSV, графики (генерирует demo7)
logs/               — файлы аудита
```

## Установка



**pip:**
```powershell
pip install -r requirements.txt
```

## Запуск

Из корня проекта:

```powershell
python src/demos/demo1.py   # День 1 — базовые счета
python src/demos/demo2.py   # День 2 — типы счетов
python src/demos/demo3.py   # День 3 — банк и клиенты
python src/demos/demo4.py   # День 4 — транзакции и очередь
python src/demos/demo5.py   # День 5 — аудит и риски
python src/demos/demo6.py   # День 6 — полная симуляция
python src/demos/demo7.py   # День 7 — отчёты и графики
```

## Результаты

После `demo7` в папке `reports/`:
- `report.json`, `transactions.csv`
- `chart_transaction_status.png`
- `chart_balance_by_client.png`
- `chart_transaction_types.png`
- `chart_balance_movement.png`

Логи аудита сохраняются в `logs/`.
