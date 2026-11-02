"""
Assignment 1

"""

import datetime
from math import ceil
from typing import Optional
from bill import Bill
from call import Call

# Constants for the month-to-month contract monthly fee and term deposit
MTM_MONTHLY_FEE = 50.00
TERM_MONTHLY_FEE = 20.00
TERM_DEPOSIT = 300.00

# Constants for the included minutes and SMSs in the term contracts (per month)
TERM_MINS = 100

# Cost per minute and per SMS in the month-to-month contract
MTM_MINS_COST = 0.05

# Cost per minute and per SMS in the term contract
TERM_MINS_COST = 0.1

# Cost per minute and per SMS in the prepaid contract
PREPAID_MINS_COST = 0.025


class Contract:
    """ A contract for a phone line

    This class is not to be changed or instantiated. It is an Abstract Class.

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    """
    start: Optional[datetime.date]
    bill: Optional[Bill]

    def __init__(self, start: Optional[datetime.date]) -> None:
        """ Create a new Contract with the <start> date, starts as inactive
        """
        self.start = start
        self.bill = None

    def is_active(self, month: int, year: int) -> bool:
        """ Return True if the contract is active during the given <month>
        and <year>, and False otherwise.
        """
        return (self.start is not None and (self.start.year < year or (
                self.start.year == year and self.start.month <= month)))

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.

        DO NOT CHANGE THIS METHOD
        """
        raise NotImplementedError

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        self.bill.add_billed_minutes(ceil(call.duration / 60.0))

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        return self.bill.get_cost()


class MTMContract(Contract):
    """ A month to month contract for a phone line """

    def __init__(self, start: Optional[datetime.date]) -> None:
        """ Create a new Contract with the <start> date, starts as inactive
        """
        super().__init__(start)
        self.start = start
        self.bill = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
           <year>. This may be the first month of the contract.
           Store the <bill> argument in this contract and set the appropriate
            rate per minute and fixed cost.
        """
        if self.start is not None:
            self.bill = bill

        if self.bill is not None:
            self.bill.set_rates("MTM", MTM_MINS_COST)
            self.bill.add_fixed_cost(MTM_MONTHLY_FEE)


class TermContract(Contract):
    """ A term contract for a phone line """
    finish: datetime.datetime
    dead: bool
    extra_mins: int

    def __init__(self, start: datetime.date, end: datetime.date) -> None:
        """ Create a new Term Contract with the <start> date, starts as
        inactive, and <end> date when contract is being terminated.
        This class inherits Contract superclass.
        """
        Contract.__init__(self, start)
        self.extra_mins = TERM_MINS
        self.dead = False
        self.finish = end

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
            <year>. This may be the first month of the contract.
            Store the <bill> argument in this contract and set the appropriate
             rate per minute and fixed cost.
        """
        if self.start is not None:
            self.extra_mins = TERM_MINS
            self.bill = bill
            self.bill.set_rates("TERM", TERM_MINS_COST)
            fixed_cost = TERM_DEPOSIT + TERM_MONTHLY_FEE \
                if (self.start.year == year) and (self.start.month == month) \
                else TERM_MONTHLY_FEE
            self.bill.add_fixed_cost(fixed_cost)
            self.dead = True if (self.finish.year == year) and \
                                (self.finish.month > month) \
                else False

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.
        """
        duration = call.duration // 60 + (1 if call.duration % 60 > 0 else 0)

        if duration <= self.extra_mins:
            self.bill.add_free_minutes(duration)
            self.extra_mins = self.extra_mins - duration
        else:
            if self.extra_mins > 0:
                billed_minutes = duration - self.extra_mins
                self.bill.add_free_minutes(self.extra_mins)
                self.extra_mins = 0
                self.bill.add_billed_minutes(billed_minutes)
            else:
                self.bill.add_billed_minutes(duration)

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
         with this contract.

         Precondition:
         - a bill has already been created for the month+year when this
          contract is being cancelled.
        """
        self.start = None
        cost = self.bill.get_cost()
        return cost - TERM_DEPOSIT if self.dead else cost


class PrepaidContract(Contract):
    """ A prepaid contract for a phone line """
    balance: float

    def __init__(self, start: datetime.date, balance: float) -> None:
        """ Create a new Term Contract with the <start> date, starts as
         inactive.
        """

        Contract.__init__(self, start)
        self.balance = -balance

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
           <year>. This may be the first month of the contract.
           Store the <bill> argument in this contract and set the appropriate
            rate per minute and fixed cost.
        """
        if self.start is not None and self.bill is None:
            self.bill = bill
            self.bill.set_rates('PREPAID', PREPAID_MINS_COST)
            self.bill.add_fixed_cost(self.balance)
        elif self.start is None:
            pass
        else:
            self.bill.set_rates('PREPAID', PREPAID_MINS_COST)
            self.balance = self.bill.get_cost()
            self.balance = self.balance - 25.00 if 0 > self.balance > -10 \
                else self.balance
            self.bill.add_fixed_cost(self.balance)
            self.bill = bill

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
         with this contract.
        """
        if self.bill is not None and self.bill.get_cost() > 0:
            self.start = self.bill.get_cost()
        else:
            self.start = 0

        return self.start


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-import-modules': [
            'python_ta', 'typing', 'datetime', 'bill', 'call', 'math'
        ],
        'disable': ['R0902', 'R0913'],
        'generated-members': 'pygame.*'
    })
