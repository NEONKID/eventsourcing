from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from unittest.case import TestCase
from uuid import uuid4

from eventsourcing.domain import Aggregate, TZINFO, VersionError


class TestAggregate(TestCase):
    def test_aggregate_base_class(self):
        # Check the _create() method creates a new aggregate.
        before_created = datetime.now(tz=TZINFO)
        uuid = uuid4()
        a = Aggregate._create(
            event_class=Aggregate.Created,
            id=uuid,
        )
        after_created = datetime.now(tz=TZINFO)
        self.assertIsInstance(a, Aggregate)
        self.assertEqual(a.id, uuid)
        self.assertEqual(a.version, 1)
        self.assertEqual(a.created_on, a.modified_on)
        self.assertGreater(a.created_on, before_created)
        self.assertGreater(after_created, a.created_on)

        # Check the aggregate can trigger further events.
        a._trigger_event(Aggregate.Event)
        self.assertLess(a.created_on, a.modified_on)

        pending = a.collect_events()
        self.assertEqual(len(pending), 2)
        self.assertIsInstance(pending[0], Aggregate.Created)
        self.assertEqual(pending[0].originator_version, 1)
        self.assertIsInstance(pending[1], Aggregate.Event)
        self.assertEqual(pending[1].originator_version, 2)

        # Try to mutate aggregate with an invalid domain event.
        next_version = a.version
        event = Aggregate.Event(
            originator_id=a.id,
            originator_version=next_version,
            timestamp=datetime.now(tz=TZINFO),
        )
        # Check raises "VersionError".
        with self.assertRaises(VersionError):
            event.mutate(a)

    def test_subclass_bank_account(self):

        # Open an account.
        account: BankAccount = BankAccount.open(
            full_name="Alice",
            email_address="alice@example.com",
        )

        # Check the created_on.
        assert account.created_on == account.modified_on

        # Check the initial balance.
        assert account.balance == 0

        # Credit the account.
        account.append_transaction(Decimal("10.00"))

        # Check the modified_on time was updated.
        assert account.created_on < account.modified_on

        # Check the balance.
        assert account.balance == Decimal("10.00")

        # Credit the account again.
        account.append_transaction(Decimal("10.00"))

        # Check the balance.
        assert account.balance == Decimal("20.00")

        # Debit the account.
        account.append_transaction(Decimal("-15.00"))

        # Check the balance.
        assert account.balance == Decimal("5.00")

        # Fail to debit account (insufficient funds).
        try:
            account.append_transaction(Decimal("-15.00"))
        except InsufficientFundsError:
            pass
        else:
            raise Exception("Insufficient funds error not raised")

        # Increase the overdraft limit.
        account.set_overdraft_limit(Decimal("100.00"))

        # Debit the account.
        account.append_transaction(Decimal("-15.00"))

        # Check the balance.
        assert account.balance == Decimal("-10.00")

        # Close the account.
        account.close()

        # Fail to debit account (account closed).
        try:
            account.append_transaction(Decimal("-15.00"))
        except AccountClosedError:
            pass
        else:
            raise Exception("Account closed error not raised")

        # Collect pending events.
        pending = account.collect_events()
        assert len(pending) == 7

    def test_raises_type_error_when_created_event_is_broken(self):

        class BrokenAggregate(Aggregate):
            @classmethod
            def create(cls, name):
                return cls._create(
                    event_class=cls.Created,
                    id=uuid4(),
                    name=name
                )

        with self.assertRaises(TypeError) as cm:
            BrokenAggregate.create('name')
        self.assertEqual(
            cm.exception.args[0], (
                "Unable to construct event with class Aggregate.Created"
                " and keyword args {'name': 'name'}: __init__() got an "
                "unexpected keyword argument 'name'"
            )
        )


class BankAccount(Aggregate):
    """
    Aggregate root for bank accounts.
    """

    def __init__(self, full_name: str, email_address: str, **kwargs):
        super().__init__(**kwargs)
        self.full_name = full_name
        self.email_address = email_address
        self.balance = Decimal("0.00")
        self.overdraft_limit = Decimal("0.00")
        self.is_closed = False

    @classmethod
    def open(cls, full_name: str, email_address: str) -> "BankAccount":
        """
        Creates new bank account object.
        """
        return cls._create(
            cls.Opened,
            id=uuid4(),
            full_name=full_name,
            email_address=email_address,
        )

    @dataclass(frozen=True)
    class Opened(Aggregate.Created):
        full_name: str
        email_address: str

    def append_transaction(self, amount: Decimal) -> None:
        """
        Appends given amount as transaction on account.
        """
        self.check_account_is_not_closed()
        self.check_has_sufficient_funds(amount)
        self._trigger_event(
            self.TransactionAppended,
            amount=amount,
        )

    def check_account_is_not_closed(self) -> None:
        if self.is_closed:
            raise AccountClosedError({"account_id": self.id})

    def check_has_sufficient_funds(self, amount: Decimal) -> None:
        if self.balance + amount < -self.overdraft_limit:
            raise InsufficientFundsError({"account_id": self.id})

    @dataclass(frozen=True)
    class TransactionAppended(Aggregate.Event):
        """
        Domain event for when transaction
        is appended to bank account.
        """

        amount: Decimal

        def apply(self, account: "BankAccount") -> None:
            """
            Increments the account balance.
            """
            account.balance += self.amount

    def set_overdraft_limit(self, overdraft_limit: Decimal) -> None:
        """
        Sets the overdraft limit.
        """
        # Check the limit is not a negative value.
        assert overdraft_limit >= Decimal("0.00")
        self.check_account_is_not_closed()
        self._trigger_event(
            self.OverdraftLimitSet,
            overdraft_limit=overdraft_limit,
        )

    @dataclass(frozen=True)
    class OverdraftLimitSet(Aggregate.Event):
        """
        Domain event for when overdraft
        limit is set.
        """

        overdraft_limit: Decimal

        def apply(self, account: "BankAccount"):
            account.overdraft_limit = self.overdraft_limit

    def close(self) -> None:
        """
        Closes the bank account.
        """
        self._trigger_event(self.Closed)

    @dataclass(frozen=True)
    class Closed(Aggregate.Event):
        """
        Domain event for when account is closed.
        """

        def apply(self, account: "BankAccount"):
            account.is_closed = True


class AccountClosedError(Exception):
    """
    Raised when attempting to operate a closed account.
    """


class InsufficientFundsError(Exception):
    """
    Raised when attempting to go past overdraft limit.
    """
