from .policy_base import BaseMonetaryPolicy
import numpy as np

class AggMonetaryPolicy3(BaseMonetaryPolicy):
    def __init__(self):
        # Constants from the contract
        self.MAX_RATE = 43959106799  # 300% APY
        self.MAX_EXP = 1000 * 10**18
        self.MIN_SIGMA = 10**14
        self.MAX_SIGMA = 10**18
        self.TARGET_REMAINDER = 10**17
        self.MAX_TARGET_DEBT_FRACTION = 10**18

    @property
    def policy_name(self):
        return "Aggregated Monetary Policy v3"

    @property
    def required_parameters(self):
        return {
            'price': 'Current price (in 1e18)',
            'sigma': f'Volatility parameter ({self.MIN_SIGMA} to {self.MAX_SIGMA})',
            'rate0': f'Base rate (0 to {self.MAX_RATE})',
            'target_debt_fraction': f'Target debt fraction (0 to {self.MAX_TARGET_DEBT_FRACTION})',
            'debt_for': 'Debt for specific market (optional)',
            'total_debt': 'Total system debt (optional)',
            'pk_debt': 'PegKeeper debt (optional)',
            'ceiling': 'Debt ceiling (optional)'
        }

    def exp(self, power):
        # Simplified exponential implementation for demo
        if power <= -41446531673892821376:
            return 0
        if power >= 135305999368893231589:
            return self.MAX_EXP
        return min(np.exp(power / 1e18) * 1e18, self.MAX_EXP)

    def calculate_rate(self, **kwargs):
        """
        Implementation of the contract's calculate_rate logic
        """
        price = kwargs.get('price', 10**18)  # default to 1.0
        sigma = kwargs.get('sigma', 2 * 10**16)
        rate0 = kwargs.get('rate0', 0)
        target_debt_fraction = kwargs.get('target_debt_fraction', 10**17)
        debt_for = kwargs.get('debt_for', 0)
        total_debt = kwargs.get('total_debt', 0)
        pk_debt = kwargs.get('pk_debt', 0)
        ceiling = kwargs.get('ceiling', 0)

        # Core rate calculation
        power = (10**18 - price) * 10**18 // sigma

        if pk_debt > 0 and total_debt > 0:
            power -= (pk_debt * 10**18 // total_debt * 10**18 // target_debt_fraction)

        rate = rate0 * min(self.exp(power), self.MAX_EXP) // 10**18

        # Ceiling adjustment
        if ceiling > 0 and debt_for > 0:
            f = min(debt_for * 10**18 // ceiling, 10**18 - self.TARGET_REMAINDER // 1000)
            rate = min(
                rate * ((10**18 - self.TARGET_REMAINDER) + 
                       self.TARGET_REMAINDER * 10**18 // (10**18 - f)) // 10**18,
                self.MAX_RATE
            )

        return rate