"""
Production-Grade AES-GCM Encryption Engine
Algorithm: AES-256-GCM with AEAD
Security: Military-grade authenticated encryption
"""

import os
import base64
import json
import hashlib
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag
from typing import Tuple, Dict, Optional


class CryptoEngine:
    """Production-grade AES-GCM encryption engine"""
    
    VERSION = "v2.0"
    KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits (optimal for GCM)
    TAG_SIZE = 16  # 128 bits
    PBKDF2_ITERATIONS = 600_000  # OWASP 2023 standard
    
    def __init__(self, key: bytes):
        """Initialize with 256-bit key"""
        if len(key) != self.KEY_SIZE:
            raise ValueError(f"Key must be {self.KEY_SIZE} bytes")
        self.aesgcm = AESGCM(key)
        self.key_hash = hashlib.sha256(key).hexdigest()[:16]
    
    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Derive 256-bit key from password using PBKDF2-SHA256
        
        Args:
            password: User password
            salt: 16-byte salt (generated if None)
        
        Returns:
            (key, salt) tuple
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=CryptoEngine.KEY_SIZE,
            salt=salt,
            iterations=CryptoEngine.PBKDF2_ITERATIONS
        )
        key = kdf.derive(password.encode('utf-8'))
        return key, salt
    
    def encrypt(self, plaintext: bytes, metadata: Optional[Dict] = None) -> Dict[str, str]:
        """
        Encrypt data with AES-GCM
        
        Returns:
            Dictionary with version, timestamp, nonce, ciphertext, tag
        """
        # Generate random nonce
        nonce = os.urandom(self.NONCE_SIZE)
        
        # Prepare metadata
        meta = metadata or {}
        meta.update({
            'version': self.VERSION,
            'timestamp': datetime.utcnow().isoformat(),
            'key_hash': self.key_hash,
            'size': len(plaintext)
        })
        
        # Authenticated data (not encrypted, but verified)
        aad = json.dumps(meta, sort_keys=True).encode('utf-8')
        
        # Encrypt
        ciphertext = self.aesgcm.encrypt(nonce, plaintext, aad)
        
        # Split ciphertext and tag
        ct = ciphertext[:-self.TAG_SIZE]
        tag = ciphertext[-self.TAG_SIZE:]
        
        return {
            'version': self.VERSION,
            'metadata': base64.b64encode(aad).decode('utf-8'),
            'nonce': base64.b64encode(nonce).decode('utf-8'),
            'ciphertext': base64.b64encode(ct).decode('utf-8'),
            'tag': base64.b64encode(tag).decode('utf-8')
        }
    
    def decrypt(self, bundle: Dict[str, str]) -> Tuple[bytes, Dict]:
        """
        Decrypt and verify AES-GCM encrypted data
        
        Returns:
            (plaintext, metadata) tuple
        
        Raises:
            InvalidTag: If authentication fails
        """
        # Decode components
        nonce = base64.b64decode(bundle['nonce'])
        ct = base64.b64decode(bundle['ciphertext'])
        tag = base64.b64decode(bundle['tag'])
        aad = base64.b64decode(bundle['metadata'])
        
        # Reconstruct full ciphertext
        full_ct = ct + tag
        
        try:
            # Decrypt and verify
            plaintext = self.aesgcm.decrypt(nonce, full_ct, aad)
            
            # Parse metadata
            metadata = json.loads(aad.decode('utf-8'))
            
            # Verify key
            if metadata.get('key_hash') != self.key_hash:
                raise ValueError("Key mismatch detected")
            
            return plaintext, metadata
        
        except InvalidTag:
            raise ValueError("Authentication failed: Invalid key or tampered data")
    
    @staticmethod
    def create_bundle_string(bundle: Dict[str, str]) -> str:
        """Convert bundle to base64-encoded JSON string"""
        json_str = json.dumps(bundle, separators=(',', ':'))
        return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    @staticmethod
    def parse_bundle_string(bundle_str: str) -> Dict[str, str]:
        """Parse base64-encoded JSON string to bundle"""
        json_str = base64.b64decode(bundle_str).decode('utf-8')
        return json.loads(json_str)


def quick_encrypt(key: bytes, data: bytes, metadata: Optional[Dict] = None) -> str:
    """Quick encryption returning bundle string"""
    crypto = CryptoEngine(key)
    bundle = crypto.encrypt(data, metadata)
    return crypto.create_bundle_string(bundle)


def quick_decrypt(key: bytes, bundle_str: str) -> Tuple[bytes, Dict]:
    """Quick decryption from bundle string"""
    crypto = CryptoEngine(key)
    bundle = crypto.parse_bundle_string(bundle_str)
    return crypto.decrypt(bundle)
