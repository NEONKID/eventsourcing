from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

from eventsourcing.domain import Aggregate


class TransactionError(Exception):
    pass


class AccountClosedError(TransactionError):
    pass


class InsufficientFundsError(TransactionError):
    pass


class BankAccount(Aggregate):
    def __init__(self, full_name: str, email_address: str, **kwargs: Any):
        super().__init__(**kwargs)
        self.full_name = full_name
        self.email_address = email_address
        self.balance = Decimal("0.00")
        self.overdraft_limit = Decimal("0.00")
        self.is_closed = False

    @classmethod
    def open(cls, full_name: str, email_address: str) -> "BankAccount":
        return super()._create(
            cls.Opened,
            id=uuid4(),
            full_name=full_name,
            email_address=email_address,
        )

    @dataclass(frozen=True)
    class Opened(Aggregate.Created):
        full_name: str
        email_address: str

    def append_transaction(
        self, amount: Decimal, transaction_id: Optional[UUID] = None
    ) -> None:
        self.check_account_is_not_closed()
        self.check_has_sufficient_funds(amount)
        self._trigger_event(
            self.TransactionAppended,
            amount=amount,
            transaction_id=transaction_id,
        )

    def check_account_is_not_closed(self) -> None:
        if self.is_closed:
            raise AccountClosedError({"account_id": self.id})

    def check_has_sufficient_funds(self, amount: Decimal) -> None:
        if self.balance + amount < -self.overdraft_limit:
            raise InsufficientFundsError({"account_id": self.id})

    @dataclass(frozen=True)
    class TransactionAppended(Aggregate.Event):
        amount: Decimal
        transaction_id: UUID

        def apply(self, aggregate: "BankAccount") -> None:
            aggregate.balance += self.amount

    def set_overdraft_limit(self, overdraft_limit: Decimal) -> None:
        assert overdraft_limit > Decimal("0.00")
        self.check_account_is_not_closed()
        self._trigger_event(
            self.OverdraftLimitSet,
            overdraft_limit=overdraft_limit,
        )

    @dataclass(frozen=True)
    class OverdraftLimitSet(Aggregate.Event):
        overdraft_limit: Decimal

        def apply(self, aggregate: "BankAccount") -> None:
            aggregate.overdraft_limit = self.overdraft_limit

    def close(self) -> None:
        self._trigger_event(self.Closed)

    @dataclass(frozen=True)
    class Closed(Aggregate.Event):
        def apply(self, aggregate: "BankAccount") -> None:
            aggregate.is_closed = True

    # def record_error(
    #     self, error: Exception, transaction_id=None
    # ):
    #     self._trigger_event(
    #         self.ErrorRecorded,
    #         error=error,
    #         transaction_id=transaction_id,
    #     )
    #
    # class ErrorRecorded(Aggregate.Event):
    #     @property
    #     def error(self):
    #         return self.__dict__["error"]
