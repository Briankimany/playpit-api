import pickle
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from config.config import ConfigClass
from pathlib import Path
from utils.logger import LOG

config = ConfigClass()

class SecureUtils:
    """
    Utility class for handling secure password hashing and encryption.
    Supports dev_mode for reversible encryption in development.
    """

    def __init__(self, secret_key: bytes = None, dev_mode: bool = False):
        self.dev_mode = dev_mode
        if not secret_key:
            secret_key = Fernet.generate_key()
        self.secret_key = secret_key
        self.fernet = Fernet(secret_key)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # ----------------------
    # 🔐 Hashing Methods
    # ----------------------

    def hash_password(self, password: str) -> str:
        """Hash a plain password using bcrypt."""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a bcrypt hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    # ----------------------
    # 🔏 Encryption Methods
    # ----------------------

    def encrypt(self, data: str) -> str:
        """Encrypt plaintext string and return base64-encoded string."""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        """Decrypt a base64-encoded encrypted string back to plaintext."""

        try:
            decryped_data =self.fernet.decrypt(token.encode()).decode()
            return decryped_data
        except Exception as e:
            LOG.api_logger.error(f"Error decrypting token: {e}")
            return None
     

    def get_fernet_key(self) -> str:
        """Return the Fernet secret key as a base64-encoded string."""
        return self.secret_key.decode()

    # ----------------------
    # 🔁 Smart Mode Methods
    # ----------------------

    def secure_store(self, value: str) -> str:
        """Store a value securely (encrypt in dev mode, hash in prod)."""
        return self.encrypt(value) if self.dev_mode else self.hash_password(value)

    def secure_check(self, raw: str, stored: str) -> bool:
        """Check a value against stored token/hash, based on mode."""

        if self.dev_mode:
            return raw == self.decrypt(stored)
        
        return self.verify_password(raw, stored)
    
    def load_display_value(self, value: str) -> str:
        """Load and display the value based on mode."""
        if self.dev_mode:
            return self.decrypt(value)
        return value

    # ----------------------
    # 💾 Persistence Methods
    # ----------------------

    def save_to_file(self, filepath: str):
        """Save the SecureUtils instance to a pickle file."""
        filepath = Path(filepath)
        if filepath.exists():
           return
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load_from_file(filepath: str) -> 'SecureUtils':

        """Load a SecureUtils instance from a pickle file."""
        with open(filepath, 'rb') as f:
            return pickle.load(f)
        
    
    def __getstate__(self):
        """Customize what gets pickled (exclude non-picklable objects)."""
        state = self.__dict__.copy()
        # Remove the non-picklable object
        if 'pwd_context' in state:
            del state['pwd_context']
        return state

    def __setstate__(self, state):
        """Restore instance after unpickling (rebuild pwd_context)."""
        self.__dict__.update(state)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_secure_utils():
    secure_mode = input("Enter secure mode (dev/prod): ").strip().lower()
    if secure_mode == "dev":
        dev_mode = True
    elif secure_mode == "prod":
        dev_mode = False
    else:
        raise ValueError("Invalid mode. Use 'dev' or 'prod'.")
    secure_utils = SecureUtils(dev_mode=dev_mode)
    print(f"saving to fiel: {config.SECURE_UTILS_LOCATION}")
    secure_utils.save_to_file(config.SECURE_UTILS_LOCATION)

def load_secure_utils():
    try:
        if not Path(config.SECURE_UTILS_LOCATION).exists():
            print("Secure utils file not found. Generating a new one.")
            generate_secure_utils()
            print("Secure utils file generated successfully.")
        secure_utils = SecureUtils.load_from_file(config.SECURE_UTILS_LOCATION)
        return secure_utils
    except FileNotFoundError:
        print("Secure utils file not found. Please generate it first.")
        return None
    except Exception as e:
        print(f"An error occurred while loading secure utils: {e}")
        return None