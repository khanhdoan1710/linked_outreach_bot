#!/usr/bin/env python3
"""
Quick-Start Example: LinkedIn Automation
Use this to test the script with safe defaults before running at scale
"""

from linkedin_automation import LinkedInAutomation
import os
from dotenv import load_dotenv

load_dotenv()


def test_mode():
    """
    TEST MODE: Safe defaults for first run
    - Single company
    - No messages (just connection requests)
    - Headless off (see what's happening)
    - Low rate limit
    """
    print("\n" + "="*70)
    print("LinkedIn Automation - TEST MODE")
    print("="*70)
    print("\nSettings:")
    print("  • Companies: 1 (test)")
    print("  • Send Messages: No (connection requests only)")
    print("  • Headless: Off (you'll see the browser)")
    print("  • Rate Limit: 1")
    print("\nThe script will:")
    print("  1. Prompt for LinkedIn login (first time only)")
    print("  2. Save session cookies for future runs")
    print("  3. Search for the test company")
    print("  4. Extract company data")
    print("  5. Find marketing lead")
    print("  6. Send connection request")
    print("  7. Export results to CSV + Google Sheets")
    print("\n" + "="*70 + "\n")
    
    automation = LinkedInAutomation(
        headless=False,        # Show browser
        rate_limit=1,          # Just 1 company
        use_cookies=True       # Save session
    )
    
    # Test with single company
    test_companies = ["Google"]
    
    automation.run(
        companies=test_companies,
        send_messages=False,   # Connection requests only
        message_template=None
    )
    
    print("\n✓ Test complete! Check:")
    print("  • linkedin_leads.csv (local backup)")
    print("  • Google Sheets 'LinkedIn Leads'")
    print("  • linkedin_automation.log (detailed log)")


def production_mode():
    """
    PRODUCTION MODE: Full automation with messages
    - Multiple companies
    - Send messages
    - Configurable from .env
    """
    print("\n" + "="*70)
    print("LinkedIn Automation - PRODUCTION MODE")
    print("="*70)
    
    # Read from .env
    headless = os.getenv('HEADLESS', 'true').lower() == 'true'
    rate_limit = int(os.getenv('RATE_LIMIT', '10'))
    send_messages = os.getenv('SEND_MESSAGES', 'false').lower() == 'true'
    
    print(f"\nSettings from .env:")
    print(f"  • Headless: {headless}")
    print(f"  • Rate Limit: {rate_limit} profiles")
    print(f"  • Send Messages: {send_messages}")
    print("\n" + "="*70 + "\n")
    
    automation = LinkedInAutomation(
        headless=headless,
        rate_limit=rate_limit,
        use_cookies=True
    )
    
    # Add your companies here
    companies = [
        "Google",
        "Microsoft",
        "Apple",
        "Amazon",
        "Meta",
        # Add more companies as needed
    ]
    
    # Custom message template
    message_template = """Hi {first_name},

I've been impressed by {company}'s innovation in {category}.

I'd love to explore potential collaboration opportunities. Would you be open to a brief conversation?

Best regards"""
    
    automation.run(
        companies=companies,
        send_messages=send_messages,
        message_template=message_template
    )


def resume_mode():
    """
    RESUME MODE: Continue from where you left off
    Useful if script was stopped or you want to process additional companies
    """
    print("\n" + "="*70)
    print("LinkedIn Automation - RESUME MODE")
    print("="*70)
    print("\nThis mode resumes processing.")
    print("The script will:")
    print("  • Load session cookies (no login needed)")
    print("  • Skip companies already marked as 'Complete'")
    print("  • Continue from where you left off")
    print("\n" + "="*70 + "\n")
    
    automation = LinkedInAutomation(
        headless=True,
        rate_limit=5,  # Conservative for resume
        use_cookies=True
    )
    
    # Add additional companies to process
    companies = [
        "Salesforce",
        "Adobe",
        "IBM",
        "Accenture",
    ]
    
    automation.run(
        companies=companies,
        send_messages=False,  # Check before enabling
        message_template=None
    )


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        print("\n" + "="*70)
        print("LinkedIn Automation - Quick Start")
        print("="*70)
        print("\nUsage: python quick_start.py [mode]")
        print("\nAvailable modes:")
        print("  test       - Safe test with 1 company (recommended first)")
        print("  prod       - Full production mode")
        print("  resume     - Continue from previous run")
        print("\nExample:")
        print("  python quick_start.py test")
        print("\n" + "="*70 + "\n")
        sys.exit(1)
    
    if mode == 'test':
        test_mode()
    elif mode == 'prod':
        production_mode()
    elif mode == 'resume':
        resume_mode()
    else:
        print(f"Unknown mode: {mode}")
        print("Use: test, prod, or resume")
        sys.exit(1)
