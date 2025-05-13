import os
import sys
import argparse
import logging
from twilio.rest import Client

def parse_args():
    parser = argparse.ArgumentParser(
        description="Update Twilio Voice webhook URL for a phone number."
    )
    parser.add_argument(
        "--phone-number", "-p",
        required=True,
        help="Phone number."
    )
    parser.add_argument(
        "--webhook-url", "-w",
        required=True,
        help="Public URL for Twilio webhook."
    )
    parser.add_argument(
        "--method", "-m",
        choices=["POST", "GET"],
        default="POST",
        help="HTTP method Twilio should use when requesting the webhook."
    )
    return parser.parse_args()

def main():
    args = parse_args()

    # Load credentials from environment
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token  = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        logging.error("Environment variables TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set.")
        sys.exit(1)

    client = Client(account_sid, auth_token)

    # Find the incoming phone number resource
    numbers = client.incoming_phone_numbers.list(phone_number=args.phone_number)
    if not numbers:
        logging.error(f"No incoming phone number found matching {args.phone_number}.")
        sys.exit(1)

    incoming_number = numbers[0]

    # Update the Voice webhook settings
    incoming_number.update(
        voice_url=args.webhook_url,
        voice_method=args.method
    )

    print(f"Updated {args.phone_number} Voice webhook : {args.webhook_url} ({args.method})")

if __name__ == "__main__":
    main()
