import random
import string

def generate_B2c_account_reference():
    # Generate a 6-digit number where all digits are between 0 and 13
    account_reference = ''.join(str(random.randint(0, 13)) for _ in range(6))
    
    return account_reference