"""
Utility functions for encoding harmful requests for obfuscation attacks.
"""

import base64
import codecs


def encode_base64(text: str) -> str:
    """Encode text to base64."""
    return base64.b64encode(text.encode()).decode()


def encode_hex(text: str) -> str:
    """Encode text to hexadecimal."""
    return text.encode().hex()


def encode_character_spacing(text: str) -> str:
    """Add spaces between each character."""
    return ' '.join(text)


def encode_homoglyphs(text: str) -> str:
    """
    Replace characters with similar-looking unicode characters.
    Basic implementation - can be expanded.
    """
    replacements = {
        'a': 'а',  # Cyrillic a
        'e': 'е',  # Cyrillic e
        'o': 'о',  # Cyrillic o
        'p': 'р',  # Cyrillic r (looks like p)
        'c': 'с',  # Cyrillic s (looks like c)
        'x': 'х',  # Cyrillic h (looks like x)
        'i': 'і',  # Cyrillic i
        'A': 'А',  # Cyrillic A
        'B': 'В',  # Cyrillic V (looks like B)
        'C': 'С',  # Cyrillic S (looks like C)
        'E': 'Е',  # Cyrillic E
        'H': 'Н',  # Cyrillic N (looks like H)
        'K': 'К',  # Cyrillic K
        'M': 'М',  # Cyrillic M
        'O': 'О',  # Cyrillic O
        'P': 'Р',  # Cyrillic R (looks like P)
        'T': 'Т',  # Cyrillic T
        'X': 'Х',  # Cyrillic H (looks like X)
    }

    result = []
    for char in text:
        result.append(replacements.get(char, char))
    return ''.join(result)


def translate_spanish(text: str) -> str:
    """
    Translate text to Spanish using Google Translate.
    """
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, dest='es')
        return result.text
    except ImportError:
        # Fallback if googletrans is not installed
        return f"[Spanish translation of: {text}]"
    except Exception as e:
        # Fallback if translation fails
        print(f"Translation error: {e}")
        return text


def translate_russian(text: str) -> str:
    """
    Translate text to Russian using Google Translate.
    """
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, dest='ru')
        return result.text
    except ImportError:
        # Fallback if googletrans is not installed
        return f"[Russian translation of: {text}]"
    except Exception as e:
        # Fallback if translation fails
        print(f"Translation error: {e}")
        return text


# Encoding dispatcher
ENCODERS = {
    "base64": encode_base64,
    "hex": encode_hex,
    "character_spacing": encode_character_spacing,
    "homoglyphs": encode_homoglyphs,
    "translate_spanish": translate_spanish,
    "translate_russian": translate_russian,
}


def encode_request(text: str, encoding_type: str) -> str:
    """
    Encode a harmful request using the specified encoding type.

    Args:
        text: The harmful request text
        encoding_type: Type of encoding (e.g., "base64", "hex", "character_spacing")

    """
    encoder = ENCODERS.get(encoding_type)
    if encoder is None:
        raise ValueError(f"Unknown encoding type: {encoding_type}")

    return encoder(text)
