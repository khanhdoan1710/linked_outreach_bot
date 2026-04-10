# LinkedIn Company Research & Lead Generation Automation
## Complete Setup & Usage Guide

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Google Sheets Setup](#google-sheets-setup)
4. [LinkedIn Session & Cookies](#linkedin-session--cookies)
5. [Configuration](#configuration)
6. [Running the Script](#running-the-script)
7. [Safety & Best Practices](#safety--best-practices)
8. [Troubleshooting](#troubleshooting)

---

## ⚡ Quick Start

```bash
# 1. Clone/setup project
git clone <repo>
cd linkedin-automation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env
# Edit .env with your settings

# 4. Setup Google Sheets (see section below)

# 5. Run the script (will prompt for LinkedIn login on first run)
python linkedin_automation.py
```

---

## 📦 Installation

### Prerequisites
- Python 3.8+
- Chrome/Chromium browser (latest version)
- Google account (for Sheets integration)
- LinkedIn account (with proper credentials)

### Step 1: Clone Repository
```bash
git clone <your-repo> linkedin-automation
cd linkedin-automation
```

### Step 2: Create Virtual Environment
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

This will install:
- **Selenium & undetected-chromedriver**: For stealth browser automation
- **Google Sheets APIs**: For live data syncing
- **Pandas**: For data processing
- **Requests & BeautifulSoup**: For API calls and HTML parsing
- **Python-dotenv**: For environment variable management

### Step 4: Verify Installation
```bash
python -c "import selenium; import gspread; print('✓ All dependencies installed')"
```

---

## 📊 Google Sheets Setup

### Option A: Service Account (Recommended for Automation)

**Best for:** Running unattended scripts, no interaction needed

#### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a Project" → "New Project"
3. Name it (e.g., "LinkedIn Automation")
4. Click "Create"

#### Step 2: Enable Google Sheets API
1. In the Cloud Console, search for "Google Sheets API"
2. Click "Google Sheets API"
3. Click "Enable"
4. Wait for it to be enabled (should see blue "Enabled" button)

#### Step 3: Create Service Account
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in:
   - Service Account Name: `linkedin-automation`
   - Description: `LinkedIn lead automation`
4. Click "Create and Continue"
5. Grant Basic Editor role (or create custom role with Sheets permissions)
6. Click "Continue" → "Done"

#### Step 4: Create JSON Key
1. Click the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Select "JSON"
5. Click "Create" - a JSON file will download

**Important:** This file contains credentials - **keep it secure**!

#### Step 5: Configure Environment
```bash
# Copy the downloaded JSON to your project
cp ~/Downloads/linkedin-automation-xxxxx.json ./service-account-key.json

# Update .env
GOOGLE_CREDENTIALS_FILE=./service-account-key.json
GOOGLE_SHEET_NAME=LinkedIn Leads
GOOGLE_USER_EMAIL=your-email@gmail.com
```

#### Step 6: Share Spreadsheet with Service Account
The script will create a sheet automatically. Share it with your service account email (found in the JSON file under `client_email`).

---

### Option B: OAuth2 (User-Based Authentication)

**Best for:** Personal use, interactive setup

#### Step 1: Create OAuth Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to "APIs & Services" → "Credentials"
4. Click "Create Credentials" → "OAuth client ID"
5. Select "Desktop application"
6. Download the JSON and save as `credentials.json` in project root

#### Step 2: Update .env
```bash
# Leave GOOGLE_CREDENTIALS_FILE empty - it will use credentials.json
GOOGLE_CREDENTIALS_FILE=
```

#### Step 3: First Run
- Script will open browser asking for Google account permission
- Click "Allow" to give access
- Token will be saved for future use

---

## 🔐 LinkedIn Session & Cookies

### The Problem
- Typing password every run is slow and looks bot-like
- LinkedIn may trigger 2FA repeatedly
- Session management is critical for undetected automation

### The Solution: Cookie Injection

#### How It Works
1. **First Run:** You log in manually once
2. **Script Saves:** Browser session cookies to `.linkedin_session.pkl`
3. **Future Runs:** Script injects cookies, bypassing login
4. **No 2FA:** Cookies include 2FA bypass tokens

#### Step 1: First Run Setup
```bash
# Make sure .env has:
USE_COOKIES=true
HEADLESS=false  # Show browser during login

python linkedin_automation.py
```

When the script starts:
- Browser window opens to LinkedIn login
- **Login normally** (2FA if prompted)
- Script detects successful login
- **Automatically saves session cookies**

#### Step 2: Future Runs
```bash
# Now you can use headless mode (faster, no window)
# Update .env:
HEADLESS=true
USE_COOKIES=true

python linkedin_automation.py
```

The script will:
- Load cookies from `.linkedin_session.pkl`
- Skip login entirely
- Start scraping immediately

#### Session Cookie Refresh
Cookies expire after ~30-90 days. If login fails:
```bash
# Delete old session
rm .linkedin_session.pkl

# Run again - script will prompt for manual login
python linkedin_automation.py
```

#### Security Notes
- `.linkedin_session.pkl` contains session data - **keep secure**
- Add to `.gitignore`:
  ```
  .linkedin_session.pkl
  .env
  service-account-key.json
  credentials.json
  ```
- Never commit these files to version control

---

## ⚙️ Configuration

### .env Variables Explained

#### Browser Settings
```bash
# Run in headless mode (faster, no window)
HEADLESS=true

# Max profiles per run (safety limit)
# LinkedIn's unofficial limit: ~10-25 per day
# Start low and increase gradually
RATE_LIMIT=10

# Use saved session cookies
USE_COOKIES=true
```

#### Messaging
```bash
# Automatically send messages (risky - start with false)
# false = only send connection requests
# true = send connection + message
SEND_MESSAGES=false
```

#### Google Sheets
```bash
# Sheet name (will be created if doesn't exist)
GOOGLE_SHEET_NAME=LinkedIn Leads

# Credentials file path
GOOGLE_CREDENTIALS_FILE=./service-account-key.json

# Your email (for notifications, sharing)
GOOGLE_USER_EMAIL=your-email@gmail.com
```

#### External APIs (Optional)
```bash
# Hunter.io - finds email addresses from names
# Free plan: 50/month, paid plans available
# Sign up: https://hunter.io/
HUNTER_API_KEY=your_key_here
```

---

## 🚀 Running the Script

### Basic Usage

#### Edit Companies List
```python
# In linkedin_automation.py, change this section:

companies = [
    "Google",
    "Microsoft",
    "Apple",
    # Add more companies
]
```

#### Run Script
```bash
python linkedin_automation.py
```

**Output:**
- Logs printed to console + saved to `linkedin_automation.log`
- Contacts exported to `linkedin_leads.csv` (backup)
- Data synced to Google Sheets in real-time

#### Check Results
- **CSV File:** `linkedin_leads.csv` (local backup)
- **Google Sheets:** Open the sheet shared with you
- **Log:** `linkedin_automation.log` (for debugging)

### Advanced Usage

#### Custom Message Template
```python
custom_template = """Hi {first_name},

I've been following {company}'s growth in the {category} space. 
I think we could create significant value together.

Are you open to a brief conversation this week?

Best,
[Your Name]
{contact_role}"""

automation.run(
    companies=companies,
    send_messages=True,
    message_template=custom_template
)
```

#### Partial Processing
```python
# Resume from specific company
companies = ["Google", "Microsoft", "Apple"]

automation = LinkedInAutomation(
    headless=True,
    rate_limit=5,  # Only 5 profiles
    use_cookies=True
)

automation.run(companies=companies[:2])  # Only Google, Microsoft
```

#### Disable Cookies (Force Fresh Login)
```bash
# Clear cookies and login fresh
rm .linkedin_session.pkl

# .env:
USE_COOKIES=false
HEADLESS=false

python linkedin_automation.py
```

---

## 🛡️ Safety & Best Practices

### LinkedIn Rate Limiting Guidelines

**Daily Limits** (informal, based on community reports):
- 5-10 connection requests: **Very Safe**
- 10-25 requests: **Safe** (with delays)
- 25-50 requests: **Risky** (may trigger warnings)
- 50+ requests: **Dangerous** (high ban risk)

**Best Practices:**
```python
# Conservative settings for safety
RATE_LIMIT=5          # Max 5 profiles per run
HEADLESS=true         # Run unattended
USE_COOKIES=true      # Reuse session
SEND_MESSAGES=false   # Start without messages
```

### Stealth Measures (Built-In)

The script already includes:
- ✅ **Undetected-chromedriver**: Bypasses LinkedIn bot detection
- ✅ **Gaussian delays**: Human-like wait times (2-4 seconds average)
- ✅ **Random mouse movements**: Simulates real user behavior
- ✅ **User agent rotation**: Different browser signatures
- ✅ **Session persistence**: Avoids suspicious re-logins

### What NOT to Do
- ❌ Don't run multiple instances simultaneously
- ❌ Don't process >25 profiles in one day
- ❌ Don't immediately message after connection (wait 24h)
- ❌ Don't use the same message for everyone (looks automated)
- ❌ Don't scrape without rate limiting

### Resume Strategy
If script stops or you stop it manually:
```bash
# Check status of contacts
# Edit Google Sheet to mark "Researched" as "Paused"

# Rerun later with updated rate limit
RATE_LIMIT=3  # Lower limit to stay safe

python linkedin_automation.py
```

---

## 🐛 Troubleshooting

### Issue: "Chrome not found" / Browser won't start

**Solution:**
```bash
# Install Chrome/Chromium
# macOS:
brew install --cask google-chrome

# Linux (Ubuntu/Debian):
sudo apt-get install chromium-browser

# Windows: Download from https://www.google.com/chrome/
```

### Issue: Login keeps failing

**Solution:**
```bash
# Clear all cookies and try fresh login
rm .linkedin_session.pkl

# Use non-headless to see browser
HEADLESS=false

# Check logs for specific error
tail -f linkedin_automation.log
```

### Issue: Google Sheets authentication fails

**For Service Account:**
- Verify JSON file path in .env
- Confirm file exists and is valid JSON: `cat service-account-key.json | jq .`
- Share the Google Sheet with the service account email

**For OAuth2:**
- Delete `token.pickle` if it exists
- Rerun to get new permissions
- Ensure credentials.json is valid

### Issue: Can't find marketing lead / No results

**Solution:**
- Company may be too small or new
- LinkedIn may have changed the DOM selectors
- Check `linkedin_automation.log` for specific errors
- Manually verify company exists on LinkedIn

### Issue: Getting rate limited / "Please slow down"

**Solution:**
```bash
# Increase delays and reduce rate limit
RATE_LIMIT=3        # Only 3 profiles per run
HEADLESS=false      # See what's happening

# Add manual delays between runs
# Run script, wait 2 hours, run again
```

### Issue: Messages not sending

**Common Causes:**
1. Not 1st-degree connection (connect first, message later)
2. LinkedIn has stricter message restrictions for new connections
3. Rate limit exceeded

**Solution:**
```bash
SEND_MESSAGES=false  # Disable messaging
# Manually send messages after 24-48 hours
```

### View Detailed Logs

```bash
# Show last 50 lines of log
tail -n 50 linkedin_automation.log

# Follow log in real-time
tail -f linkedin_automation.log

# Search for errors
grep ERROR linkedin_automation.log
```

---

## 📈 Scaling Up (After Testing)

Once you've verified the script works safely:

### Phase 1: Basic (Week 1)
```bash
RATE_LIMIT=5
SEND_MESSAGES=false
# Run: Once per day
# Target: 5 connections/day = 35/week
```

### Phase 2: Moderate (Week 2-3)
```bash
RATE_LIMIT=10
SEND_MESSAGES=false  # Still wait 24-48h before messaging
# Run: Once per day
# Target: 10 connections/day = 70/week
```

### Phase 3: Messaging (Week 4+)
```bash
RATE_LIMIT=5
SEND_MESSAGES=true   # Now enabled, with custom templates
# Run: Once every other day
# Target: 25 connections + messages/week
```

---

## 🔗 Additional Resources

- **LinkedIn ToS:** https://www.linkedin.com/legal/user-agreement
- **Hunter.io:** https://hunter.io/ (Email finding)
- **Google Cloud Setup:** https://console.cloud.google.com/
- **Undetected Chromedriver:** https://github.com/ultrafunkamsterdam/undetected-chromedriver
- **Selenium Docs:** https://selenium.dev/

---

## ✅ Checklist Before First Run

- [ ] Python 3.8+ installed
- [ ] Virtual environment created & activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created and configured
- [ ] Google Sheets API enabled
- [ ] Service account JSON or OAuth2 credentials set up
- [ ] Chrome/Chromium browser installed
- [ ] LinkedIn account ready (not locked)
- [ ] Companies list added to script
- [ ] `.gitignore` updated with sensitive files

---

## 📞 Support

For issues, check:
1. `linkedin_automation.log` for detailed errors
2. This guide's troubleshooting section
3. Browser console (F12) for JavaScript errors
4. Google Cloud console for API issues

---

**Last Updated:** April 2026  
**Python Version:** 3.8+  
**Maintainer Notes:** Update selectors if LinkedIn changes DOM structure
