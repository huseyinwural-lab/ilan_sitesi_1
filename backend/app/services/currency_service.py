
import logging
from decimal import Decimal
from typing import Dict

logger = logging.getLogger(__name__)

class CurrencyService:
    # Static Exchange Rates (MVP) - Base: EUR
    EXCHANGE_RATES = {
        "EUR": Decimal("1.0"),
        "USD": Decimal("1.1"),
        "TRY": Decimal("35.0"), # Dynamic updates needed in prod
        "GBP": Decimal("0.85")
    }

    SYMBOL_MAP = {
        "EUR": "€",
        "USD": "$",
        "TRY": "₺",
        "GBP": "£"
    }

    @staticmethod
    def convert(amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        if from_currency == to_currency:
            return amount
            
        # Convert to Base (EUR)
        rate_from = CurrencyService.EXCHANGE_RATES.get(from_currency)
        if not rate_from:
            raise ValueError(f"Unsupported currency: {from_currency}")
            
        amount_eur = amount / rate_from
        
        # Convert to Target
        rate_to = CurrencyService.EXCHANGE_RATES.get(to_currency)
        if not rate_to:
            raise ValueError(f"Unsupported currency: {to_currency}")
            
        return round(amount_eur * rate_to, 2)

    @staticmethod
    def format_currency(amount: Decimal, currency: str, locale: str = "en") -> str:
        symbol = CurrencyService.SYMBOL_MAP.get(currency, currency)
        
        # Simple formatting logic (Can be improved with babel library)
        try:
            val = float(amount)
            if locale == "tr":
                # 1.000,00 ₺
                formatted = "{:,.2f}".format(val).replace(",", "X").replace(".", ",").replace("X", ".")
                return f"{formatted} {symbol}"
            else:
                # €1,000.00
                formatted = "{:,.2f}".format(val)
                return f"{symbol}{formatted}"
        except:
            return f"{amount} {currency}"
