import os
import json
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from transactions import Transaction, TransactionType


class AuditLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class RiskLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class AuditEntry:
    level: AuditLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: dict = field(default_factory=dict)


class AuditLog:
    def __init__(self):
        self._entries = []

    def log_message(self, level: AuditLevel, message: str, details: dict = None) -> None:
        entry = AuditEntry(
            level=level,
            message=message,
            details=details or {}
        )
        self._entries.append(entry)

    def filter_level(self, level: AuditLevel) -> list:
        return [entry for entry in self._entries if entry.level == level]

    def filter(self, level: AuditLevel = None, client_id: str = None) -> list:
        result = self._entries
        if level is not None:
            result = [e for e in result if e.level == level]
        if client_id is not None:
            result = [e for e in result if e.details.get("client_id") == client_id]
        return result

    def save_to_file(self, filename: str, path: str = "logs") -> None:
        os.makedirs(path, exist_ok=True)
        filepath = os.path.join(path, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            data = [
                {
                    "level": entry.level.value,
                    "message": entry.message,
                    "timestamp": entry.timestamp.isoformat(),
                    "details": entry.details
                }
                for entry in self._entries
            ]
            json.dump(data, f, ensure_ascii=False, indent=2)


class RiskAnalyzer:
    def __init__(self, audit_log: AuditLog, large_amount: int = 100000, frequent_ops_limit: int = 10):
        self.audit_log = audit_log
        self.large_amount = large_amount
        self.frequent_ops_limit = frequent_ops_limit
        self._transaction_history = []
        self._known_receivers = {}

    def _account_key(self, transaction: Transaction) -> str:
        if transaction.transaction_type == TransactionType.DEPOSIT:
            return transaction.receiver_id
        return transaction.sender_id

    def analyze(self, transaction: Transaction, bank=None) -> RiskLevel:
        client_id = ""
        if bank is not None:
            client_id = bank.get_client_id_for_account(
                transaction.sender_id or transaction.receiver_id
            )

        risks = [
            self._check_large_amount(transaction, client_id),
            self._check_night_operation(transaction, client_id),
            self._check_frequent_ops(transaction, client_id),
        ]
        if bank is not None:
            risks.append(self._check_new_account_transfer(transaction, bank, client_id))

        self._transaction_history.append(transaction)
        return max(risks, key=lambda r: r.value)

    def _check_large_amount(self, transaction: Transaction, client_id: str) -> RiskLevel:
        if transaction.amount >= self.large_amount:
            self.audit_log.log_message(
                AuditLevel.WARNING,
                "Крупная транзакция",
                {
                    "amount": transaction.amount,
                    "transaction_id": transaction.transaction_id,
                    "client_id": client_id,
                }
            )
            return RiskLevel.HIGH
        return RiskLevel.LOW

    def _check_frequent_ops(self, transaction: Transaction, client_id: str) -> RiskLevel:
        account_key = self._account_key(transaction)
        if not account_key:
            return RiskLevel.LOW
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent = [
            t for t in self._transaction_history
            if self._account_key(t) == account_key
            and t.created_at >= one_hour_ago
        ]
        if len(recent) >= self.frequent_ops_limit:
            self.audit_log.log_message(
                AuditLevel.WARNING,
                "Частые операции",
                {
                    "transaction_id": transaction.transaction_id,
                    "client_id": client_id,
                    "count": len(recent) + 1,
                }
            )
            return RiskLevel.HIGH
        return RiskLevel.LOW

    def _check_night_operation(self, transaction: Transaction, client_id: str) -> RiskLevel:
        hour = transaction.created_at.hour
        if 0 <= hour < 5:
            self.audit_log.log_message(
                AuditLevel.WARNING,
                "Ночная операция",
                {
                    "transaction_id": transaction.transaction_id,
                    "hour": hour,
                    "client_id": client_id,
                }
            )
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _check_new_account_transfer(self, transaction: Transaction, bank, client_id: str) -> RiskLevel:
        if transaction.transaction_type != TransactionType.TRANSFER:
            return RiskLevel.LOW
        if not transaction.receiver_id or transaction.receiver_id not in bank.accounts:
            return RiskLevel.LOW

        known = self._known_receivers.setdefault(transaction.sender_id, set())
        if transaction.receiver_id not in known:
            is_new = len(known) > 0
            known.add(transaction.receiver_id)
            if is_new:
                self.audit_log.log_message(
                    AuditLevel.WARNING,
                    "Перевод на новый счёт",
                    {
                        "transaction_id": transaction.transaction_id,
                        "sender_id": transaction.sender_id,
                        "receiver_id": transaction.receiver_id,
                        "client_id": client_id,
                    }
                )
                return RiskLevel.MEDIUM
        return RiskLevel.LOW


class AuditReport:
    def __init__(self, audit_log: AuditLog):
        self.audit_log = audit_log

    def get_suspicious_operations(self) -> list:
        return [
            entry for entry in self.audit_log._entries
            if entry.level in (AuditLevel.WARNING, AuditLevel.CRITICAL)
        ]

    def get_client_risk_profile(self, client_id: str) -> list:
        return self.audit_log.filter(client_id=client_id)

    def get_error_stats(self) -> dict:
        stats = {level: 0 for level in AuditLevel}
        for entry in self.audit_log._entries:
            stats[entry.level] += 1
        return stats
