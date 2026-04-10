#!/usr/bin/env python3
"""
Outreach helper for LinkedIn contacts discovered in linkedin_leads.csv.

Usage:
  python outreach_from_csv.py --csv linkedin_leads.csv --preview
  python outreach_from_csv.py --csv linkedin_leads.csv --execute --message-template template.txt

Default behavior is preview-only. Use --execute to perform outreach later.
"""

import argparse
import asyncio
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd
from dotenv import load_dotenv

from linkedin_automation_playwright import LinkedInAutomation, LinkedInContact

load_dotenv()

DEFAULT_MESSAGE_TEMPLATE = """Hi {first_name},

I hope you're doing well. I found your profile while researching marketing leaders at {company}, and I'd love to connect to discuss potential collaboration.

Best regards,
"""


def load_contact_file(csv_file: Path) -> pd.DataFrame:
    if not csv_file.exists():
        raise FileNotFoundError(f"Contact file not found: {csv_file}")

    df = pd.read_csv(csv_file)
    required_columns = [
        'company', 'contact_name', 'contact_role', 'contact_url', 'contact_email', 'status'
    ]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in CSV: {missing}")

    return df


def build_contact(row: pd.Series) -> LinkedInContact:
    return LinkedInContact(
        company=row.get('company', ''),
        url=row.get('url', ''),
        category=row.get('category', ''),
        employee_count=row.get('employee_count', ''),
        contact_name=row.get('contact_name', ''),
        contact_role=row.get('contact_role', ''),
        contact_url=row.get('contact_url', ''),
        contact_email=row.get('contact_email', ''),
        contact_method=row.get('contact_method', 'LinkedIn'),
        status=row.get('status', 'Researched'),
        timestamp=row.get('timestamp', ''),
        notes=row.get('notes', ''),
    )


def render_message(contact: LinkedInContact, template: str) -> str:
    first_name = contact.contact_name.split()[0] if contact.contact_name else 'there'
    return template.format(
        first_name=first_name,
        contact_name=contact.contact_name,
        company=contact.company,
        role=contact.contact_role
    )


def filter_contacts(df: pd.DataFrame, status_values: List[str]) -> pd.DataFrame:
    return df[df['status'].isin(status_values)].copy()


async def execute_outreach(
    csv_file: Path,
    message_template: str,
    send_connection: bool,
    limit: Optional[int],
    output_file: Path,
) -> None:
    df = load_contact_file(csv_file)
    candidates = filter_contacts(df, ['Researched', 'Connection Sent', 'Failed - Already Connected'])

    if limit:
        candidates = candidates.head(limit)

    if candidates.empty:
        print('No eligible contacts found for outreach.')
        return

    headless = os.getenv('HEADLESS', 'true').lower() == 'true'
    rate_limit = int(os.getenv('RATE_LIMIT', str(len(candidates))))
    use_cookies = os.getenv('USE_COOKIES', 'true').lower() == 'true'

    async with LinkedInAutomation(headless=headless, rate_limit=rate_limit, use_cookies=use_cookies) as automation:
        if use_cookies and not await automation._load_session():
            print('No saved LinkedIn session found. Please log in manually.')
            await automation.login_manual()

        print(f'Processing {len(candidates)} contacts for outreach...')

        for index, row in candidates.iterrows():
            contact = build_contact(row)
            if not contact.contact_url:
                print(f'Skipping {contact.contact_name} ({contact.company}) - missing contact_url')
                continue

            message = render_message(contact, message_template)
            print(f'Outreach preview for {contact.contact_name} at {contact.company}:')
            print('---')
            print(message)
            print('---\n')

            success = await automation.outreach_contact(
                profile_url=contact.contact_url,
                message=message,
                send_connection=send_connection,
            )

            if success:
                df.at[index, 'status'] = 'Message Sent'
                df.at[index, 'notes'] = 'Outreach executed successfully'
            else:
                df.at[index, 'status'] = 'Outreach Failed'
                df.at[index, 'notes'] = 'Outreach execution failed or blocked'

        df.to_csv(output_file, index=False)
        print(f'Updated outreach results written to: {output_file}')


def preview_outreach(csv_file: Path, message_template: str, limit: Optional[int]) -> None:
    df = load_contact_file(csv_file)
    candidates = filter_contacts(df, ['Researched', 'Connection Sent', 'Failed - Already Connected'])

    if limit:
        candidates = candidates.head(limit)

    if candidates.empty:
        print('No eligible contacts found for preview.')
        return

    print(f'Previewing outreach for {len(candidates)} contacts...')
    print('---\n')

    for _, row in candidates.iterrows():
        contact = build_contact(row)
        message = render_message(contact, message_template)
        print(f'Contact: {contact.contact_name} ({contact.company})')
        print(f'Profile: {contact.contact_url}')
        print('Message draft:')
        print(message)
        print('---\n')

    print('Preview complete. Use --execute to perform outreach.')


def load_template(template_path: Optional[Path]) -> str:
    if template_path and template_path.exists():
        return template_path.read_text(encoding='utf-8')
    return DEFAULT_MESSAGE_TEMPLATE


def parse_args():
    parser = argparse.ArgumentParser(description='Outreach helper for LinkedIn contact CSVs')
    parser.add_argument('--csv', type=Path, default=Path('linkedin_leads.csv'), help='Contact CSV file (auto-detects demo version)')
    parser.add_argument('--template', type=Path, help='Message template file')
    parser.add_argument('--preview', action='store_true', help='Preview drafted messages only')
    parser.add_argument('--execute', action='store_true', help='Perform outreach using LinkedIn')
    parser.add_argument('--send-connection', action='store_true', help='Send connection request before messaging')
    parser.add_argument('--limit', type=int, help='Limit number of contacts to process')
    parser.add_argument('--output', type=Path, default=Path('linkedin_leads_outreach.csv'), help='Output CSV file for outreach results')
    args = parser.parse_args()
    
    # Auto-detect CSV file if default not found
    if not args.csv.exists():
        demo_csv = Path('linkedin_leads_demo.csv')
        if demo_csv.exists():
            args.csv = demo_csv
    
    return args


def main():
    args = parse_args()
    template = load_template(args.template)

    if args.execute:
        asyncio.run(
            execute_outreach(
                csv_file=args.csv,
                message_template=template,
                send_connection=args.send_connection,
                limit=args.limit,
                output_file=args.output,
            )
        )
    else:
        preview_outreach(args.csv, template, args.limit)


if __name__ == '__main__':
    main()
