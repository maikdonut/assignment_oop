from abc import ABC, abstractmethod
from enum import Enum
import uuid


class AccountFrozenError(Exception):
    pass


class AccountClosedError(Exception):
    pass


class InvalidOperationError(Exception):
    pass


class InsufficientFundsError(Exception):
    pass



class AccountStatus(Enum):
    ACTIVE = "активный"
    FROZEN = "замороженный"
    CLOSED = "закрытый"

class Currency(Enum):   
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    KZT = "KZT"
    CNY = "CNY"


class AbstractAccount(ABC):

    def __init__(self, account_id, owner_info):
        self.account_id = account_id
        self.owner_info = owner_info
        self.status = AccountStatus.ACTIVE
        self._balance = 0
    
    @property
    def balance(self):
        return self._balance

    @abstractmethod
    def deposit(self, amount: float) -> None:
        pass

    @abstractmethod
    def withdraw(self, amount: float) -> None:
        pass

    @abstractmethod
    def get_account_info(self) -> str:
        pass
    

class BankAccount(AbstractAccount):
    """
    Банковский счет.
    
    Поддерживает пополнение, снятие и управление статусом.
    Автоматически генерирует короткий UUID, если account_id не передан.
    
    Атрибуты:
        account_id (str): Уникальный идентификатор счёта.
        owner_info (str): Имя или информация о владельце.
        currency (str): Валюта счёта. Одна из: RUB, USD, EUR, KZT, CNY.
        status (AccountStatus): Текущий статус счёта.
    
    Исключения:
        InvalidOperationError: Если owner_info пустой или валюта неверная.
    """
    def __init__(self, account_id, owner_info, currency="RUB"):
        if not owner_info:
            raise InvalidOperationError("Нет информации о владельце счета")
        if currency not in ("RUB", "USD", "EUR", "KZT", "CNY"):
            raise InvalidOperationError("Неверная валюта")
        if account_id is None:
            account_id = str(uuid.uuid4())[:8]
        super().__init__(account_id, owner_info)
        self.currency = currency

    def _check_status(self):
        if self.status == AccountStatus.FROZEN:
            raise AccountFrozenError("Счет заморожен")
        if self.status == AccountStatus.CLOSED:
            raise AccountClosedError("Счет закрыт")
        

    def deposit(self, amount: float) -> None:
        self._check_status()
        if amount <= 0:
            raise InvalidOperationError("Сумма должна быть положительной")
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        self._check_status()
        if amount <= 0:
            raise InvalidOperationError("Сумма должна быть положительной")
        if amount > self._balance:
            raise InsufficientFundsError("Недостаточно средств")
        self._balance -= amount

    def get_account_info(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return "\n".join([
            f"Тип счета: {self.__class__.__name__}",
            f"Клиент: {self.owner_info}",
            f"№ счета: ****{self.account_id[-4:]}",
            f"Статус: {self.status.value}",
            f"Баланс: {self._balance} {self.currency}"
        ])
    