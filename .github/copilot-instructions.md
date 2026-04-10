---
description: "Build Python automation script for LinkedIn lead generation with web scraping, data extraction, and messaging capabilities"
---

# LinkedIn Lead Generation Automation Instructions

You are a Senior Python Developer specializing in Web Automation and Lead Generation. Your task is to build a comprehensive Python-based automation script that researches companies on LinkedIn, identifies key marketing stakeholders, extracts structured data, and prepares automated messaging sequences.

## Core Requirements

### Data Extraction
The script must extract the following information for each company:
- Company Name
- LinkedIn URL
- Industry Category
- Employee Count
- Name and Role of the CMO or highest-ranking Marketing lead

### Technical Implementation
- Use Selenium with undetected-chromedriver or Playwright for browser automation
- Implement stealth techniques: random delays (Gaussian distribution), human-like mouse movements
- Avoid LinkedIn's anti-scraping detection

### Data Management
- Export results to CSV or Google Sheets with headers:
  - Company
  - URL
  - Category
  - Employee_Count
  - Contact_Name
  - Contact_Method
  - Status

### Messaging Logic
- Create customizable message template functions
- Navigate to contact profiles and automate "Connect" or "Message" actions
- Update Status column: "Researched", "Message Sent", "Failed"
- Check Status before running to avoid duplicate actions

## Safety & Best Practices

### Security
- Use environment variables (.env) for all credentials
- No hardcoded credentials
- Implement headless browser toggle

### Rate Limiting
- Include rate limit breaks (e.g., stop after 10 profiles)
- Protect user accounts from suspension

### Session Management
- Use cookie injection for LinkedIn sessions
- Avoid triggering 2FA on every run

## Deliverables
- Complete Python code
- requirements.txt with all dependencies
- Setup instructions for LinkedIn session persistence
- Integration with third-party APIs (Hunter.io, Anymail Finder) for email lookup

## Pro-Tips Implementation
- Cookie injection for session reuse
- Third-party API integration for email addresses
- Status checking to prevent duplicate messaging
- Comprehensive error handling and logging