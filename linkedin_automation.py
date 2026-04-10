#!/usr/bin/env python3
"""
LinkedIn Company Research & Lead Generation Automation
Author: Senior Python Developer - Web Automation Specialist
Purpose: Research companies, identify CMO/Marketing leads, extract data, and automate messaging
Safety: Rate limiting, session cookies, human-like behavior, status tracking
"""

import os
import sys
import json
import time
import random
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
import pickle

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc

# Google Sheets & API imports
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
import gspread
from gspread_dataframe import set_with_dataframe

# Data & HTTP imports
import pandas as pd
import requests
from bs4 import BeautifulSoup

# ============================================================================
# CONFIGURATION & LOGGING
# ============================================================================

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class LinkedInContact:
    """Data model for LinkedIn contact"""
    company: str
    url: str
    category: str
    employee_count: str
    contact_name: str
    contact_role: str
    contact_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_method: str = "LinkedIn"
    status: str = "Researched"
    timestamp: str = ""
    notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

# ============================================================================
# LINKEDIN AUTOMATION CLASS
# ============================================================================

class LinkedInAutomation:
    """
    Main automation class for LinkedIn research and outreach
    """
    
    # LinkedIn selectors (may need updates as LinkedIn changes DOM)
    SELECTORS = {
        'company_name': 'h1.text-heading-xlarge',
        'employees_count': '[data-test-id="about-us-employees-count"]',
        'industry': '[data-test-id="about-us-industry"]',
        'company_link': 'a[href*="/company/"]',
        'profile_name': 'h1.text-heading-xlarge',
        'connect_button': 'button[aria-label*="Invite"]',
        'message_button': 'button[aria-label*="Message"]',
        'send_button': 'button[data-test-id="send-button"]',
    }
    
    def __init__(self, headless: bool = True, rate_limit: int = 10, use_cookies: bool = True):
        """
        Initialize LinkedIn automation
        
        Args:
            headless: Run browser in headless mode
            rate_limit: Number of profiles to process per run
            use_cookies: Use saved session cookies (recommended)
        """
        self.headless = headless
        self.rate_limit = rate_limit
        self.use_cookies = use_cookies
        self.driver = None
        self.contacts: List[LinkedInContact] = []
        self.processed_count = 0
        self.session_file = Path('.linkedin_session.pkl')
        
        logger.info(f"Initializing LinkedInAutomation (headless={headless}, rate_limit={rate_limit})")
    
    # ========================================================================
    # BROWSER SETUP & SESSION MANAGEMENT
    # ========================================================================
    
    def _setup_browser(self) -> webdriver.Chrome:
        """
        Setup undetected Chrome driver with stealth options
        
        Returns:
            Configured Chrome WebDriver instance
        """
        logger.info("Setting up undetected Chrome driver...")
        
        options = ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless=new')
        
        # Stealth options to avoid LinkedIn detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--user-data-dir={Path.home()}/.chrome_linkedin_profile')
        
        # User agent rotation
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        try:
            driver = uc.Chrome(options=options, version_main=None)
            logger.info("Browser initialized successfully")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    def _save_session(self):
        """Save cookies to file for session persistence"""
        if self.driver:
            try:
                cookies = self.driver.get_cookies()
                with open(self.session_file, 'wb') as f:
                    pickle.dump(cookies, f)
                logger.info(f"Session saved to {self.session_file}")
            except Exception as e:
                logger.error(f"Failed to save session: {e}")
    
    def _load_session(self) -> bool:
        """
        Load cookies from file and inject into browser
        
        Returns:
            True if session loaded, False otherwise
        """
        if not self.session_file.exists():
            logger.info("No saved session found")
            return False
        
        try:
            with open(self.session_file, 'rb') as f:
                cookies = pickle.load(f)
            
            # Load LinkedIn main page first to establish domain
            self.driver.get('https://www.linkedin.com/feed/')
            time.sleep(self._gaussian_delay(2, 1))
            
            # Inject cookies
            for cookie in cookies:
                try:
                    # Handle cookie attributes that might not exist
                    cookie_dict = {k: v for k, v in cookie.items() 
                                   if k in ['name', 'value', 'domain', 'path', 'secure', 'httpOnly']}
                    self.driver.add_cookie(cookie_dict)
                except Exception as e:
                    logger.warning(f"Failed to add cookie {cookie.get('name')}: {e}")
            
            # Refresh page with cookies loaded
            self.driver.get('https://www.linkedin.com/feed/')
            time.sleep(self._gaussian_delay(2, 1))
            
            # Check if logged in by looking for profile element
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test-id="navatar"]'))
                )
                logger.info("Session loaded successfully - user authenticated")
                return True
            except TimeoutException:
                logger.warning("Session loaded but authentication may have failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False
    
    def login_manual(self):
        """
        Manual login flow - user enters credentials in browser
        After login, session is saved for future runs
        """
        logger.info("Starting manual login flow...")
        logger.info("Please log in to LinkedIn in the browser window that opens")
        
        self.driver.get('https://www.linkedin.com/login')
        time.sleep(self._gaussian_delay(3, 1))
        
        # Wait for user to log in manually
        try:
            WebDriverWait(self.driver, 300).until(  # 5 minute timeout
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test-id="navatar"]'))
            )
            logger.info("Login detected! Saving session...")
            time.sleep(self._gaussian_delay(2, 1))
            self._save_session()
            logger.info("Session saved successfully")
        except TimeoutException:
            logger.error("Login timeout - user did not complete login within 5 minutes")
            raise
    
    # ========================================================================
    # HUMAN-LIKE BEHAVIOR
    # ========================================================================
    
    @staticmethod
    def _gaussian_delay(mean: float = 2.0, std_dev: float = 1.0) -> float:
        """
        Generate realistic delay using Gaussian distribution
        
        Args:
            mean: Mean delay in seconds
            std_dev: Standard deviation
            
        Returns:
            Delay in seconds (minimum 0.5s)
        """
        delay = max(0.5, random.gauss(mean, std_dev))
        return delay
    
    def _human_scroll(self, element=None):
        """Simulate human-like scrolling"""
        try:
            if element:
                actions = ActionChains(self.driver)
                actions.move_to_element(element)
                actions.perform()
            
            scroll_amount = random.randint(100, 500)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
            time.sleep(self._gaussian_delay(1, 0.5))
        except Exception as e:
            logger.warning(f"Scroll failed: {e}")
    
    def _random_mouse_movement(self):
        """Simulate random mouse movements"""
        try:
            actions = ActionChains(self.driver)
            for _ in range(random.randint(2, 4)):
                x = random.randint(0, 1920)
                y = random.randint(0, 1080)
                actions.move_by_offset(x, y)
                actions.pause(random.uniform(0.1, 0.3))
            actions.perform()
        except Exception as e:
            logger.warning(f"Mouse movement failed: {e}")
    
    # ========================================================================
    # COMPANY RESEARCH
    # ========================================================================
    
    def search_company(self, company_name: str) -> Optional[str]:
        """
        Search for company on LinkedIn and return company URL
        
        Args:
            company_name: Name of company to search
            
        Returns:
            LinkedIn company URL or None
        """
        try:
            logger.info(f"Searching for company: {company_name}")
            
            search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name.replace(' ', '+')}"
            self.driver.get(search_url)
            time.sleep(self._gaussian_delay(3, 1))
            
            # Find first result link
            try:
                first_result = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/company/"]'))
                )
                company_url = first_result.get_attribute('href')
                logger.info(f"Found company URL: {company_url}")
                return company_url
            except TimeoutException:
                logger.warning(f"No results found for {company_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching company {company_name}: {e}")
            return None
    
    def extract_company_data(self, company_url: str) -> Optional[Dict]:
        """
        Extract company data from LinkedIn company page
        
        Args:
            company_url: URL of LinkedIn company page
            
        Returns:
            Dictionary with company data or None
        """
        try:
            logger.info(f"Extracting company data from {company_url}")
            
            self.driver.get(company_url)
            time.sleep(self._gaussian_delay(3, 1))
            self._human_scroll()
            
            company_data = {}
            
            # Extract company name
            try:
                name_elem = self.driver.find_element(By.CSS_SELECTOR, 'h1.text-heading-xlarge')
                company_data['company_name'] = name_elem.text.strip()
            except:
                company_data['company_name'] = 'Unknown'
            
            # Extract employee count
            try:
                emp_elem = self.driver.find_element(By.CSS_SELECTOR, '[data-test-id="about-us-employees-count"]')
                company_data['employee_count'] = emp_elem.text.strip()
            except:
                company_data['employee_count'] = 'Unknown'
            
            # Extract industry
            try:
                ind_elem = self.driver.find_element(By.CSS_SELECTOR, '[data-test-id="about-us-industry"]')
                company_data['industry'] = ind_elem.text.strip()
            except:
                company_data['industry'] = 'Unknown'
            
            company_data['url'] = company_url
            logger.info(f"Extracted data: {company_data}")
            return company_data
            
        except Exception as e:
            logger.error(f"Error extracting company data: {e}")
            return None
    
    # ========================================================================
    # MARKETING LEAD RESEARCH
    # ========================================================================
    
    def find_marketing_lead(self, company_url: str) -> Optional[Dict]:
        """
        Find CMO or highest-ranking marketing lead at company
        
        Args:
            company_url: URL of LinkedIn company page
            
        Returns:
            Dictionary with contact info or None
        """
        try:
            logger.info("Searching for marketing lead...")
            
            # Navigate to company people page
            company_id = company_url.split('/company/')[-1].split('/')[0]
            people_url = f"https://www.linkedin.com/search/results/people/?currentCompany={company_id}&keywords=CMO%2CCMO%2CChief%20Marketing%20Officer%2CMarketing%20Director%2CHead%20of%20Marketing"
            
            self.driver.get(people_url)
            time.sleep(self._gaussian_delay(3, 1))
            self._human_scroll()
            
            # Try to find first result
            try:
                # Wait for search results to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="/in/"]'))
                )
                
                profile_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
                
                if profile_links:
                    first_profile = profile_links[0]
                    profile_url = first_profile.get_attribute('href')
                    profile_name = first_profile.text.strip()
                    
                    logger.info(f"Found marketing lead: {profile_name}")
                    
                    return {
                        'name': profile_name,
                        'url': profile_url,
                        'company_url': company_url
                    }
            except TimeoutException:
                logger.warning("No marketing leads found in search results")
                return None
                
        except Exception as e:
            logger.error(f"Error finding marketing lead: {e}")
            return None
    
    def extract_profile_data(self, profile_url: str) -> Optional[Dict]:
        """
        Extract detailed data from LinkedIn profile
        
        Args:
            profile_url: URL of LinkedIn profile
            
        Returns:
            Dictionary with profile data or None
        """
        try:
            logger.info(f"Extracting profile data from {profile_url}")
            
            self.driver.get(profile_url)
            time.sleep(self._gaussian_delay(3, 1))
            self._human_scroll()
            
            profile_data = {}
            
            # Extract name
            try:
                name_elem = self.driver.find_element(By.CSS_SELECTOR, 'h1')
                profile_data['name'] = name_elem.text.strip()
            except:
                profile_data['name'] = 'Unknown'
            
            # Extract headline (role)
            try:
                headline_elem = self.driver.find_element(By.CSS_SELECTOR, '#headline')
                profile_data['role'] = headline_elem.text.strip()
            except:
                profile_data['role'] = 'Unknown'
            
            profile_data['url'] = profile_url
            logger.info(f"Extracted profile: {profile_data}")
            return profile_data
            
        except Exception as e:
            logger.error(f"Error extracting profile data: {e}")
            return None
    
    # ========================================================================
    # EXTERNAL API INTEGRATION (Hunter.io)
    # ========================================================================
    
    def get_email_from_hunter(self, name: str, domain: str) -> Optional[str]:
        """
        Use Hunter.io API to find email address
        
        Args:
            name: Full name of contact
            domain: Company domain (e.g., "google.com")
            
        Returns:
            Email address or None
        """
        api_key = os.getenv('HUNTER_API_KEY')
        
        if not api_key:
            logger.warning("HUNTER_API_KEY not set - skipping email lookup")
            return None
        
        try:
            # First, try domain search
            url = f"https://api.hunter.io/v2/domain-search"
            params = {
                'domain': domain,
                'type': 'personal',
                'api_key': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                emails = data.get('data', {}).get('emails', [])
                
                # Try to find matching name
                for email_obj in emails:
                    if name.split()[0].lower() in email_obj.get('value', '').lower():
                        logger.info(f"Found email via Hunter: {email_obj['value']}")
                        return email_obj['value']
                
                # Return first email if no name match
                if emails:
                    logger.info(f"Found email via Hunter: {emails[0]['value']}")
                    return emails[0]['value']
            
            logger.warning(f"Hunter.io API returned status {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error calling Hunter.io API: {e}")
            return None
    
    # ========================================================================
    # MESSAGING & CONNECTION
    # ========================================================================
    
    def create_message(self, contact: LinkedInContact, template: Optional[str] = None) -> str:
        """
        Create personalized message for contact
        
        Args:
            contact: LinkedInContact object
            template: Optional custom template
            
        Returns:
            Personalized message
        """
        first_name = contact.contact_name.split()[0] if contact.contact_name else "there"
        
        if template:
            return template.format(
                first_name=first_name,
                contact_name=contact.contact_name,
                company=contact.company,
                role=contact.contact_role
            )
        
        # Default template
        default_message = f"""Hi {first_name},

I've been impressed by {contact.company}'s approach to marketing innovation. I'd love to connect and explore how we might collaborate on growth initiatives.

Looking forward to connecting!

Best regards"""
        
        return default_message
    
    def send_connection_request(self, profile_url: str) -> bool:
        """
        Send LinkedIn connection request to profile
        
        Args:
            profile_url: URL of LinkedIn profile
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Sending connection request to {profile_url}")
            
            self.driver.get(profile_url)
            time.sleep(self._gaussian_delay(3, 1))
            
            # Find and click connect button
            try:
                connect_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label*="Invite"]'))
                )
                self._human_scroll(connect_button)
                time.sleep(self._gaussian_delay(1, 0.5))
                connect_button.click()
                
                logger.info("Connection request sent")
                time.sleep(self._gaussian_delay(2, 1))
                return True
                
            except TimeoutException:
                logger.warning("Connect button not found or already connected")
                return False
                
        except Exception as e:
            logger.error(f"Error sending connection request: {e}")
            return False
    
    def send_message(self, profile_url: str, message: str) -> bool:
        """
        Send LinkedIn message to contact
        
        Args:
            profile_url: URL of LinkedIn profile
            message: Message text to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Sending message to {profile_url}")
            
            self.driver.get(profile_url)
            time.sleep(self._gaussian_delay(3, 1))
            
            # Try to find message button
            try:
                message_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label*="Message"]'))
                )
                self._human_scroll(message_button)
                time.sleep(self._gaussian_delay(1, 0.5))
                message_button.click()
                
                time.sleep(self._gaussian_delay(2, 1))
                
                # Type message
                message_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[role="textbox"]'))
                )
                
                # Type message with realistic timing
                for char in message:
                    message_field.send_keys(char)
                    time.sleep(random.uniform(0.01, 0.05))
                
                time.sleep(self._gaussian_delay(1, 0.5))
                
                # Find and click send button
                send_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-test-id="send-button"]')
                send_button.click()
                
                logger.info("Message sent successfully")
                time.sleep(self._gaussian_delay(2, 1))
                return True
                
            except TimeoutException:
                logger.warning("Message interface not available")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    # ========================================================================
    # GOOGLE SHEETS INTEGRATION
    # ========================================================================
    
    def setup_google_sheets(self) -> gspread.Spreadsheet:
        """
        Setup Google Sheets authentication and get spreadsheet
        
        Returns:
            gspread.Spreadsheet object
        """
        try:
            # Check for service account credentials
            creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
            
            if creds_file and os.path.exists(creds_file):
                logger.info("Using service account credentials")
                credentials = service_account.Credentials.from_service_account_file(
                    creds_file,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            else:
                # Fallback to OAuth2
                logger.info("Using OAuth2 credentials")
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json',
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                credentials = flow.run_local_server(port=0)
            
            gc = gspread.authorize(credentials)
            
            # Get or create spreadsheet
            sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'LinkedIn Leads')
            
            try:
                spreadsheet = gc.open(sheet_name)
                logger.info(f"Opened existing spreadsheet: {sheet_name}")
            except gspread.SpreadsheetNotFound:
                logger.info(f"Creating new spreadsheet: {sheet_name}")
                spreadsheet = gc.create(sheet_name)
                # Share with user
                user_email = os.getenv('GOOGLE_USER_EMAIL')
                if user_email:
                    spreadsheet.share(user_email, perm_type='user', role='owner')
            
            return spreadsheet
            
        except Exception as e:
            logger.error(f"Error setting up Google Sheets: {e}")
            raise
    
    def sync_to_google_sheets(self, spreadsheet: gspread.Spreadsheet):
        """
        Sync contacts to Google Sheets
        
        Args:
            spreadsheet: gspread.Spreadsheet object
        """
        try:
            logger.info(f"Syncing {len(self.contacts)} contacts to Google Sheets...")
            
            # Convert contacts to dataframe
            df = pd.DataFrame([c.to_dict() for c in self.contacts])
            
            # Reorder columns
            columns = [
                'company', 'url', 'category', 'employee_count',
                'contact_name', 'contact_role', 'contact_email',
                'contact_method', 'status', 'timestamp', 'notes'
            ]
            df = df[[col for col in columns if col in df.columns]]
            
            # Get or create worksheet
            try:
                worksheet = spreadsheet.worksheet('Leads')
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet('Leads', len(df) + 10, len(columns))
            
            # Clear and write data
            worksheet.clear()
            set_with_dataframe(worksheet, df, include_index=False)
            
            logger.info("Successfully synced to Google Sheets")
            
        except Exception as e:
            logger.error(f"Error syncing to Google Sheets: {e}")
    
    # ========================================================================
    # MAIN WORKFLOW
    # ========================================================================
    
    def process_company(self, company_name: str, send_message: bool = False,
                       message_template: Optional[str] = None) -> bool:
        """
        Complete workflow for single company:
        1. Search company
        2. Extract company data
        3. Find marketing lead
        4. Send connection/message
        5. Update status
        
        Args:
            company_name: Name of company to research
            send_message: Whether to send message after connection
            message_template: Custom message template
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing company: {company_name}")
            logger.info(f"{'='*60}")
            
            # Check rate limit
            if self.processed_count >= self.rate_limit:
                logger.warning(f"Rate limit reached ({self.rate_limit} profiles)")
                return False
            
            # Step 1: Search company
            company_url = self.search_company(company_name)
            if not company_url:
                logger.error(f"Failed to find company: {company_name}")
                return False
            
            time.sleep(self._gaussian_delay(2, 1))
            
            # Step 2: Extract company data
            company_data = self.extract_company_data(company_url)
            if not company_data:
                logger.error(f"Failed to extract company data")
                return False
            
            time.sleep(self._gaussian_delay(2, 1))
            
            # Step 3: Find marketing lead
            lead_data = self.find_marketing_lead(company_url)
            if not lead_data:
                logger.error(f"Failed to find marketing lead")
                return False
            
            time.sleep(self._gaussian_delay(2, 1))
            
            # Step 4: Extract profile data
            profile_data = self.extract_profile_data(lead_data['url'])
            if not profile_data:
                logger.error(f"Failed to extract profile data")
                return False
            
            time.sleep(self._gaussian_delay(2, 1))
            
            # Step 5: Try to get email from Hunter
            email = None
            domain = company_url.split('/company/')[-1].split('/')[0]
            if domain:
                email = self.get_email_from_hunter(profile_data['name'], f"{domain}.com")
            
            time.sleep(self._gaussian_delay(1, 0.5))
            
            # Create contact object
            contact = LinkedInContact(
                company=company_data['company_name'],
                url=company_url,
                category=company_data['industry'],
                employee_count=company_data['employee_count'],
                contact_name=profile_data['name'],
                contact_role=profile_data['role'],
                contact_url=profile_data['url'],
                contact_email=email,
                contact_method="LinkedIn",
                status="Connection Sent" if send_message else "Researched",
                timestamp=datetime.now().isoformat(),
                notes=""
            )
            
            # Step 6: Send connection request
            if self.send_connection_request(lead_data['url']):
                contact.status = "Connection Sent"
                
                # Step 7: Send message if requested
                if send_message:
                    time.sleep(self._gaussian_delay(3, 2))
                    message = self.create_message(contact, message_template)
                    
                    if self.send_message(lead_data['url'], message):
                        contact.status = "Message Sent"
                    else:
                        contact.status = "Connection Sent"
                        contact.notes = "Message send failed"
            else:
                contact.status = "Failed - Already Connected"
            
            self.contacts.append(contact)
            self.processed_count += 1
            
            logger.info(f"✓ Successfully processed {company_name}")
            logger.info(f"  Status: {contact.status}")
            logger.info(f"  Lead: {contact.contact_name} ({contact.contact_role})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing company {company_name}: {e}")
            return False
    
    def run(self, companies: List[str], send_messages: bool = False,
            message_template: Optional[str] = None, skip_existing: bool = True):
        """
        Main execution loop
        
        Args:
            companies: List of company names to process
            send_messages: Whether to send messages
            message_template: Custom message template
            skip_existing: Skip companies already in sheet
        """
        try:
            # Setup browser
            self.driver = self._setup_browser()
            
            # Try to load session
            if self.use_cookies and not self._load_session():
                logger.info("No valid session found, starting manual login...")
                self.login_manual()
            
            # Setup Google Sheets
            try:
                spreadsheet = self.setup_google_sheets()
            except Exception as e:
                logger.error(f"Failed to setup Google Sheets: {e}")
                spreadsheet = None
            
            # Process companies
            logger.info(f"\nStarting to process {len(companies)} companies...")
            
            for company in companies:
                if self.processed_count >= self.rate_limit:
                    logger.info(f"Reached rate limit of {self.rate_limit}")
                    break
                
                try:
                    self.process_company(company, send_messages, message_template)
                except Exception as e:
                    logger.error(f"Error in main loop for {company}: {e}")
                
                # Delay between companies
                time.sleep(self._gaussian_delay(3, 2))
            
            # Save session
            self._save_session()
            
            # Sync to Google Sheets
            if spreadsheet:
                self.sync_to_google_sheets(spreadsheet)
            
            # Export to CSV as backup
            self.export_to_csv()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Automation complete!")
            logger.info(f"Processed: {self.processed_count} companies")
            logger.info(f"Contacts extracted: {len(self.contacts)}")
            logger.info(f"{'='*60}")
            
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
    
    def export_to_csv(self, filename: str = 'linkedin_leads.csv'):
        """Export contacts to CSV file"""
        try:
            df = pd.DataFrame([c.to_dict() for c in self.contacts])
            df.to_csv(filename, index=False)
            logger.info(f"Exported {len(self.contacts)} contacts to {filename}")
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    
    # Configuration from environment
    headless = os.getenv('HEADLESS', 'true').lower() == 'true'
    rate_limit = int(os.getenv('RATE_LIMIT', '10'))
    use_cookies = os.getenv('USE_COOKIES', 'true').lower() == 'true'
    send_messages = os.getenv('SEND_MESSAGES', 'false').lower() == 'true'
    
    # Example companies to research
    companies = [
        "Google",
        "Microsoft",
        "Apple",
        "Amazon",
        "Meta",
    ]
    
    # Custom message template (optional)
    message_template = """Hi {first_name},

I noticed {company}'s impressive growth in the market. I believe there might be great opportunities for us to collaborate on marketing initiatives.

Would you be open to a quick call next week?

Best,
[Your Name]"""
    
    # Initialize automation
    automation = LinkedInAutomation(
        headless=headless,
        rate_limit=rate_limit,
        use_cookies=use_cookies
    )
    
    # Run automation
    automation.run(
        companies=companies,
        send_messages=send_messages,
        message_template=message_template
    )


if __name__ == '__main__':
    main()
