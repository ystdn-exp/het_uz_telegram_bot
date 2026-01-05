from cryptography.fernet import Fernet
from passlib.context import CryptContext

from src.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Hashes a password using bcrypt.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if the plain password matches the hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password, scheme="bcrypt")


class PasswordEncoder:
    """
    Encodes a password using AES-256 Fernet.
    """

    def __init__(self, secret_key: str):
        self.cipher_suit = Fernet(b"oLQN4s7mkO71Ws9MwLtok_jNk8zX-30y43ET1w_zeSw=")

    def get_password_encoding(self, password: str) -> str:
        """
        Encodes a password using AES-256 Fernet.
        """
        return self.cipher_suit.encrypt(password.encode()).decode()

    def verify_password_encoding(
        self, plain_password: str, encoded_password: str
    ) -> bool:
        """
        Checks if the plain password matches the encoded password.
        """
        return (
            self.cipher_suit.decrypt(encoded_password.encode()).decode() == plain_password
        )


password_encoder = PasswordEncoder(secret_key=settings.SECRET_KEY)
