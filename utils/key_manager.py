"""
Production Key Management System
Handles secure key generation, storage, and retrieval
"""

import os
import secrets
import base64
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import hashlib


class KeyManager:
    """Secure key management with metadata"""
    
    KEYS_DIR = Path("keys")
    KEY_SIZE = 32  # 256 bits
    
    def __init__(self):
        self.KEYS_DIR.mkdir(exist_ok=True)
    
    @staticmethod
    def generate_key() -> bytes:
        """Generate cryptographically secure 256-bit key"""
        return secrets.token_bytes(KeyManager.KEY_SIZE)
    
    @staticmethod
    def key_to_string(key: bytes) -> str:
        """Convert binary key to base64 string"""
        return base64.b64encode(key).decode('utf-8')
    
    @staticmethod
    def string_to_key(key_string: str) -> bytes:
        """Convert base64 string to binary key"""
        try:
            key = base64.b64decode(key_string)
            if len(key) != KeyManager.KEY_SIZE:
                raise ValueError(f"Invalid key size: {len(key)} bytes")
            return key
        except Exception as e:
            raise ValueError(f"Invalid key format: {str(e)}")
    
    @staticmethod
    def get_key_fingerprint(key: bytes) -> str:
        """Generate SHA-256 fingerprint of key"""
        return hashlib.sha256(key).hexdigest()[:16].upper()
    
    def save_key(self, key: bytes, name: str, description: str = "") -> Path:
        """Save key with metadata"""
        fingerprint = self.get_key_fingerprint(key)
        
        key_data = {
            'name': name,
            'description': description,
            'key': self.key_to_string(key),
            'fingerprint': fingerprint,
            'algorithm': 'AES-256-GCM',
            'size_bits': self.KEY_SIZE * 8,
            'created': datetime.utcnow().isoformat(),
            'version': '2.0'
        }
        
        # Sanitize filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_name}_{fingerprint}.key.json"
        filepath = self.KEYS_DIR / filename
        
        with open(filepath, 'w') as f:
            json.dump(key_data, f, indent=2)
        
        return filepath
    
    def load_key(self, identifier: str) -> Tuple[bytes, Dict]:
        """
        Load key by name, filename, or fingerprint
        
        Returns:
            (key_bytes, metadata)
        """
        # Try exact filename
        filepath = self.KEYS_DIR / identifier
        if not filepath.exists():
            filepath = self.KEYS_DIR / f"{identifier}.key.json"
        
        # Search by name or fingerprint
        if not filepath.exists():
            for keyfile in self.KEYS_DIR.glob("*.key.json"):
                with open(keyfile, 'r') as f:
                    data = json.load(f)
                    if data.get('name') == identifier or data.get('fingerprint') == identifier:
                        filepath = keyfile
                        break
        
        if not filepath.exists():
            raise FileNotFoundError(f"Key not found: {identifier}")
        
        with open(filepath, 'r') as f:
            key_data = json.load(f)
        
        key = self.string_to_key(key_data['key'])
        return key, key_data
    
    def list_keys(self) -> List[Dict]:
        """List all saved keys with metadata"""
        keys = []
        for keyfile in sorted(self.KEYS_DIR.glob("*.key.json")):
            try:
                with open(keyfile, 'r') as f:
                    data = json.load(f)
                    keys.append({
                        'file': keyfile.name,
                        'name': data.get('name', 'Unknown'),
                        'description': data.get('description', ''),
                        'fingerprint': data.get('fingerprint', ''),
                        'created': data.get('created', ''),
                        'algorithm': data.get('algorithm', 'Unknown')
                    })
            except Exception:
                continue
        return keys
    
    def delete_key(self, identifier: str) -> bool:
        """Delete key by name, filename, or fingerprint"""
        try:
            key, metadata = self.load_key(identifier)
            
            # Find and delete file
            for keyfile in self.KEYS_DIR.glob("*.key.json"):
                if keyfile.name == identifier or metadata['fingerprint'] in keyfile.name:
                    keyfile.unlink()
                    return True
            
            return False
        except Exception:
            return False
    
    def export_key(self, identifier: str, export_path: str):
        """Export key to file"""
        key, metadata = self.load_key(identifier)
        
        export_data = {
            'key': self.key_to_string(key),
            'metadata': metadata
        }
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def import_key(self, import_path: str) -> str:
        """Import key from file"""
        with open(import_path, 'r') as f:
            import_data = json.load(f)
        
        key = self.string_to_key(import_data['key'])
        metadata = import_data.get('metadata', {})
        
        name = metadata.get('name', 'Imported Key')
        description = metadata.get('description', f"Imported on {datetime.now().strftime('%Y-%m-%d')}")
        
        filepath = self.save_key(key, name, description)
        return name
