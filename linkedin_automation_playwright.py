#!/usr/bin/env python3
"""
LinkedIn Company Research & Lead Generation Automation
Author: Senior Python Developer - Web Automation Specialist
Purpose: Research companies, identify CMO/Marketing leads, extract data, and automate messaging
Safety: Rate limiting, session cookies, human-like behavior, status tracking

Updated to use Playwright instead of Selenium for better compatibility
"""

import os
import sys
import json
import time
import random
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Playwright imports
from playwright.async_api import async_playwright, Browser, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError

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
    Main automation class for LinkedIn research and outreach using Playwright
    """

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
        self.playwright = None
        self.browser = None
        self.context = None
        self.contacts: List[LinkedInContact] = []
        self.processed_count = 0
        self.session_file = Path('linkedin_session.json')

        logger.info(f"Initializing LinkedInAutomation (headless={headless}, rate_limit={rate_limit})")

    async def __aenter__(self):
        await self._setup_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._cleanup()

    # ========================================================================
    # BROWSER SETUP & SESSION MANAGEMENT
    # ========================================================================

    async def _setup_browser(self):
        """
        Setup Playwright browser with stealth options
        """
        logger.info("Setting up Playwright browser...")

        self.playwright = await async_playwright().start()

        # Launch browser with stealth options
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )

        # Create context with user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        self.context = await self.browser.new_context(
            user_agent=random.choice(user_agents),
            viewport={'width': 1920, 'height': 1080}
        )

        logger.info("Browser initialized successfully")

    async def _cleanup(self):
        """Clean up browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser cleanup complete")

    async def _save_session(self):
        """Save cookies to file for session persistence"""
        if self.context:
            try:
                cookies = await self.context.cookies()
                with open(self.session_file, 'w') as f:
                    json.dump(cookies, f, indent=2)
                logger.info(f"Session saved to {self.session_file}")
            except Exception as e:
                logger.error(f"Failed to save session: {e}")

    async def _load_session(self) -> bool:
        """
        Load cookies from file and inject into browser

        Returns:
            True if session loaded, False otherwise
        """
        if not self.session_file.exists():
            logger.info("No saved session found")
            return False

        try:
            with open(self.session_file, 'r') as f:
                cookies = json.load(f)

            # Navigate to LinkedIn first
            page = await self.context.new_page()
            await page.goto('https://www.linkedin.com/feed/')
            await self._human_delay(2, 1)

            # Add cookies
            await self.context.add_cookies(cookies)

            # Refresh page with cookies
            await page.reload()
            await self._human_delay(2, 1)

            # Check if logged in
            try:
                await page.wait_for_selector('[data-test-id="navatar"]', timeout=10000)
                logger.info("Session loaded successfully - user authenticated")
                await page.close()
                return True
            except PlaywrightTimeoutError:
                logger.warning("Session loaded but authentication may have failed")
                await page.close()
                return False

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False

    async def login_manual(self):
        """
        Manual login flow - user enters credentials in browser
        After login, session is saved for future runs
        """
        logger.info("Starting manual login flow...")
        logger.info("Please log in to LinkedIn in the browser window that opens")

        page = await self.context.new_page()
        await page.goto('https://www.linkedin.com/login')
        await self._human_delay(3, 1)

        # Wait for user to log in manually
        try:
            await page.wait_for_selector('[data-test-id="navatar"]', timeout=300000)  # 5 minute timeout
            logger.info("Login detected! Saving session...")
            await self._human_delay(2, 1)
            await self._save_session()
            logger.info("Session saved successfully")
        except PlaywrightTimeoutError:
            logger.error("Login timeout - user did not complete login within 5 minutes")
            raise
        finally:
            await page.close()

    # ========================================================================
    # HUMAN-LIKE BEHAVIOR
    # ========================================================================

    @staticmethod
    async def _human_delay(mean: float = 2.0, std_dev: float = 1.0) -> float:
        """
        Generate realistic delay using Gaussian distribution

        Args:
            mean: Mean delay in seconds
            std_dev: Standard deviation

        Returns:
            Delay in seconds (minimum 0.5s)
        """
        delay = max(0.5, random.gauss(mean, std_dev))
        await asyncio.sleep(delay)
        return delay

    async def _human_scroll(self, page: Page):
        """Simulate human-like scrolling"""
        try:
            scroll_amount = random.randint(100, 500)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await self._human_delay(1, 0.5)
        except Exception as e:
            logger.warning(f"Scroll failed: {e}")

    # ========================================================================
    # COMPANY RESEARCH
    # ========================================================================

    async def search_company(self, company_name: str) -> Optional[str]:
        """Search for company on LinkedIn and return company URL"""
        page = await self.context.new_page()

        try:
            logger.info(f"Searching for company: {company_name}")

            search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name.replace(' ', '+')}"
            await page.goto(search_url)
            await self._human_delay(3, 1)
            await self._human_scroll(page)

            # Find first result link
            try:
                company_link = await page.wait_for_selector('a[href*="/company/"]', timeout=10000)
                company_url = await company_link.get_attribute('href')
                logger.info(f"Found company URL: {company_url}")
                return company_url
            except PlaywrightTimeoutError:
                logger.warning(f"No results found for {company_name}")
                return None

        except Exception as e:
            logger.error(f"Error searching company {company_name}: {e}")
            return None
        finally:
            await page.close()

    async def extract_company_data(self, company_url: str) -> Optional[Dict]:
        """
        Extract company data from LinkedIn company page
        """
        page = await self.context.new_page()

        try:
            logger.info(f"Extracting company data from {company_url}")

            await page.goto(company_url)
            await self._human_delay(3, 1)
            await self._human_scroll(page)

            company_data = {}

            # Extract company name
            try:
                name_elem = await page.query_selector('h1.text-heading-xlarge')
                if name_elem:
                    company_data['company_name'] = await name_elem.inner_text()
                else:
                    company_data['company_name'] = 'Unknown'
            except:
                company_data['company_name'] = 'Unknown'

            # Extract employee count
            try:
                emp_elem = await page.query_selector('[data-test-id="about-us-employees-count"]')
                if emp_elem:
                    company_data['employee_count'] = await emp_elem.inner_text()
                else:
                    company_data['employee_count'] = 'Unknown'
            except:
                company_data['employee_count'] = 'Unknown'

            # Extract industry
            try:
                ind_elem = await page.query_selector('[data-test-id="about-us-industry"]')
                if ind_elem:
                    company_data['industry'] = await ind_elem.inner_text()
                else:
                    company_data['industry'] = 'Unknown'
            except:
                company_data['industry'] = 'Unknown'

            company_data['url'] = company_url
            logger.info(f"Extracted data: {company_data}")
            return company_data

        except Exception as e:
            logger.error(f"Error extracting company data: {e}")
            return None
        finally:
            await page.close()

    def _is_tech_industry(self, industry: str) -> bool:
        if not industry:
            return False

        keywords = [
            'software', 'information technology', 'internet', 'computer',
            'telecommunications', 'technology', 'digital', 'fintech', 'e-commerce'
        ]
        return any(keyword in industry.lower() for keyword in keywords)

    def _parse_employee_count(self, employee_count: str) -> Optional[int]:
        if not employee_count or employee_count.lower() == 'unknown':
            return None

        cleaned = employee_count.lower().replace('employees', '').replace('employee', '').replace('+', '').strip()
        if '-' in cleaned:
            parts = cleaned.split('-')
            try:
                return int(parts[0].strip())
            except ValueError:
                return None

        try:
            return int(cleaned)
        except ValueError:
            return None

    def _matches_company_criteria(self, company_data: Dict) -> bool:
        if not company_data:
            return False

        if not self._is_tech_industry(company_data.get('industry', '')):
            return False

        size = self._parse_employee_count(company_data.get('employee_count', ''))
        if size is None:
            return False

        return 200 <= size <= 1000

    async def search_companies_in_vietnam(self, limit: int = 10) -> List[str]:
        """
        Search for Vietnamese tech companies with mid-market size on LinkedIn
        """
        page = await self.context.new_page()

        try:
            logger.info("🔍 Searching for tech companies in Vietnam...")

            # Search for Vietnamese tech companies
            search_url = (
                "https://www.linkedin.com/search/results/companies/"
                "?keywords=vietnam%20technology%20company&origin=GLOBAL_SEARCH_HEADER"
            )
            await page.goto(search_url)
            await self._human_delay(3, 1)
            await self._human_scroll(page)

            companies = []
            seen = set()

            try:
                await page.wait_for_selector('[data-test-id="company-result-item"]', timeout=10000)

                company_elements = await page.query_selector_all('[data-test-id="company-result-item"] a[href*="/company/"]')

                for elem in company_elements:
                    if len(companies) >= limit:
                        break

                    company_url = await elem.get_attribute('href')
                    if not company_url:
                        continue

                    company_url = company_url.split('?')[0]
                    if company_url in seen:
                        continue

                    seen.add(company_url)
                    company_name = await elem.inner_text() or ''
                    company_name = company_name.strip()
                    if not company_name:
                        continue

                    company_data = await self.extract_company_data(company_url)
                    if self._matches_company_criteria(company_data):
                        companies.append(company_name)

                logger.info(f"✅ Found {len(companies)} tech companies in Vietnam via LinkedIn search")

            except PlaywrightTimeoutError:
                logger.warning("⚠️  Could not find company search results, using fallback list")
                fallback_companies = [
                    "Tiki", "MoMo", "VNG Corporation", "Cốc Cốc", "Sendo",
                    "Foody", "Be Group", "AhaMove", "TopCV", "GotIt",
                    "Lozi", "Yody", "Homee Vietnam", "Edumall", "Hocmai Academy",
                    "NotionPharm", "Sky Mavis", "Zalo Cloud", "ELSA Speak", "Skillbox Vietnam",
                    "OnTaxi", "HashTech Digital", "Metaverse Vietnam", "TechComBank Innovation", "Bamboo Airways Digital"
                ]
                companies = fallback_companies[:limit]
                logger.info(f"📋 Using fallback list: {len(companies)} tech companies")

            return companies

        except Exception as e:
            logger.error(f"❌ Error searching companies in Vietnam: {e}")
            return []
        finally:
            await page.close()

    # ========================================================================
    # MARKETING LEAD RESEARCH
    # ========================================================================

    async def find_marketing_lead(self, company_url: str) -> Optional[Dict]:
        """
        Find CMO or highest-ranking marketing lead at company
        """
        page = await self.context.new_page()

        try:
            logger.info("Searching for marketing lead...")

            # Navigate to company people page
            company_id = company_url.split('/company/')[-1].split('/')[0]
            people_url = f"https://www.linkedin.com/search/results/people/?currentCompany={company_id}&keywords=CMO%2CCMO%2CChief%20Marketing%20Officer%2CMarketing%20Director%2CHead%20of%20Marketing"
            await page.goto(people_url)
            await self._human_delay(3, 1)
            await self._human_scroll(page)

            # Try to find first result
            try:
                # Wait for search results to load
                await page.wait_for_selector('a[href*="/in/"]', timeout=10000)

                profile_links = await page.query_selector_all('a[href*="/in/"]')

                if profile_links:
                    first_profile = profile_links[0]
                    profile_url = await first_profile.get_attribute('href')
                    profile_name = await first_profile.inner_text()

                    logger.info(f"Found marketing lead: {profile_name}")

                    return {
                        'name': profile_name.strip(),
                        'url': profile_url
                    }
            except PlaywrightTimeoutError:
                logger.warning("No marketing leads found in search results")
                return None

        except Exception as e:
            logger.error(f"Error finding marketing lead: {e}")
            return None
        finally:
            await page.close()

    async def extract_profile_data(self, profile_url: str) -> Optional[Dict]:
        """
        Extract detailed data from LinkedIn profile
        """
        page = await self.context.new_page()

        try:
            logger.info(f"Extracting profile data from {profile_url}")

            await page.goto(profile_url)
            await self._human_delay(3, 1)
            await self._human_scroll(page)

            profile_data = {}

            # Extract name
            try:
                name_elem = await page.query_selector('h1')
                if name_elem:
                    profile_data['name'] = await name_elem.inner_text()
                else:
                    profile_data['name'] = 'Unknown'
            except:
                profile_data['name'] = 'Unknown'

            # Extract headline (role)
            try:
                headline_elem = await page.query_selector('#headline')
                if headline_elem:
                    profile_data['role'] = await headline_elem.inner_text()
                else:
                    profile_data['role'] = 'Unknown'
            except:
                profile_data['role'] = 'Unknown'

            profile_data['url'] = profile_url
            logger.info(f"Extracted profile: {profile_data}")
            return profile_data

        except Exception as e:
            logger.error(f"Error extracting profile data: {e}")
            return None
        finally:
            await page.close()

    # ========================================================================
    # EXTERNAL API INTEGRATION (Hunter.io)
    # ========================================================================

    def get_email_from_hunter(self, name: str, domain: str) -> Optional[str]:
        """
        Use Hunter.io API to find email address
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

    async def send_connection_request(self, profile_url: str) -> bool:
        """
        Send LinkedIn connection request to profile
        """
        page = await self.context.new_page()

        try:
            logger.info(f"Sending connection request to {profile_url}")

            await page.goto(profile_url)
            await self._human_delay(3, 1)

            # Find and click connect button
            try:
                connect_button = await page.wait_for_selector('button[aria-label*="Invite"]', timeout=10000)
                await self._human_scroll(page)
                await self._human_delay(1, 0.5)
                await connect_button.click()

                logger.info("Connection request sent")
                await self._human_delay(2, 1)
                return True

            except PlaywrightTimeoutError:
                logger.warning("Connect button not found or already connected")
                return False

        except Exception as e:
            logger.error(f"Error sending connection request: {e}")
            return False
        finally:
            await page.close()

    async def send_message(self, profile_url: str, message: str) -> bool:
        """
        Send LinkedIn message to contact
        """
        page = await self.context.new_page()

        try:
            logger.info(f"Sending message to {profile_url}")

            await page.goto(profile_url)
            await self._human_delay(3, 1)

            # Try to find message button
            try:
                message_button = await page.wait_for_selector('button[aria-label*="Message"]', timeout=10000)
                await self._human_scroll(page)
                await self._human_delay(1, 0.5)
                await message_button.click()

                await self._human_delay(2, 1)

                # Type message
                message_field = await page.wait_for_selector('[role="textbox"]', timeout=10000)

                # Type message with realistic timing
                for char in message:
                    await message_field.type(char)
                    await asyncio.sleep(random.uniform(0.01, 0.05))

                await self._human_delay(1, 0.5)

                # Find and click send button
                send_button = await page.wait_for_selector('button[data-test-id="send-button"]', timeout=10000)
                await send_button.click()

                logger.info("Message sent successfully")
                await self._human_delay(2, 1)
                return True

            except PlaywrightTimeoutError:
                logger.warning("Message interface not available")
                return False

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
        finally:
            await page.close()

    async def outreach_contact(self, profile_url: str, message: Optional[str] = None,
                               send_connection: bool = True) -> bool:
        """
        Perform outreach for a single contact after discovery.
        This method can be used later once the contact list is ready.
        """
        if send_connection:
            await self._human_delay(2, 1)
            await self.send_connection_request(profile_url)

        if message:
            await self._human_delay(2, 1)
            return await self.send_message(profile_url, message)

        return True

    # ========================================================================
    # GOOGLE SHEETS INTEGRATION
    # ========================================================================

    def setup_google_sheets(self) -> gspread.Spreadsheet:
        """
        Setup Google Sheets authentication and get spreadsheet
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

            return spreadsheet

        except Exception as e:
            logger.error(f"Error setting up Google Sheets: {e}")
            raise

    def sync_to_google_sheets(self, spreadsheet: gspread.Spreadsheet):
        """
        Sync contacts to Google Sheets
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

    async def process_company(self, company_name: str, send_message: bool = False,
                             message_template: Optional[str] = None) -> bool:
        """
        Complete workflow for single company:
        1. Search company
        2. Extract company data
        3. Find marketing lead
        4. Send connection/message
        5. Update status
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
            company_url = await self.search_company(company_name)
            if not company_url:
                logger.error(f"Failed to find company: {company_name}")
                return False

            await self._human_delay(2, 1)

            # Step 2: Extract company data
            company_data = await self.extract_company_data(company_url)
            if not company_data:
                logger.error(f"Failed to extract company data")
                return False

            await self._human_delay(2, 1)

            # Step 3: Find marketing lead
            lead_data = await self.find_marketing_lead(company_url)
            if not lead_data:
                logger.error(f"Failed to find marketing lead")
                return False

            await self._human_delay(2, 1)

            # Step 4: Extract profile data
            profile_data = await self.extract_profile_data(lead_data['url'])
            if not profile_data:
                logger.error(f"Failed to extract profile data")
                return False

            await self._human_delay(2, 1)

            # Step 5: Try to get email from Hunter
            email = None
            domain = company_url.split('/company/')[-1].split('/')[0]
            if domain:
                email = self.get_email_from_hunter(profile_data['name'], f"{domain}.com")

            await self._human_delay(1, 0.5)

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
                status="Researched",
                timestamp=datetime.now().isoformat(),
                notes=""
            )

            # Only perform outreach if explicitly requested
            if send_message:
                if await self.send_connection_request(lead_data['url']):
                    contact.status = "Connection Sent"
                else:
                    contact.notes = "Connection request unavailable or already connected"

                await self._human_delay(3, 2)
                message = self.create_message(contact, message_template)

                if await self.send_message(lead_data['url'], message):
                    contact.status = "Message Sent"
                else:
                    contact.notes = (contact.notes + " Message send failed").strip()

            self.contacts.append(contact)
            self.processed_count += 1

            logger.info(f"✓ Successfully processed {company_name}")
            logger.info(f"  Status: {contact.status}")
            logger.info(f"  Lead: {contact.contact_name} ({contact.contact_role})")

            return True

        except Exception as e:
            logger.error(f"Error processing company {company_name}: {e}")
            return False

    async def run(self, companies: List[str] = None, send_messages: bool = False,
                  message_template: Optional[str] = None, skip_existing: bool = True):
        """
        Main execution loop - automatically finds Vietnamese companies if none provided
        """
        try:
            await self._setup_browser()

            # Try to load session
            if self.use_cookies and not await self._load_session():
                logger.info("No valid session found, starting manual login...")
                await self.login_manual()

            # If no companies provided, search for Vietnamese companies
            if not companies:
                logger.info("📍 No companies specified - searching for companies in Vietnam...")
                companies = await self.search_companies_in_vietnam(limit=10)
                logger.info(f"🏢 Will process {len(companies)} Vietnamese companies")

            # Setup Google Sheets
            try:
                spreadsheet = self.setup_google_sheets()
            except Exception as e:
                logger.error(f"Failed to setup Google Sheets: {e}")
                spreadsheet = None

            # Process companies
            logger.info(f"\n🏭 Processing {len(companies)} Vietnamese companies...")

            for company in companies:
                if self.processed_count >= self.rate_limit:
                    logger.info(f"Reached rate limit of {self.rate_limit}")
                    break

                try:
                    await self.process_company(company, send_messages, message_template)
                except Exception as e:
                    logger.error(f"Error in main loop for {company}: {e}")

                # Delay between companies
                await self._human_delay(3, 2)

            # Save session
            await self._save_session()

            # Sync to Google Sheets
            if spreadsheet:
                self.sync_to_google_sheets(spreadsheet)

            # Export to CSV as backup
            self.export_to_csv()

            logger.info(f"\n{'='*60}")
            logger.info(f"🎉 Vietnam lead generation complete!")
            logger.info(f"📈 Processed: {self.processed_count} companies")
            logger.info(f"👥 Marketing leads found: {len(self.contacts)}")
            logger.info(f"📍 Location: Vietnam")
            logger.info(f"{'='*60}")

        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}")
        finally:
            await self._cleanup()

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

async def main():
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

I've been impressed by {company}'s approach to marketing innovation. I'd love to connect and explore how we might collaborate on growth initiatives.

Looking forward to connecting!

Best regards"""

    # Initialize automation
    async with LinkedInAutomation(
        headless=headless,
        rate_limit=rate_limit,
        use_cookies=use_cookies
    ) as automation:
        # Run automation
        await automation.run(
            companies=companies,
            send_messages=send_messages,
            message_template=message_template
        )


if __name__ == '__main__':
    asyncio.run(main())