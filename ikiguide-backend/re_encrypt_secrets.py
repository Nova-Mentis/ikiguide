import os
import base64
import getpass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def generate_key(password: str, salt: bytes = None) -> bytes:
    """
    Generate a consistent encryption key
    """
    if salt is None:
        salt = b'ikiguide_fixed_salt_2024'
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_secret(secret: str, key: bytes) -> str:
    """
    Encrypt a secret using Fernet symmetric encryption
    """
    f = Fernet(key)
    return f.encrypt(secret.encode()).decode()

def main():
    # Prompt for encryption password
    password = getpass.getpass("Enter encryption password: ")
    
    # Generate key from password
    key = generate_key(password)
    
    # Predefined secrets to collect
    secret_prompts = [
        ('ENCRYPTED_OPENAI_API_KEY', 'OpenAI API Key'),
        ('ENCRYPTED_AZURE_TENANT_ID', 'Azure Tenant ID'),
        ('ENCRYPTED_AZURE_CLIENT_ID', 'Azure Client ID'),
        ('ENCRYPTED_AZURE_CLIENT_SECRET', 'Azure Client Secret'),
    ]
    
    # Secrets to encrypt
    secrets = {}
    
    # Collect secrets
    print("\nPlease enter the following secrets:")
    for env_var, prompt in secret_prompts:
        secret = getpass.getpass(f"Enter {prompt}: ")
        if secret:  # Only add non-empty secrets
            secrets[env_var] = secret
    
    # Encrypt and print secrets
    if secrets:
        print("\nEncrypted Secrets:")
        for env_var, secret in secrets.items():
            encrypted = encrypt_secret(secret, key)
            print(f"{env_var}={encrypted}")
    else:
        print("No secrets to encrypt.")

if __name__ == '__main__':
    main()
