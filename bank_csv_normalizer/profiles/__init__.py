from .israeli_cards_aggregate_v1 import IsraeliCardsAggregateV1
from .israeli_credit_card_v1 import IsraeliCreditCardV1
from .discount_bank_visa_v1 import DiscountBankVisaV1

ALL_PROFILES = [
    IsraeliCardsAggregateV1(),
    IsraeliCreditCardV1(),
    DiscountBankVisaV1(),
]
