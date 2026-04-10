#!/usr/bin/env python3
"""
Quick-Start Demo: LinkedIn Automation
DEMO VERSION: Shows the workflow without actual browser automation
"""

from linkedin_automation_demo import LinkedInAutomationDemo
import os
from dotenv import load_dotenv

load_dotenv()


def demo_mode():
    """
    DEMO MODE: Shows the complete workflow with mock data
    - Multiple companies
    - Simulated data extraction
    - Mock messaging
    - Google Sheets export
    """
    print("\n" + "="*70)
    print("LinkedIn Automation - DEMO MODE")
    print("="*70)
    print("\n🎭 This is a demonstration - no actual browser automation")
    print("\nSettings:")
    print("  • Companies: Auto-discovered (Vietnamese companies)")
    print("  • Send Messages: Yes (simulated)")
    print("  • Rate Limit: 10")
    print("\nThe demo will simulate:")
    print("  1. Searching LinkedIn for companies in Vietnam")
    print("  2. Extracting company data (industry, employees)")
    print("  3. Finding marketing leads (CMO, VP Marketing)")
    print("  4. Looking up email addresses")
    print("  5. Sending connection requests")
    print("  6. Sending personalized messages")
    print("  7. Exporting results to CSV + Google Sheets")
    print("\n" + "="*70 + "\n")

    automation = LinkedInAutomationDemo(
        rate_limit=10
    )

    # Demo companies - Vietnamese companies
    demo_companies = [
        "Vingroup",     # Largest conglomerate in Vietnam
        "Vietcombank",  # Largest bank in Vietnam
        "Vinamilk",     # Largest dairy company in Vietnam
        "FPT Corporation", # Largest IT company in Vietnam
        "Masan Group",  # Consumer goods conglomerate
    ]

    # Custom message template
    message_template = """Hi {first_name},

I've been impressed by {company}'s innovation in the technology space.

I'd love to explore potential collaboration opportunities. Would you be open to a brief conversation?

Best regards,
[Your Name]"""

    automation.run(
        companies=None,  # Will automatically search for Vietnamese companies
        send_messages=False,  # Collect contacts only - use outreach_from_csv.py to send later
        message_template=None  # Not used in discovery mode
    )

    print("\n✓ Demo complete! Check:")
    print("  • linkedin_leads_demo.csv (local backup)")
    print("  • Google Sheets 'LinkedIn Leads Demo'")
    print("  • linkedin_automation_demo.log (detailed log)")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1].lower() == 'demo':
        demo_mode()
    else:
        print("\n" + "="*70)
        print("LinkedIn Automation - Demo")
        print("="*70)
        print("\n🎭 DEMO VERSION - No actual browser automation")
        print("\nUsage: python quick_start_demo.py demo")
        print("\nThis will run a complete simulation of the LinkedIn")
        print("automation workflow using mock data.")
        print("\n" + "="*70 + "\n")