"""
Authentication module for BUAA SSO system.
Handles login and session management.
"""

import requests
from bs4 import BeautifulSoup
import config
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('auth')

class SSOAuth:
    def __init__(self, username=None, password=None):
        """Initialize the SSO authentication handler."""
        self.username = username or config.USERNAME
        self.password = password or config.PASSWORD
        self.session = requests.Session()
        self.session_id = None
        self.user_info = None

    def login(self):
        """
        Log in to the BUAA SSO system and return the session.
        Returns:
            bool: True if login successful, False otherwise
        """
        if not self.username or not self.password:
            logger.error("Username or password not provided")
            return False

        try:
            # Step 1: Get the login page to obtain the execution parameter
            logger.info("Fetching SSO login page...")
            response = self.session.get(
                config.SSO_LOGIN_URL,
                params={"service": config.ICLASS_SERVICE_URL},
                allow_redirects=True
            )

            # Parse the login page to get the execution parameter
            soup = BeautifulSoup(response.text, "html.parser")
            execution = soup.find('input', {'name': 'execution'}).get('value')

            if not execution:
                logger.error("Could not find execution parameter")
                return False

            logger.info(f"Got execution parameter: {execution[:20]}...")

            # Step 2: Submit login credentials
            logger.info("Submitting login credentials...")
            login_data = {
                "username": self.username,
                "password": self.password,
                "submit": "登录",
                "type": "username_password",
                "execution": execution,
                "_eventId": "submit"
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
                "Referer": config.SSO_LOGIN_URL,
                "Content-Type": "application/x-www-form-urlencoded"
            }

            response = self.session.post(
                config.SSO_LOGIN_URL,
                headers=headers,
                data=login_data,
                allow_redirects=True
            )

            # Step 3: Handle the redirects and get the session ID
            logger.info("Following redirects after login...")

            # Check if the URL contains 'loginName', which indicates successful login
            if 'loginName' in response.url:
                logger.info("Login successful")

                # Step 4: Get user information
                logger.info("Retrieving user information...")
                self._get_user_info()

                return True
            else:
                logger.error("Login failed, response URL: " + response.url)
                return False

        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return False

    def _get_user_info(self):
        """
        Retrieve user information after login.
        Sets self.user_info with user data.
        """
        try:
            # Extract the login name from URL if present
            login_name_match = re.search(r'loginName=([^&#]+)', self.session.get(config.ICLASS_SERVICE_URL).url)
            if login_name_match:
                login_name = login_name_match.group(1)

                # Get user information from API
                login_api = f"{config.ICLASS_API_BASE}/user/login.action"
                params = {
                    "phone": login_name,
                    "password": "",
                    "verificationType": "2",
                    "verificationUrl": "",
                    "userLevel": "1"
                }

                response = self.session.get(login_api, params=params)

                if response.status_code == 200:
                    user_data = response.json()
                    if user_data.get("STATUS") == "0":
                        self.user_info = user_data.get("result", {})
                        self.session_id = user_data.get("result", {}).get("sessionId")
                        logger.info(f"Got user info for: {self.user_info.get('realName')}")
                    else:
                        logger.error(f"Failed to get user info: {user_data}")
                else:
                    logger.error(f"Failed to get user info: {response.status_code}")
            else:
                logger.error("Could not extract login name from URL")
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")