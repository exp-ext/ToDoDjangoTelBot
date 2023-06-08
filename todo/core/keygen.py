import secrets
import string


def get_key(length: int) -> str:
    """
    This is a function that generates a random key of a specified length.
    The key is made up of a combination of digits and letters
    (both uppercase and lowercase). The function uses the secrets
    module to ensure that the generated key is cryptographically secure.

    length (:obj:`int`) - key length
    """
    character_set = string.digits + string.ascii_letters
    return ''.join(secrets.choice(character_set) for _ in range(length))
