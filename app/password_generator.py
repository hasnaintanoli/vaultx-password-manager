"""
VaultX Secure Password Generator & Evaluator.
Uses Python's cryptographically secure `secrets` module to generate strong passwords.
"""

import math
import secrets
import string
from typing import Dict, Any


AMBIGUOUS_CHARS = set("l1IO0oQS5Z2")

UPPERCASE_SET = string.ascii_uppercase
LOWERCASE_SET = string.ascii_lowercase
DIGITS_SET = string.digits
SYMBOLS_SET = "!@#$%^&*()_+-=[]{}|;:,.<>?"


def generate_password(
    length: int = 20,
    use_uppercase: bool = True,
    use_lowercase: bool = True,
    use_numbers: bool = True,
    use_symbols: bool = True,
    exclude_ambiguous: bool = False
) -> str:
    """
    Generates a cryptographically secure random password using Python's `secrets` module.
    
    Args:
        length: Password length (must be between 4 and 128).
        use_uppercase: Include A-Z.
        use_lowercase: Include a-z.
        use_numbers: Include 0-9.
        use_symbols: Include special characters.
        exclude_ambiguous: If True, filters out ambiguous visual characters (e.g. 1, l, I, 0, O).
        
    Returns:
        Generated password string.
        
    Raises:
        ValueError: If no character sets are selected or length is less than active character pools.
    """
    pools = []
    
    if use_uppercase:
        pool = UPPERCASE_SET
        if exclude_ambiguous:
            pool = "".join(c for c in pool if c not in AMBIGUOUS_CHARS)
        if pool:
            pools.append(pool)
            
    if use_lowercase:
        pool = LOWERCASE_SET
        if exclude_ambiguous:
            pool = "".join(c for c in pool if c not in AMBIGUOUS_CHARS)
        if pool:
            pools.append(pool)
            
    if use_numbers:
        pool = DIGITS_SET
        if exclude_ambiguous:
            pool = "".join(c for c in pool if c not in AMBIGUOUS_CHARS)
        if pool:
            pools.append(pool)
            
    if use_symbols:
        pool = SYMBOLS_SET
        if exclude_ambiguous:
            pool = "".join(c for c in pool if c not in AMBIGUOUS_CHARS)
        if pool:
            pools.append(pool)

    if not pools:
        raise ValueError("At least one character type must be selected.")

    if length < len(pools):
        length = len(pools)

    # Ensure at least one character from each selected pool is present
    password_chars = [secrets.choice(pool) for pool in pools]

    # Combine all character pools for remaining positions
    full_charset = "".join(pools)
    remaining_length = length - len(password_chars)
    
    for _ in range(remaining_length):
        password_chars.append(secrets.choice(full_charset))

    # Secure shuffle using Fisher-Yates algorithm driven by secrets.randbelow
    for i in range(len(password_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

    return "".join(password_chars)


def evaluate_password_strength(password: str) -> Dict[str, Any]:
    """
    Evaluates password strength and calculates entropy in bits.
    
    Returns:
        Dict containing:
        - score: 0 to 100
        - entropy: calculated entropy in bits
        - label: "Weak", "Medium", "Strong", "Very Strong"
        - color: Hex color code matching UI design system
    """
    if not password:
        return {
            "score": 0,
            "entropy": 0.0,
            "label": "Very Weak",
            "color": "#EF4444"
        }

    # Determine pool size R based on character types present
    has_upper = any(c in UPPERCASE_SET for c in password)
    has_lower = any(c in LOWERCASE_SET for c in password)
    has_digit = any(c in DIGITS_SET for c in password)
    has_symbol = any(c in SYMBOLS_SET or (c not in UPPERCASE_SET and c not in LOWERCASE_SET and c not in DIGITS_SET) for c in password)

    charset_size = 0
    if has_upper:
        charset_size += 26
    if has_lower:
        charset_size += 26
    if has_digit:
        charset_size += 10
    if has_symbol:
        charset_size += 32

    if charset_size == 0:
        charset_size = 26

    # Entropy E = L * log2(R)
    entropy = len(password) * math.log2(charset_size)

    # Score calculation (0 - 100)
    score = min(100, int((entropy / 80.0) * 100))

    if entropy < 36:
        label = "Weak"
        color = "#EF4444"  # Danger Red
    elif entropy < 60:
        label = "Medium"
        color = "#F59E0B"  # Warning Amber
    elif entropy < 80:
        label = "Strong"
        color = "#10B981"  # Success Green
    else:
        label = "Very Strong"
        color = "#059669"  # Emerald Green

    return {
        "score": score,
        "entropy": round(entropy, 1),
        "label": label,
        "color": color
    }
