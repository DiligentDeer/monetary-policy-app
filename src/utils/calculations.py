
def to_wei(val, decimals=18):
    """Convert human readable number to wei (with decimals)"""
    return int(val * 10**decimals)

def from_wei(val, decimals=18):
    """Convert wei to human readable number"""
    return val / 10**decimals

def calculate_annual_rate(rate):
    """Calculate annual rate from the contract rate"""
    seconds_in_year = 365 * 24 * 60 * 60
    return ((1 + rate/1e18) ** seconds_in_year) - 1