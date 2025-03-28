from abc import ABC, abstractmethod

class BaseMonetaryPolicy(ABC):
    """Abstract base class for monetary policies"""
    
    @abstractmethod
    def calculate_rate(self, **kwargs):
        """Calculate rate based on policy-specific parameters"""
        pass

    @property
    @abstractmethod
    def required_parameters(self):
        """Return list of required parameters for this policy"""
        pass

    @property
    @abstractmethod
    def policy_name(self):
        """Return the name of the policy"""
        pass