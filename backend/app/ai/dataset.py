"""Built-in labeled dataset used to train the on-device classifiers.

The dataset is intentionally broad so the models generalize to real-world
messages without any external/paid data. Admins can retrain on additional
labeled scans from the platform.
"""
from __future__ import annotations

SCAM_TEXTS: list[str] = [
    # SMS / OTP scams
    "URGENT: Your account has been suspended. Verify immediately to reactivate: http://bit.ly/verify-account",
    "Your bank has detected suspicious activity. Confirm your identity now or your card will be blocked. http://short.url",
    "Your verification code is 482913. Do not share this code with anyone.",
    "We could not deliver your package. Please confirm your address and pay 2.99 delivery fee: http://tiny.cc/track",
    "Your Apple ID was used to sign in on a new device. If this was not you, secure your account now.",
    "PayPal: your payment of $499.00 was declined. Update your payment method immediately.",
    "DHL: your parcel is held in customs. Pay the release fee of $3.50 to complete delivery.",
    "Your Netflix account has been put on hold due to a payment problem. Renew membership now.",
    "Microsoft: unusual sign-in activity on your account. We locked your account temporarily.",
    "You have a pending refund of $289. Click here to claim it within 24 hours.",
    # Lottery / prizes
    "Congratulations! You have been selected as the winner of our lottery. Claim your prize of $1,000,000 now.",
    "You won a free iPhone 15! Submit your details and a small shipping fee to receive it.",
    "Mega Millions draw 8899: your ticket has won the jackpot. Contact our claims agent for payout.",
    "You have won a cash prize of 500000 USD. To release funds, pay a small processing fee.",
    # Investment / crypto
    "Guaranteed 300% returns on your investment in 30 days. Limited slots, act now!",
    "Our crypto trading signals have a 97% win rate. Minimum deposit of $100 required.",
    "Double your Bitcoin in 24 hours. Send BTC to this wallet and receive twice as much back.",
    "Forex masterclass: earn passive income of $5000/month with zero experience.",
    "Invest in our oil and gas project, guaranteed profit of 45% in 3 months.",
    "We are giving away 2x your BNB as part of our anniversary event. Send now.",
    # Job scams
    "Earn $300 per day working from home, no experience needed. Data entry job, apply today.",
    "We are hiring online assistants, get paid $25 per task. Sign up now for free.",
    "Your application for the remote position was successful. Please pay a refundable training fee.",
    "Work from home and earn easy money by completing simple tasks. Start immediately.",
    # Romance
    "Hello my love, I am a military officer deployed overseas. I need your help to receive my inheritance. Please trust me.",
    "I have feelings for you. I will send you a gift, just pay the customs fee of $200 first.",
    "My dear, I am stuck in a foreign country and need money for a plane ticket to meet you.",
    "I am a doctor on an oil rig, I cannot access my bank account, please lend me money until I return.",
    # Government / tax
    "IRS: Your tax return has errors and you owe $1,200. Pay immediately to avoid legal action or arrest.",
    "Social Security Administration: your number has been compromised. Call us immediately to protect your benefits.",
    "Your national insurance number has been used fraudulently. We will send the police to your home unless you verify now.",
    "Court: failure to appear will result in a warrant. Pay your fine through the attached link today.",
    # Bank / payment fraud
    "Visa: A charge of $749.00 was attempted on your card. Confirm or dispute: http://secure-paypal-verify.com",
    "Your account will be debited $1,000 for your subscription renewal. Cancel here.",
    "We noticed a new login to your online banking from an unknown device. Confirm this was you.",
    "Refund of $350 is waiting for you from your electricity provider. Provide card details to receive it.",
    # Fake payment requests
    "I am your manager and need you to purchase gift cards urgently and send me the codes. Do it now.",
    "This is the CEO. I need you to wire $5,000 to this account today and keep it confidential.",
    "Your invoice of $2,400 is overdue. Pay now to avoid late fees and collection agencies.",
    "Complete your payment to release your order. Click the link below.",
    # General phishing
    "Dear user, your email storage is 98% full. Upgrade your account to avoid losing access: http://mail-upgrade-secure.net",
    "Your domain will expire in 24 hours. Renew immediately to avoid losing it: http://domain-renewal-service.tk",
    "We updated our privacy policy. You must verify your account within 48 hours or it will be closed.",
    "Someone requested a password reset. If this was not you, click here to secure your account.",
    "Your antivirus subscription has expired. Renew now for 50% off, limited time only.",
    "Claim your government stimulus payment by providing your banking details here.",
]

LEGIT_TEXTS: list[str] = [
    "Your appointment with Dr. Miller is confirmed for Tuesday at 3 PM. Reply R to reschedule.",
    "Your order #48291 has shipped and will arrive on Thursday. Track it here.",
    "This is your monthly statement from GreenBank. Your balance is $1,204.87.",
    "Thank you for shopping with us! Your receipt is attached.",
    "Two-factor authentication is now enabled on your account. You will receive a code each time you sign in.",
    "The meeting has been moved to 10 AM. Please update your calendar.",
    "Your package was delivered to the mailbox at 5:42 PM. Enjoy!",
    "Remember to bring your ID to the exam center tomorrow at 9:00 AM.",
    "Your library book is due on Friday. You can renew it online.",
    "Welcome to our newsletter! Here is what we shipped this week.",
    "Your doctor's office confirms your lab results are available in the patient portal.",
    "We received your support ticket #1290 and will respond within 24 hours.",
    "Your password was changed successfully. If this was not you, contact support immediately.",
    "The school bus will be 10 minutes late this afternoon due to traffic.",
    "Your electricity bill for March is $86.50. Autopay is scheduled for the 15th.",
    "Here is the recipe you asked for. Let me know how it turns out!",
    "Reminder: Team standup is at 9:30 AM. Please join the usual video link.",
    "Your gym membership renews on the 1st of next month at $29.99/month.",
    "The software update will be installed tonight after 11 PM. No action needed.",
    "Thanks for confirming. The documents are ready for pickup at reception.",
    "Your application was received and is under review. We will contact you by email.",
    "Flight BA284 departs at 18:40 from Gate 14. Check-in closes 45 minutes before.",
    "Today's lunch special: grilled chicken salad with lemon dressing.",
    "The invoice for last month's catering is attached for your records.",
    "Weather advisory: heavy rain expected tonight, drive carefully.",
    "Your coffee order is ready for pickup at the counter.",
]

# For URL classification
SCAM_URLS: list[str] = [
    "http://paypa1-secure-login.com/verify",
    "https://paypal-account-verify.tk/login",
    "http://www.bankofamerica.security-check.net/",
    "https://amazon-giftcard-redeem.top/redeem",
    "http://login-appleid-icloud.com/",
    "https://get-rich-quick-investments.xyz/start",
    "http://free-bitcoin-doubler.io/",
    "https://bitcoin-mixer-tumbler.xyz/",
    "http://secure-payment-confirmation.top/",
    "https://netflix-update-billing.com/confirm",
    "http://update-your-account-info.ga/",
    "https://refund-center-2024.info/claim",
    "http://admin-login-portal.net/",
    "https://online-jobs-earn-money.biz/apply",
    "http://www.microsoft-support-alert.info/",
    "https://paypal.com.verify-account.cn/login",
    "http://192.168.1.25/login",
    "https://42.113.87.5/secure/banking",
    "http://steam-community.gift-card.site/",
    "https://crypto-exchange-signup.xyz/register",
]

LEGIT_URLS: list[str] = [
    "https://www.paypal.com/us/home",
    "https://github.com/features",
    "https://www.python.org/downloads/",
    "https://fastapi.tiangolo.com/",
    "https://www.google.com/maps",
    "https://www.wikipedia.org/",
    "https://mozilla.org/en-US/",
    "https://www.amazon.com/",
    "https://stackoverflow.com/questions",
    "https://www.youtube.com/watch",
    "https://developer.mozilla.org/en-US/docs/Web",
    "https://www.reddit.com/r/python/",
    "https://www.bbc.com/news",
    "https://www.reuters.com/technology/",
    "https://www.nasa.gov/",
    "https://www.postgresql.org/docs/",
    "https://www.docker.com/products/docker-desktop/",
    "https://docs.python.org/3/library/",
    "https://www.openstreetmap.org/",
    "https://pypi.org/project/httpx/",
]


def labeled_text_pairs() -> list[tuple[str, int]]:
    return [(t, 1) for t in SCAM_TEXTS] + [(t, 0) for t in LEGIT_TEXTS]


def labeled_url_pairs() -> list[tuple[str, int]]:
    return [(u, 1) for u in SCAM_URLS] + [(u, 0) for u in LEGIT_URLS]
