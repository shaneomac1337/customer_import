#!/usr/bin/env python3
"""
Authentication Manager for Bulk Customer Import
Handles automatic token refresh and authentication
"""

import requests
import json
import time
import base64
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

class AuthenticationManager:
    """Manages OAuth2 authentication with automatic token refresh"""
    
    def __init__(self,
                 username: str = "coop_sweden",
                 password: str = "coopsverige123",
                 gk_passport: str = "1.1:CiMg46zV+88yKOOMxZPwMjIDMDAxOg5idXNpbmVzc1VuaXRJZBIKCAISBnVzZXJJZBoSCAIaCGNsaWVudElkIgR3c0lkIhoaGGI6Y3VzdC5jdXN0b21lci5pbXBvcnRlcg==",
                 auth_url: str = "https://prod.cse.cloud4retail.co/auth-service/tenants/001/oauth/token",
                 basic_auth: str = "bGF1bmNocGFkOk5iV295MWxES3Y4N1JBQXdOUHJF"):
        """
        Initialize the authentication manager
        
        Args:
            username: OAuth username
            password: OAuth password  
            gk_passport: GK-Passport header value
            auth_url: OAuth token endpoint URL
            basic_auth: Base64 encoded basic auth credentials
        """
        self.username = username
        self.password = password
        self.gk_passport = gk_passport
        self.auth_url = auth_url
        self.basic_auth = basic_auth
        
        # Token management
        self.current_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.token_lock = threading.Lock()
        
        # Buffer time before token expiry (refresh 50 minutes early = every 10 minutes)
        self.refresh_buffer_seconds = 3000
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def get_valid_token(self) -> str:
        """
        Get a valid authentication token, refreshing if necessary
        
        Returns:
            Valid authentication token
            
        Raises:
            Exception: If token refresh fails
        """
        with self.token_lock:
            # Check if we need a new token
            if self._needs_refresh():
                self._refresh_token()
            
            if not self.current_token:
                raise Exception("Failed to obtain authentication token")
                
            return self.current_token
    
    def _needs_refresh(self) -> bool:
        """Check if token needs to be refreshed"""
        if not self.current_token or not self.token_expires_at:
            return True
            
        # Refresh if token expires within buffer time
        buffer_time = datetime.now() + timedelta(seconds=self.refresh_buffer_seconds)
        return buffer_time >= self.token_expires_at
    
    def _refresh_token(self) -> None:
        """Refresh the authentication token"""
        try:
            self.logger.info("🔄 Refreshing authentication token...")
            
            headers = {
                'Authorization': f'Basic {self.basic_auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'username': self.username,
                'password': self.password,
                'grant_type': 'password'
            }
            
            response = requests.post(
                self.auth_url,
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                self.current_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
                
                # Calculate expiration time
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                self.logger.info(f"✅ Token refreshed successfully. Expires at: {self.token_expires_at}")
                
            else:
                error_msg = f"Token refresh failed: HTTP {response.status_code} - {response.text}"
                self.logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Token refresh network error: {e}"
            self.logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Token refresh error: {e}"
            self.logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get complete authentication headers for API requests
        
        Returns:
            Dictionary with Authorization and GK-Passport headers
        """
        token = self.get_valid_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        if self.gk_passport:
            headers['GK-Passport'] = self.gk_passport
            
        return headers
    
    def test_authentication(self) -> Dict[str, Any]:
        """
        Test authentication by getting a token
        
        Returns:
            Dictionary with test results
        """
        try:
            start_time = datetime.now()
            token = self.get_valid_token()
            end_time = datetime.now()
            
            return {
                'success': True,
                'token_preview': f"{token[:20]}..." if token else None,
                'expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
                'response_time_ms': (end_time - start_time).total_seconds() * 1000,
                'message': 'Authentication successful'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Authentication failed'
            }
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get information about the current token
        
        Returns:
            Dictionary with token information
        """
        with self.token_lock:
            if not self.current_token:
                return {
                    'has_token': False,
                    'message': 'No token available'
                }
            
            time_until_expiry = None
            needs_refresh = self._needs_refresh()
            
            if self.token_expires_at:
                time_until_expiry = (self.token_expires_at - datetime.now()).total_seconds()
            
            return {
                'has_token': True,
                'token_preview': f"{self.current_token[:20]}...",
                'expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
                'time_until_expiry_seconds': time_until_expiry,
                'needs_refresh': needs_refresh,
                'refresh_buffer_seconds': self.refresh_buffer_seconds
            }
    
    def force_refresh(self) -> None:
        """Force an immediate token refresh"""
        with self.token_lock:
            self.current_token = None
            self.token_expires_at = None
            self._refresh_token()

# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Test authentication manager (GK-Passport now hardcoded in constructor)
    auth_manager = AuthenticationManager()
    
    print("Testing Authentication Manager...")
    print("=" * 50)
    
    # Test authentication
    result = auth_manager.test_authentication()
    print(f"Authentication test: {result}")
    
    # Get token info
    info = auth_manager.get_token_info()
    print(f"Token info: {info}")
    
    # Test getting headers
    try:
        headers = auth_manager.get_auth_headers()
        print(f"Auth headers: {headers}")
    except Exception as e:
        print(f"Error getting headers: {e}")
