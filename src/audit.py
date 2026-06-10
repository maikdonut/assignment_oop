import os
import json
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from accounts import InvalidOperationError
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

    def analyze(self, transaction: Transaction) -> RiskLevel:
        risks = []
        risks.append(self._check_large_amount(transaction))
        risks.append(self._check_night_operation(transaction))
        risks.append(self._check_frequent_ops(transaction))
        self._transaction_history.append(transaction)
        return max(risks, key=lambda r: r.value)

    def _check_large_amount(self, transaction: Transaction) -> RiskLevel:
        if transaction.amount >= self.large_amount:
            self.audit_log.log_message(
                AuditLevel.WARNING,
                "Крупная транзакция",
                {"amount": transaction.amount, "transaction_id": transaction.transaction_id}
            )
            return RiskLevel.HIGH
        return RiskLevel.LOW

    def _check_frequent_ops(self, transaction: Transaction) -> RiskLevel:
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent = [
            t for t in self._transaction_history
            if t.sender_id == transaction.sender_id
            and t.created_at >= one_hour_ago
        ]
        if len(recent) >= self.frequent_ops_limit:
            return RiskLevel.HIGH
        return RiskLevel.LOW

    def _check_night_operation(self, transaction: Transaction) -> RiskLevel:
        hour = transaction.created_at.hour
        if 0 <= hour < 5:
            self.audit_log.log_message(
                AuditLevel.WARNING,
                "Ночная операция",
                {"transaction_id": transaction.transaction_id, "hour": hour}
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
        return [
            entry for entry in self.audit_log._entries
            if entry.details.get("client_id") == client_id
        ]

    def get_error_stats(self) -> dict:
        stats = {level: 0 for level in AuditLevel}
        for entry in self.audit_log._entries:
            stats[entry.level] += 1
        return stats