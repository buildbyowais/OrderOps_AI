import os
import smtplib
import imaplib
import email

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv


load_dotenv()


EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")


def send_offer_email(
    customer_email,
    customer_name,
    offer,
    order_id
):
    subject = f"Order #{order_id} - Alternative Product Offer"

    body = f"""
    
Order #{order_id}
{offer["message"]}

Please reply with ACCEPT or REJECT to confirm your choice.

Thank you,
OrderOps AI
"""

    message = MIMEMultipart()

    message["From"] = f"OrderOps AI <{EMAIL_ADDRESS}>"
    message["To"] = customer_email
    message["Subject"] = subject

    message.attach(
        MIMEText(body, "plain")
    )

    with smtplib.SMTP(
        "smtp.gmail.com",
        587
    ) as server:

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_APP_PASSWORD
        )

        server.send_message(message)

    return {
        "status": "sent",
        "recipient": customer_email
    }


def check_customer_response(order_id):

    mail = imaplib.IMAP4_SSL(
        "imap.gmail.com"
    )

    mail.login(
        EMAIL_ADDRESS,
        EMAIL_APP_PASSWORD
    )

    mail.select("INBOX")

    search_query = (
        f'(UNSEEN SUBJECT '
        f'"Order #{order_id} - Alternative Product Offer")'
    )

    status, messages = mail.search(
        None,
        search_query
    )

    if status != "OK":

        mail.logout()

        return None

    email_ids = messages[0].split()

    if not email_ids:

        mail.logout()

        return None

    latest_email_id = email_ids[-1]

    status, data = mail.fetch(
        latest_email_id,
        "(RFC822)"
    )

    if status != "OK":

        mail.logout()

        return None

    raw_email = data[0][1]

    msg = email.message_from_bytes(
        raw_email
    )

    sender = msg.get("From")
    subject = msg.get("Subject")

    order_id = None

    if subject:

        try:

            order_part = subject.split(
                "Order #"
            )[1]

            order_id = int(
                order_part.split("-")[0].strip()
            )

        except (IndexError, ValueError):

            order_id = None

    body = ""

    if msg.is_multipart():

        for part in msg.walk():

            if part.get_content_type() == "text/plain":

                payload = part.get_payload(
                    decode=True
                )

                if payload:

                    body = payload.decode(
                        errors="ignore"
                    )

                break

    else:

        payload = msg.get_payload(
            decode=True
        )

        if payload:

            body = payload.decode(
                errors="ignore"
            )

    reply_body = body

    if "\nOn " in reply_body:

        reply_body = reply_body.split(
            "\nOn ",
            1
        )[0]

    lines = reply_body.splitlines()

    clean_lines = []

    for line in lines:

        if line.strip().startswith(">"):
            continue

        clean_lines.append(line)

    reply_body = "\n".join(
        clean_lines
    ).strip()

    response = reply_body.upper()

    if "REJECT" in response:

        decision = "REJECT"

    elif "ACCEPT" in response:

        decision = "ACCEPT"

    else:

        decision = "UNKNOWN"

    mail.store(
        latest_email_id,
        "+FLAGS",
        "\\Seen"
    )

    mail.logout()

    return {
        "order_id": order_id,
        "sender": sender,
        "subject": subject,
        "body": reply_body,
        "decision": decision
    }