import os
from typing import Optional, Dict

class TokenManager:
    """Secure token management class"""
    
    _token: Optional[str] = None
    
    @classmethod
    def get_token(cls) -> str:
        """Get GitHub token securely"""
        if cls._token is None:
            cls._token = cls._load_token()
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
        """Basic validation of token format"""
        return (
            isinstance(token, str) 
            and len(token) >= 40
            and (token.startswith(('ghp_', 'github_pat_')) 
                 or all(c in 'abcdef0123456789' for c in token))
        )
    
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
