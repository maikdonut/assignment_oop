import os
import json
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from bank import Bank
from audit import AuditReport, AuditLevel



class ReportBuilder:
    def __init__(self, bank: Bank, transactions: list, output_dir: str = "reports"):
        self.bank = bank
        self.transactions = transactions
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # ===========================
    # ТЕКСТОВЫЕ ОТЧЁТЫ
    # ===========================

    def client_report(self, client_id: str) -> str:
        if client_id not in self.bank.clients:
            raise ValueError("Клиент не найден")
        client = self.bank.clients[client_id]
        accounts = self.bank.search_accounts(client_id)
        total = sum(acc.balance for acc in accounts)

        lines = [
            f"{'=' * 40}",
            f"ОТЧЁТ ПО КЛИЕНТУ: {client.name}",
            f"{'=' * 40}",
            f"ID: {client.client_id}",
            f"Возраст: {client.age}",
            f"Статус: {'активен' if client.status else 'заблокирован'}",
            f"Счетов: {len(accounts)}",
            f"Общий баланс: {total:,.2f} RUB",
            f"\nСчета:",
        ]
        for acc in accounts:
            lines.append(f"  - {acc.account_id} | {acc.__class__.__name__} | {acc.balance:,.2f} {acc.currency} | {acc.status.value}")

        client_txns = [
            t for t in self.transactions
            if t.sender_id in [a.account_id for a in accounts]
            or t.receiver_id in [a.account_id for a in accounts]
        ]
        lines.append(f"\nТранзакций: {len(client_txns)}")
        completed = sum(1 for t in client_txns if t.status.value == "completed")
        failed = sum(1 for t in client_txns if t.status.value == "failed")
        lines.append(f"  Успешных: {completed}")
        lines.append(f"  Неудачных: {failed}")

        history = self.bank.get_client_transaction_history(client_id)
        if history:
            lines.append("\nИстория операций:")
            for t in history[-10:]:
                lines.append(
                    f"  {t.created_at.strftime('%H:%M:%S')} | {t.transaction_type.value} | "
                    f"{t.amount:,.0f} | {t.status.value}"
                )

        return "\n".join(lines)

    def bank_report(self) -> str:
        total_balance = self.bank.get_total_balance()
        completed = sum(1 for t in self.transactions if t.status.value == "completed")
        failed = sum(1 for t in self.transactions if t.status.value == "failed")

        lines = [
            f"{'=' * 40}",
            f"ОТЧЁТ ПО БАНКУ: {self.bank.name}",
            f"{'=' * 40}",
            f"Клиентов: {len(self.bank.clients)}",
            f"Счетов: {len(self.bank.accounts)}",
            f"Общий баланс: {total_balance:,.2f} RUB",
            f"\nТранзакции:",
            f"  Всего: {len(self.transactions)}",
            f"  Успешных: {completed}",
            f"  Неудачных: {failed}",
            f"\nРейтинг клиентов (топ-3):",
        ]
        for i, client in enumerate(self.bank.get_clients_ranking(top_k=3), 1):
            total = sum(
                self.bank.accounts[acc_id].balance
                for acc_id in client.account_ids
                if acc_id in self.bank.accounts
            )
            lines.append(f"  {i}. {client.name}: {total:,.2f} RUB")

        return "\n".join(lines)

    def risk_report(self) -> str:
        report = AuditReport(self.bank.audit_log)
        suspicious = report.get_suspicious_operations()
        stats = report.get_error_stats()

        lines = [
            f"{'=' * 40}",
            f"ОТЧЁТ ПО РИСКАМ",
            f"{'=' * 40}",
            f"Подозрительных операций: {len(suspicious)}",
            f"\nСтатистика аудита:",
        ]
        for level, count in stats.items():
            lines.append(f"  {level.value}: {count}")

        lines.append("\nПодозрительные операции:")
        for entry in suspicious:
            lines.append(f"  [{entry.level.value}] {entry.timestamp.strftime('%H:%M:%S')} — {entry.message} | {entry.details}")

        return "\n".join(lines)

    # ===========================
    # ЭКСПОРТ
    # ===========================

    def export_to_json(self, filename: str = "report.json") -> None:
        data = {
            "bank": self.bank.name,
            "generated_at": datetime.now().isoformat(),
            "total_balance": self.bank.get_total_balance(),
            "clients_count": len(self.bank.clients),
            "accounts_count": len(self.bank.accounts),
            "transactions": [
                {
                    "id": t.transaction_id,
                    "type": t.transaction_type.value,
                    "amount": t.amount,
                    "status": t.status.value,
                    "failure_reason": t.failure_reason,
                    "created_at": t.created_at.isoformat(),
                }
                for t in self.transactions
            ]
        }
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"JSON сохранён: {filepath}")

    def export_to_csv(self, filename: str = "transactions.csv") -> None:
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "type", "amount", "currency", "sender", "receiver", "status", "failure_reason", "created_at"])
            for t in self.transactions:
                writer.writerow([
                    t.transaction_id,
                    t.transaction_type.value,
                    t.amount,
                    t.currency,
                    t.sender_id,
                    t.receiver_id,
                    t.status.value,
                    t.failure_reason,
                    t.created_at.isoformat(),
                ])
        print(f"CSV сохранён: {filepath}")

    # ===========================
    # ГРАФИКИ
    # ===========================

    def save_charts(self) -> None:
        self._chart_transaction_status()
        self._chart_balance_by_client()
        self._chart_transaction_types()
        self._chart_balance_movement()

    def _chart_transaction_status(self) -> None:
        completed = sum(1 for t in self.transactions if t.status.value == "completed")
        failed = sum(1 for t in self.transactions if t.status.value == "failed")

        plt.figure(figsize=(6, 6))
        plt.pie(
            [completed, failed],
            labels=["Успешные", "Неудачные"],
            colors=["#4CAF50", "#F44336"],
            autopct="%1.1f%%",
            startangle=90
        )
        plt.title("Статусы транзакций")
        filepath = os.path.join(self.output_dir, "chart_transaction_status.png")
        plt.savefig(filepath)
        plt.close()
        print(f"График сохранён: {filepath}")

    def _chart_balance_by_client(self) -> None:
        names = []
        balances = []
        for client in self.bank.get_clients_ranking():
            total = sum(
                self.bank.accounts[acc_id].balance
                for acc_id in client.account_ids
                if acc_id in self.bank.accounts
            )
            names.append(client.name.split()[0])
            balances.append(total)

        plt.figure(figsize=(10, 5))
        plt.bar(names, balances, color="#2196F3")
        plt.title("Баланс по клиентам")
        plt.xlabel("Клиент")
        plt.ylabel("Баланс (RUB)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, "chart_balance_by_client.png")
        plt.savefig(filepath)
        plt.close()
        print(f"График сохранён: {filepath}")

    def _chart_transaction_types(self) -> None:
        from collections import Counter
        counts = Counter(t.transaction_type.value for t in self.transactions)

        plt.figure(figsize=(6, 6))
        plt.pie(
            counts.values(),
            labels=counts.keys(),
            autopct="%1.1f%%",
            startangle=90
        )
        plt.title("Типы транзакций")
        filepath = os.path.join(self.output_dir, "chart_transaction_types.png")
        plt.savefig(filepath)
        plt.close()
        print(f"График сохранён: {filepath}")

    def _chart_balance_movement(self) -> None:
        snapshots = self.bank.get_balance_snapshots()
        if len(snapshots) < 2:
            return

        times = [s[0] for s in snapshots]
        balances = [s[1] for s in snapshots]

        plt.figure(figsize=(10, 5))
        plt.plot(times, balances, marker="o", color="#FF9800", linewidth=2)
        plt.title("Движение общего баланса банка")
        plt.xlabel("Время")
        plt.ylabel("Баланс (RUB)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, "chart_balance_movement.png")
        plt.savefig(filepath)
        plt.close()
        print(f"График сохранён: {filepath}")