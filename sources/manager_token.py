import os
from typing import Optional, Dict
import hashlib
import math

class TokenManager:
    """Enhanced secure token management"""
    
    _token: Optional[str] = None
    _token_hash: Optional[str] = None  # Store hash instead of actual token
    
    @classmethod
    def get_token(cls) -> str:
        if cls._token is None:
            cls._token = cls._load_token()
            # Store hash for validation
            cls._token_hash = hashlib.sha256(cls._token.encode()).hexdigest()
        else:
            # Validate token hasn't been tampered with
            current_hash = hashlib.sha256(cls._token.encode()).hexdigest()
            if current_hash != cls._token_hash:
                raise SecurityException("Token validation failed - possible tampering detected")
        return cls._token
    
    @classmethod
    def _load_token(cls) -> str:
        """Load token from environment or prompt securely"""
        # Try loading from environment
        token = os.getenv('INPUT_GH_TOKEN')
        
        if not token:
            try:
                # Try loading from .env file if python-dotenv is available
                from dotenv import load_dotenv
                load_dotenv()
                token = os.getenv('INPUT_GH_TOKEN')
            except ImportError:
                pass
        
        if not token:
            # If still no token, prompt user securely
            try:
                import getpass
                print("\n⚠️  GitHub Token Required")
                print("Please enter your GitHub Personal Access Token.")
                print("Note: Token input will be hidden for security.")
                token = getpass.getpass("Token: ")
            except Exception as e:
                raise ValueError("Failed to get GitHub token: Interactive input failed") from e
                
        if not token:
            raise ValueError("GitHub token is required. Please set INPUT_GH_TOKEN environment variable or create a .env file")
            
        # Validate token format
        if not cls._validate_token(token):
            raise ValueError("Invalid GitHub token format. Token should start with 'ghp_' or 'github_pat_' and be at least 40 characters long")
            
        return token
    
    @staticmethod
    def _validate_token(token: str) -> bool:
        """Enhanced token validation"""
        if not isinstance(token, str) or len(token) < 40:
            return False
            
        # Check for common token prefixes
        valid_prefixes = ('ghp_', 'github_pat_')
        if not any(token.startswith(prefix) for prefix in valid_prefixes):
            # Fall back to checking if it's a classic token format
            if not all(c in 'abcdef0123456789' for c in token):
                return False
                
        # Basic entropy check
        char_frequency = {}
        for char in token:
            char_frequency[char] = char_frequency.get(char, 0) + 1
        entropy = sum(-freq/len(token) * math.log2(freq/len(token)) 
                     for freq in char_frequency.values())
        if entropy < 3.0:  # Arbitrary threshold, adjust as needed
            return False
            
        return True
    
    @staticmethod
    def mask_token(text: str, token: Optional[str] = None) -> str:
        """Mask token in text to prevent accidental exposure"""
        if token is None:
            token = TokenManager._token
            
        if token and token in text:
            visible_chars = 4 if len(token) > 4 else 0
            return text.replace(token, f"{token[:visible_chars]}{'*' * (len(token) - visible_chars)}")
        return text
    
    @classmethod
    def get_credentials_helper(cls) -> Dict[str, str]:
        """Get Git credentials helper configuration"""
        token = cls.get_token()
        return {
            'GIT_ASKPASS': 'echo',
            'GIT_USERNAME': 'oauth2',
            'GIT_PASSWORD': token
        }
