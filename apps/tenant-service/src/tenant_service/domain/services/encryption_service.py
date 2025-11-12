"""Encryption service for sensitive credentials storage."""

import base64
import hashlib
import json
import logging
from typing import Optional

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Encrypts and decrypts sensitive data like storage credentials.

    Uses Fernet (symmetric encryption) for credential protection.
    Each tenant can have their own encryption key for additional isolation.
    """

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption service.

        Args:
            master_key: Master encryption key. If not provided, uses environment.
        """
        self.master_key = master_key or self._get_default_key()
        self.cipher = Fernet(self.master_key)
        logger.info("Encryption service initialized")

    @staticmethod
    def _get_default_key() -> bytes:
        """
        Get or generate default encryption key.

        In production, this should come from a secure key management service
        like AWS KMS, Azure Key Vault, or HashiCorp Vault.

        Returns:
            Fernet encryption key
        """
        # Default key for development - MUST be changed in production
        default_key = "your-master-encryption-key-change-in-production"

        # Ensure key is proper Fernet format
        hashed = hashlib.sha256(default_key.encode()).digest()
        return base64.urlsafe_b64encode(hashed)

    def encrypt_credentials(self, credentials: dict, tenant_id: Optional[str] = None) -> str:
        """
        Encrypt credentials dictionary to string.

        Args:
            credentials: Dictionary of credentials
            tenant_id: Optional tenant ID for additional isolation

        Returns:
            Encrypted credentials string (base64)
        """
        try:
            # Serialize to JSON
            json_str = json.dumps(credentials)

            # Add tenant ID to encrypted data for additional validation
            if tenant_id:
                json_str = f"{tenant_id}||{json_str}"

            # Encrypt
            encrypted = self.cipher.encrypt(json_str.encode())

            # Return as base64 string for storage in database
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Credential encryption failed: {e}")
            raise

    def decrypt_credentials(self, encrypted_str: str, tenant_id: Optional[str] = None) -> dict:
        """
        Decrypt credentials string back to dictionary.

        Args:
            encrypted_str: Encrypted credentials string
            tenant_id: Optional tenant ID for validation

        Returns:
            Decrypted credentials dictionary
        """
        try:
            # Decrypt
            decrypted = self.cipher.decrypt(encrypted_str.encode())
            decrypted_str = decrypted.decode()

            # Verify tenant ID if provided
            if tenant_id:
                stored_tenant_id, json_str = decrypted_str.split("||", 1)
                if stored_tenant_id != tenant_id:
                    logger.warning(
                        f"Tenant ID mismatch in decrypted credentials: expected {tenant_id}, got {stored_tenant_id}"
                    )
                    raise ValueError("Tenant ID mismatch in encrypted data")
            else:
                json_str = decrypted_str

            # Deserialize
            credentials = json.loads(json_str)

            logger.debug("Credentials decrypted successfully")
            return credentials
        except Exception as e:
            logger.error(f"Credential decryption failed: {e}")
            raise

    def rotate_key(self, new_key: str) -> None:
        """
        Rotate encryption key (for future credentials).

        Note: This does NOT re-encrypt existing credentials.
        In production, would need migration process.

        Args:
            new_key: New encryption key
        """
        try:
            hashed = hashlib.sha256(new_key.encode()).digest()
            self.master_key = base64.urlsafe_b64encode(hashed)
            self.cipher = Fernet(self.master_key)
            logger.info("Encryption key rotated")
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            raise
