#!/usr/bin/env python3
"""
LinkedIn Company Research & Lead Generation Automation - DEMO VERSION
Author: Senior Python Developer - Web Automation Specialist
Purpose: Research companies, identify CMO/Marketing leads, extract data, and automate messaging
Safety: Rate limiting, session cookies, human-like behavior, status tracking

DEMO VERSION: Shows the workflow without actual browser automation
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
        logging.FileHandler('linkedin_automation_demo.log'),
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
# LINKEDIN AUTOMATION DEMO CLASS
# ============================================================================

class LinkedInAutomationDemo:
    """
    Demo version that simulates LinkedIn automation without browser
    """

    def __init__(self, headless: bool = True, rate_limit: int = 10, use_cookies: bool = True):
        """
        Initialize LinkedIn automation demo
        """
        self.headless = headless
        self.rate_limit = rate_limit
        self.use_cookies = use_cookies
        self.contacts: List[LinkedInContact] = []
        self.processed_count = 0

        logger.info(f"Initializing LinkedInAutomationDemo (rate_limit={rate_limit})")

    # ========================================================================
    # SIMULATED HUMAN-LIKE BEHAVIOR
    # ========================================================================

    @staticmethod
    def _gaussian_delay(mean: float = 2.0, std_dev: float = 1.0) -> float:
        """Generate realistic delay using Gaussian distribution"""
        delay = max(0.5, random.gauss(mean, std_dev))
        time.sleep(delay)
        return delay

    def search_companies_in_vietnam(self, limit: int = 10) -> List[str]:
        """Simulate searching for companies in Vietnam"""
        logger.info("🔍 Searching for tech companies in Vietnam...")

        # Mock Vietnamese tech companies with 200-1000 employees
        vietnamese_companies = [
            "Tiki",
            "MoMo",
            "VNG Corporation",
            "Cốc Cốc",
            "Sendo",
            "Foody",
            "Be Group",
            "AhaMove",
            "TopCV",
            "GotIt",
            "Lozi",
            "Yody",
            "Homee Vietnam",
            "Edumall",
            "Hocmai Academy",
            "NotionPharm",
            "Sky Mavis",
            "Zalo Cloud",
            "ELSA Speak",
            "Skillbox Vietnam",
            "OnTaxi",
            "HashTech Digital",
            "Metaverse Vietnam",
            "TechComBank Innovation",
            "Bamboo Airways Digital"
        ]

        # Simulate search delay
        self._gaussian_delay(3, 1)

        # Return limited results
        selected_companies = vietnamese_companies[:limit]
        logger.info(f"✅ Found {len(selected_companies)} tech companies in Vietnam")

        return selected_companies

    # ========================================================================
    # MOCK DATA FOR DEMONSTRATION
    # ========================================================================

    def _get_mock_company_data(self, company_name: str) -> Dict:
        """Return mock company data for demonstration - Vietnamese companies"""
        mock_data = {
            "Tiki": {
                "url": "https://www.linkedin.com/company/tiki",
                "industry": "E-commerce",
                "employee_count": "450-600"
            },
            "MoMo": {
                "url": "https://www.linkedin.com/company/momo",
                "industry": "Financial Technology",
                "employee_count": "600-750"
            },
            "VNG Corporation": {
                "url": "https://www.linkedin.com/company/vng-corporation",
                "industry": "Internet",
                "employee_count": "750-900"
            },
            "Cốc Cốc": {
                "url": "https://www.linkedin.com/company/coc-coc",
                "industry": "Software",
                "employee_count": "380-450"
            },
            "Sendo": {
                "url": "https://www.linkedin.com/company/sendo",
                "industry": "E-commerce",
                "employee_count": "330-420"
            },
            "Foody": {
                "url": "https://www.linkedin.com/company/foody",
                "industry": "Internet",
                "employee_count": "220-300"
            },
            "Be Group": {
                "url": "https://www.linkedin.com/company/be-group",
                "industry": "Technology",
                "employee_count": "280-350"
            },
            "AhaMove": {
                "url": "https://www.linkedin.com/company/ahamove",
                "industry": "Logistics Technology",
                "employee_count": "250-320"
            },
            "TopCV": {
                "url": "https://www.linkedin.com/company/topcv",
                "industry": "Software",
                "employee_count": "200-250"
            },
            "GotIt": {
                "url": "https://www.linkedin.com/company/gotit",
                "industry": "Education Technology",
                "employee_count": "220-280"
            },
            "Lozi": {
                "url": "https://www.linkedin.com/company/lozi",
                "industry": "Technology",
                "employee_count": "180-250"
            },
            "Yody": {
                "url": "https://www.linkedin.com/company/yody",
                "industry": "E-commerce",
                "employee_count": "300-400"
            },
            "Homee Vietnam": {
                "url": "https://www.linkedin.com/company/homee-vietnam",
                "industry": "Technology",
                "employee_count": "150-220"
            },
            "Edumall": {
                "url": "https://www.linkedin.com/company/edumall",
                "industry": "Education Technology",
                "employee_count": "200-280"
            },
            "Hocmai Academy": {
                "url": "https://www.linkedin.com/company/hocmai-academy",
                "industry": "Education Technology",
                "employee_count": "280-380"
            },
            "NotionPharm": {
                "url": "https://www.linkedin.com/company/notionpharm",
                "industry": "Healthcare Technology",
                "employee_count": "120-200"
            },
            "Sky Mavis": {
                "url": "https://www.linkedin.com/company/sky-mavis",
                "industry": "Gaming Technology",
                "employee_count": "350-450"
            },
            "Zalo Cloud": {
                "url": "https://www.linkedin.com/company/zalo-cloud",
                "industry": "Software",
                "employee_count": "200-300"
            },
            "ELSA Speak": {
                "url": "https://www.linkedin.com/company/elsa-speak",
                "industry": "Education Technology",
                "employee_count": "150-220"
            },
            "Skillbox Vietnam": {
                "url": "https://www.linkedin.com/company/skillbox-vietnam",
                "industry": "Education Technology",
                "employee_count": "220-300"
            },
            "OnTaxi": {
                "url": "https://www.linkedin.com/company/ontaxi",
                "industry": "Transportation Technology",
                "employee_count": "280-360"
            },
            "HashTech Digital": {
                "url": "https://www.linkedin.com/company/hashtech-digital",
                "industry": "Software Development",
                "employee_count": "250-350"
            },
            "Metaverse Vietnam": {
                "url": "https://www.linkedin.com/company/metaverse-vietnam",
                "industry": "Technology",
                "employee_count": "200-280"
            },
            "TechComBank Innovation": {
                "url": "https://www.linkedin.com/company/techcombank-innovation",
                "industry": "Financial Technology",
                "employee_count": "300-400"
            },
            "Bamboo Airways Digital": {
                "url": "https://www.linkedin.com/company/bamboo-airways-digital",
                "industry": "Technology",
                "employee_count": "250-350"
            }
        }
        return mock_data.get(company_name, {
            "url": f"https://www.linkedin.com/company/{company_name.lower().replace(' ', '-')}",
            "industry": "Unknown",
            "employee_count": "Unknown"
        })

    def _get_mock_lead_data(self, company_name: str) -> Dict:
        """Return mock marketing lead data for demonstration"""
        mock_leads = {
            "Vingroup": {
                "name": "Nguyen Thi Thanh Thuy",
                "role": "Chief Marketing Officer",
                "url": "https://www.linkedin.com/in/nguyen-thi-thanh-thuy-vingroup"
            },
            "Vietcombank": {
                "name": "Pham Thanh Long",
                "role": "Deputy Director of Marketing",
                "url": "https://www.linkedin.com/in/pham-thanh-long-vietcombank"
            },
            "Vinamilk": {
                "name": "Tran Tuan Anh",
                "role": "Marketing Director",
                "url": "https://www.linkedin.com/in/tran-tuan-anh-vinamilk"
            },
            "FPT Corporation": {
                "name": "Nguyen Hoang Anh",
                "role": "Head of Marketing",
                "url": "https://www.linkedin.com/in/nguyen-hoang-anh-fpt"
            },
            "Masan Group": {
                "name": "Le Hong Minh",
                "role": "Chief Marketing Officer",
                "url": "https://www.linkedin.com/in/le-hong-minh-masan"
            }
        }
        return mock_leads.get(company_name, {
            "name": f"Marketing Lead at {company_name}",
            "role": "Chief Marketing Officer",
            "url": f"https://www.linkedin.com/in/marketing-{company_name.lower()}"
        })

    # ========================================================================
    # SIMULATED COMPANY RESEARCH
    # ========================================================================

    def search_company(self, company_name: str) -> Optional[str]:
        """Simulate searching for company on LinkedIn"""
        logger.info(f"🔍 Searching for company: {company_name}")
        self._gaussian_delay(1, 0.5)

        mock_data = self._get_mock_company_data(company_name)
        logger.info(f"✅ Found company URL: {mock_data['url']}")
        return mock_data['url']

    def extract_company_data(self, company_url: str) -> Optional[Dict]:
        """Simulate extracting company data"""
        logger.info(f"📊 Extracting company data from {company_url}")
        self._gaussian_delay(2, 1)

        company_name = company_url.split('/company/')[-1].title()
        mock_data = self._get_mock_company_data(company_name)

        company_data = {
            'company_name': company_name,
            'industry': mock_data['industry'],
            'employee_count': mock_data['employee_count'],
            'url': company_url
        }

        logger.info(f"📈 Extracted data: {company_data}")
        return company_data

    def find_marketing_lead(self, company_url: str) -> Optional[Dict]:
        """Simulate finding marketing lead"""
        logger.info("🎯 Searching for marketing lead...")
        self._gaussian_delay(2, 1)

        company_name = company_url.split('/company/')[-1].title()
        mock_lead = self._get_mock_lead_data(company_name)

        logger.info(f"👤 Found marketing lead: {mock_lead['name']}")
        return mock_lead

    def extract_profile_data(self, profile_url: str) -> Optional[Dict]:
        """Simulate extracting profile data"""
        logger.info(f"👔 Extracting profile data from {profile_url}")
        self._gaussian_delay(1, 0.5)

        # Extract name from URL for demo
        name_from_url = profile_url.split('/in/')[-1].replace('-', ' ').title()
        mock_lead = None

        # Find matching mock data
        for company, lead in {
            "Google": {"name": "Lorraine Twohill", "role": "VP of Marketing"},
            "Microsoft": {"name": "Chris Capossela", "role": "Chief Marketing Officer"},
            "Apple": {"name": "Tor Myhren", "role": "Chief Marketing Officer"},
            "Amazon": {"name": "Jill Soley", "role": "VP of Marketing"},
            "Meta": {"name": "Marne Levine", "role": "Chief Business Officer"}
        }.items():
            if lead['name'].lower().replace(' ', '-') in profile_url.lower():
                mock_lead = lead
                break

        if not mock_lead:
            mock_lead = {"name": name_from_url, "role": "Chief Marketing Officer"}

        profile_data = {
            'name': mock_lead['name'],
            'role': mock_lead['role'],
            'url': profile_url
        }

        logger.info(f"📋 Extracted profile: {profile_data}")
        return profile_data

    # ========================================================================
    # EXTERNAL API INTEGRATION (Hunter.io)
    # ========================================================================

    def get_email_from_hunter(self, name: str, domain: str) -> Optional[str]:
        """Mock Hunter.io API call"""
        api_key = os.getenv('HUNTER_API_KEY')

        if not api_key:
            logger.warning("HUNTER_API_KEY not set - skipping email lookup")
            return None

        logger.info(f"🔍 Looking up email for {name} at {domain}")
        self._gaussian_delay(1, 0.5)

        # Mock email generation
        first_name = name.split()[0].lower()
        domain_clean = domain.replace('www.', '').split('.')[0]
        mock_email = f"{first_name}@{domain_clean}.com"

        logger.info(f"📧 Found email via Hunter: {mock_email}")
        return mock_email

    # ========================================================================
    # MESSAGING & CONNECTION SIMULATION
    # ========================================================================

    def create_message(self, contact: LinkedInContact, template: Optional[str] = None) -> str:
        """Create personalized message"""
        first_name = contact.contact_name.split()[0] if contact.contact_name else "there"

        if template:
            return template.format(
                first_name=first_name,
                contact_name=contact.contact_name,
                company=contact.company,
                role=contact.contact_role,
                category=contact.category
            )

        default_message = f"""Hi {first_name},

I've been impressed by {contact.company}'s approach to marketing innovation. I'd love to connect and explore how we might collaborate on growth initiatives.

Looking forward to connecting!

Best regards"""

        return default_message

    def send_connection_request(self, profile_url: str) -> bool:
        """Simulate sending connection request"""
        logger.info(f"🤝 Sending connection request to {profile_url}")
        self._gaussian_delay(2, 1)

        # Simulate success/failure randomly
        success = random.choice([True, True, True, False])  # 75% success rate

        if success:
            logger.info("✅ Connection request sent")
            return True
        else:
            logger.warning("❌ Connect button not available")
            return False

    def send_message(self, profile_url: str, message: str) -> bool:
        """Simulate sending message"""
        logger.info(f"💬 Sending message to {profile_url}")
        self._gaussian_delay(1, 0.5)

        # Simulate typing
        logger.info("⌨️  Typing message...")
        for _ in range(len(message) // 10):
            time.sleep(0.1)

        logger.info("✅ Message sent successfully")
        return True

    # ========================================================================
    # GOOGLE SHEETS INTEGRATION
    # ========================================================================

    def setup_google_sheets(self) -> gspread.Spreadsheet:
        """Setup Google Sheets authentication"""
        try:
            creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE')

            if creds_file and os.path.exists(creds_file):
                logger.info("🔐 Using service account credentials")
                credentials = service_account.Credentials.from_service_account_file(
                    creds_file,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            else:
                logger.warning("⚠️  No Google credentials found - Google Sheets integration disabled")
                return None

            gc = gspread.authorize(credentials)

            sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'LinkedIn Leads Demo')

            try:
                spreadsheet = gc.open(sheet_name)
                logger.info(f"📊 Opened existing spreadsheet: {sheet_name}")
            except gspread.SpreadsheetNotFound:
                logger.info(f"📝 Creating new spreadsheet: {sheet_name}")
                spreadsheet = gc.create(sheet_name)

            return spreadsheet

        except Exception as e:
            logger.error(f"❌ Error setting up Google Sheets: {e}")
            return None

    def sync_to_google_sheets(self, spreadsheet: gspread.Spreadsheet):
        """Sync contacts to Google Sheets"""
        if not spreadsheet:
            logger.warning("⚠️  Google Sheets not configured - skipping sync")
            return

        try:
            logger.info(f"☁️  Syncing {len(self.contacts)} contacts to Google Sheets...")

            df = pd.DataFrame([c.to_dict() for c in self.contacts])

            columns = [
                'company', 'url', 'category', 'employee_count',
                'contact_name', 'contact_role', 'contact_email',
                'contact_method', 'status', 'timestamp', 'notes'
            ]
            df = df[[col for col in columns if col in df.columns]]

            try:
                worksheet = spreadsheet.worksheet('Leads')
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet('Leads', len(df) + 10, len(columns))

            worksheet.clear()
            set_with_dataframe(worksheet, df, include_index=False)

            logger.info("✅ Successfully synced to Google Sheets")

        except Exception as e:
            logger.error(f"❌ Error syncing to Google Sheets: {e}")

    # ========================================================================
    # MAIN WORKFLOW
    # ========================================================================

    def process_company(self, company_name: str, send_message: bool = False,
                       message_template: Optional[str] = None) -> bool:
        """Complete workflow for single company"""
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"🏢 Processing company: {company_name}")
            logger.info(f"{'='*60}")

            if self.processed_count >= self.rate_limit:
                logger.warning(f"🚫 Rate limit reached ({self.rate_limit} profiles)")
                return False

            # Step 1: Search company
            company_url = self.search_company(company_name)
            if not company_url:
                logger.error(f"❌ Failed to find company: {company_name}")
                return False

            # Step 2: Extract company data
            company_data = self.extract_company_data(company_url)
            if not company_data:
                logger.error("❌ Failed to extract company data")
                return False

            # Step 3: Find marketing lead
            lead_data = self.find_marketing_lead(company_url)
            if not lead_data:
                logger.error("❌ Failed to find marketing lead")
                return False

            # Step 4: Extract profile data
            profile_data = self.extract_profile_data(lead_data['url'])
            if not profile_data:
                logger.error("❌ Failed to extract profile data")
                return False

            # Step 5: Try to get email
            email = None
            domain = company_url.split('/company/')[-1].split('/')[0]
            if domain:
                email = self.get_email_from_hunter(profile_data['name'], f"{domain}.com")

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
                if self.send_connection_request(lead_data['url']):
                    contact.status = "Connection Sent"
                else:
                    contact.notes = "Connection request unavailable or already connected"

                self._gaussian_delay(3, 2)
                message = self.create_message(contact, message_template)

                if self.send_message(lead_data['url'], message):
                    contact.status = "Message Sent"
                else:
                    contact.notes = (contact.notes + " Message send failed").strip()

            self.contacts.append(contact)
            self.processed_count += 1

            logger.info(f"✅ Successfully processed {company_name}")
            logger.info(f"📊 Status: {contact.status}")
            logger.info(f"👤 Lead: {contact.contact_name} ({contact.contact_role})")

            return True

        except Exception as e:
            logger.error(f"💥 Error processing company {company_name}: {e}")
            return False

    def run(self, companies: List[str] = None, send_messages: bool = False,
            message_template: Optional[str] = None, skip_existing: bool = True):
        """Main execution loop - automatically finds Vietnamese companies if none provided"""
        try:
            logger.info(f"\n🚀 Starting LinkedIn automation for Vietnam...")
            logger.info("🎭 This is a DEMO version - no actual browser automation")

            # If no companies provided, search for Vietnamese companies
            if not companies:
                logger.info("📍 No companies specified - searching for companies in Vietnam...")
                companies = self.search_companies_in_vietnam(limit=10)
                logger.info(f"🏢 Will process {len(companies)} Vietnamese companies")

            # Setup Google Sheets
            try:
                spreadsheet = self.setup_google_sheets()
            except Exception as e:
                logger.error(f"❌ Failed to setup Google Sheets: {e}")
                spreadsheet = None

            # Process companies
            logger.info(f"\n🏭 Processing {len(companies)} Vietnamese companies...")

            for company in companies:
                if self.processed_count >= self.rate_limit:
                    logger.info(f"⏹️  Reached rate limit of {self.rate_limit}")
                    break

                try:
                    self.process_company(company, send_messages, message_template)
                except Exception as e:
                    logger.error(f"💥 Error in main loop for {company}: {e}")

                # Delay between companies
                self._gaussian_delay(1, 0.5)

            # Sync to Google Sheets
            if spreadsheet:
                self.sync_to_google_sheets(spreadsheet)

            # Export to CSV
            self.export_to_csv()

            logger.info(f"\n{'='*60}")
            logger.info("🎉 Vietnam lead generation complete!")
            logger.info(f"📈 Processed: {self.processed_count} companies")
            logger.info(f"👥 Marketing leads found: {len(self.contacts)}")
            logger.info(f"📍 Location: Vietnam")
            logger.info(f"{'='*60}")

        except Exception as e:
            logger.error(f"💥 Fatal error in main loop: {e}")

    def export_to_csv(self, filename: str = 'linkedin_leads_demo.csv'):
        """Export contacts to CSV file"""
        try:
            df = pd.DataFrame([c.to_dict() for c in self.contacts])
            df.to_csv(filename, index=False)
            logger.info(f"💾 Exported {len(self.contacts)} contacts to {filename}")
        except Exception as e:
            logger.error(f"❌ Error exporting to CSV: {e}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""

    # Configuration from environment
    rate_limit = int(os.getenv('RATE_LIMIT', '10'))
    send_messages = os.getenv('SEND_MESSAGES', 'false').lower() == 'true'

    # Example companies to research
    companies = [
        "Google",
        "Microsoft",
        "Apple",
        "Amazon",
        "Meta",
    ]

    # Custom message template
    message_template = """Hi {first_name},

I've been impressed by {company}'s approach to marketing innovation. I'd love to connect and explore how we might collaborate on growth initiatives.

Looking forward to connecting!

Best regards"""

    # Initialize demo automation
    automation = LinkedInAutomationDemo(
        rate_limit=rate_limit
    )

    # Run demo
    automation.run(
        companies=companies,
        send_messages=send_messages,
        message_template=message_template
    )


if __name__ == '__main__':
    main()