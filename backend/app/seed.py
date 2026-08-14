"""Seed data: rules, keywords, learning content, admin account, sample threats.

Idempotent - safe to run on every startup.
"""
from __future__ import annotations

import logging

from app.database import SessionLocal
from app.repositories.admin_repo import AuditLogRepository, KeywordRepository, RuleRepository
from app.repositories.learning_repo import LearningRepository
from app.repositories.user_repo import UserRepository
from app.security.hashing import hash_password
from app.trust_engine.defaults import DEFAULT_RULES

logger = logging.getLogger("aegis.seed")

SEED_KEYWORDS = [
    # (keyword, category, impact, severity)
    ("urgent", "urgency", -6, "high"),
    ("immediately", "urgency", -5, "high"),
    ("act now", "urgency", -6, "high"),
    ("expires today", "urgency", -8, "high"),
    ("limited time", "urgency", -4, "medium"),
    ("account will be closed", "fear", -10, "high"),
    ("account suspended", "fear", -10, "high"),
    ("suspicious activity", "fear", -8, "high"),
    ("legal action", "fear", -12, "critical"),
    ("arrest warrant", "fear", -14, "critical"),
    ("you have won", "reward", -12, "high"),
    ("claim your prize", "reward", -12, "high"),
    ("lottery", "lottery", -10, "high"),
    ("jackpot", "lottery", -10, "high"),
    ("guaranteed return", "investment", -15, "critical"),
    ("double your money", "investment", -18, "critical"),
    ("get rich quick", "investment", -15, "critical"),
    ("bitcoin", "crypto", -6, "medium"),
    ("send crypto", "crypto", -15, "critical"),
    ("wallet address", "crypto", -10, "high"),
    ("work from home", "job", -4, "medium"),
    ("no experience needed", "job", -6, "medium"),
    ("earn $", "job", -8, "high"),
    ("my love", "romance", -10, "high"),
    ("i have feelings", "romance", -8, "high"),
    ("military officer", "romance", -10, "high"),
    ("irs", "government", -12, "critical"),
    ("tax authority", "government", -10, "critical"),
    ("police department", "government", -10, "critical"),
    ("your bank", "bank", -12, "critical"),
    ("fraud department", "bank", -10, "critical"),
    ("paypal", "bank", -6, "high"),
    ("verification code", "otp", -15, "critical"),
    ("one time password", "otp", -15, "critical"),
    ("security code", "otp", -12, "critical"),
    ("your password", "password", -20, "critical"),
    ("confirm your password", "password", -20, "critical"),
    ("verify your account", "verification", -10, "high"),
    ("account verification", "verification", -10, "high"),
    ("copy of your passport", "identity", -15, "critical"),
    ("social security number", "identity", -18, "critical"),
    ("driver's license", "identity", -15, "critical"),
    ("remote access", "remote", -20, "critical"),
    ("install teamviewer", "remote", -20, "critical"),
    ("install anydesk", "remote", -20, "critical"),
    ("western union", "money", -12, "critical"),
    ("moneygram", "money", -12, "critical"),
    ("wire transfer", "money", -10, "high"),
    ("processing fee", "money", -8, "high"),
    ("trust me", "social", -8, "high"),
    ("confidential", "social", -6, "medium"),
    ("do not tell anyone", "social", -10, "high"),
]

SEED_LESSONS = [
    {
        "slug": "what-is-phishing",
        "title": "What is Phishing?",
        "category": "Basics",
        "summary": "Learn how attackers trick you into revealing passwords and money.",
        "content": (
            "Phishing is a type of social engineering where attackers pretend to be "
            "a trusted organization to steal credentials, money or personal data. "
            "It can arrive by email, SMS, chat, phone, QR code or a fake website.\n\n"
            "Attackers rely on psychological tricks: urgency, fear, authority and "
            "rewards. They want you to act before you think.\n\n"
            "A legitimate organization will never ask for your password or a "
            "one-time verification code over message.\n\n"
            "Before clicking anything, stop and verify the source through an "
            "independent channel: type the address yourself, call the official "
            "number, or check the sender address character by character."
        ),
        "example": (
            "'URGENT: Your account will be suspended unless you verify immediately: "
            "http://bit.ly/verify' - this is phishing: it creates urgency and asks "
            "you to verify through a shortened link."
        ),
        "tips": [
            "Check the sender address, not just the display name",
            "Hover over links to preview the real destination",
            "Never share one-time codes with anyone",
            "Type the official website address yourself",
        ],
        "reading_time": 5,
        "order": 1,
    },
    {
        "slug": "spotting-scam-messages",
        "title": "Spotting Scam Messages",
        "category": "Basics",
        "summary": "The language tricks used in scam SMS, WhatsApp and Telegram.",
        "content": (
            "Scam messages share common patterns. Urgency words like 'immediately' "
            "or 'last chance'. Fear tactics like 'your account will be closed' or "
            "'legal action'. Rewards that are too good to be true.\n\n"
            "Scammers ask for verification codes, passwords, remote access, gift "
            "cards or cryptocurrency - things that are irreversible once sent.\n\n"
            "Look for: unusual sender numbers, shortened links, bad grammar, "
            "requests for personal documents, and pressure to keep it secret."
        ),
        "example": (
            "'We noticed unusual activity. Reply with your OTP code now.' Real banks "
            "never ask you to send a code to them - the code is for you to type "
            "into their official app."
        ),
        "tips": [
            "Reply with 'no' if unsure - real services accept questions",
            "Search the exact wording online - scams are copied",
            "Report scam messages to your mobile operator",
        ],
        "reading_time": 6,
        "order": 2,
    },
    {
        "slug": "fake-websites",
        "title": "Fake Websites and Links",
        "category": "Web Safety",
        "summary": "How typosquatting, punycode and lookalike domains work.",
        "content": (
            "Fake websites imitate brands to steal your login. They use typosquatting "
            "('paypa1.com' instead of 'paypal.com'), punycode that replaces letters "
            "with non-ASCII characters, shortened links and direct IP addresses.\n\n"
            "Always check the domain carefully. Look for the padlock but remember: "
            "a padlock only means encryption, not that the site is legitimate.\n\n"
            "Use the AEGIS URL scanner to get an explainable Trust Score before "
            "entering any credentials."
        ),
        "example": (
            "'https://paypal-com-security-check.tk/login' imitates PayPal but the "
            "domain ends in .tk - a free TLD heavily used by scammers."
        ),
        "tips": [
            "Manually type important addresses",
            "Bookmark the real login pages you use",
            "Use a password manager that refuses to autofill on lookalikes",
        ],
        "reading_time": 5,
        "order": 3,
    },
    {
        "slug": "protecting-your-identity",
        "title": "Protecting Your Identity",
        "category": "Personal Safety",
        "summary": "Stop identity theft before it happens.",
        "content": (
            "Identity thieves collect your passport, ID number, birth date, bank "
            "statements or mother's maiden name. They use them to open accounts, "
            "take loans or empty your bank balance.\n\n"
            "Never send copies of identity documents in chat. If a job, lottery or "
            "'investment' asks for your ID card, it is almost certainly a scam.\n\n"
            "Use strong unique passwords and enable two-factor authentication "
            "everywhere you can."
        ),
        "example": (
            "'We just need a copy of your passport and bank statement to release "
            "your prize money.' No legitimate organization releases prizes this way."
        ),
        "tips": [
            "Share personal documents only on official portals",
            "Monitor your accounts for unusual activity",
            "Freeze your credit if documents are lost",
        ],
        "reading_time": 5,
        "order": 4,
    },
    {
        "slug": "qr-code-safety",
        "title": "QR Code Safety",
        "category": "Web Safety",
        "summary": "Quishing: QR codes that hide malicious links.",
        "content": (
            "QR codes are convenient but can hide anything. A scammer can place a "
            "fake QR sticker over a real payment code.\n\n"
            "Before scanning a QR code, ask: was it placed by a trusted person? "
            "After scanning, preview the link - if it looks like a login page for "
            "a bank, be suspicious.\n\n"
            "Use the AEGIS QR analyzer to decode and check the destination safely."
        ),
        "example": (
            "A QR sticker on a parking meter that links to a fake payment page "
            "collecting card details."
        ),
        "tips": [
            "Prefer official apps for payments",
            "Don't scan codes from unknown posters or emails",
            "Check the destination URL after scanning",
        ],
        "reading_time": 4,
        "order": 5,
    },
]

SEED_QUIZZES = [
    {
        "slug": "phishing-101",
        "title": "Phishing 101",
        "category": "Basics",
        "description": "Test your ability to spot phishing attempts.",
        "pass_percent": 80.0,
        "questions": [
            {
                "text": "You receive an SMS: 'Your bank card will be blocked. Verify now: http://bit.ly/xyz'. What should you do?",
                "options": ["Click the link to verify quickly", "Ignore the message and contact your bank directly",
                            "Reply with your OTP to prove you are real", "Forward it to your friends"],
                "correct_index": 1,
                "explanation": "Banks never ask you to verify through shortened links. Contact your bank using an official number.",
            },
            {
                "text": "Which of these domains is most likely a phishing site?",
                "options": ["https://www.paypal.com", "https://paypal-secure-verify.tk",
                            "https://www.amazon.com/gp/buy", "https://github.com"],
                "correct_index": 1,
                "explanation": "'secure-verify' words plus a free .tk domain are classic phishing indicators.",
            },
            {
                "text": "Is it safe to share a one-time SMS verification code with a caller from 'bank security'?",
                "options": ["Yes, they need it to protect me", "Only if they know my name",
                            "No, never share codes with anyone", "Yes, if the number looks official"],
                "correct_index": 2,
                "explanation": "Verification codes protect your account. Any real service generates and reads the code on its own system.",
            },
            {
                "text": "A lottery says you won $1,000,000 but must pay a 'processing fee' first. This is:",
                "options": ["A standard prize procedure", "A lottery scam",
                            "A legitimate tax rule", "A government program"],
                "correct_index": 1,
                "explanation": "Real prizes never require upfront fees. Money-before-reward is a universal scam pattern.",
            },
        ],
    },
    {
        "slug": "url-security",
        "title": "URL & Website Security",
        "category": "Web Safety",
        "description": "Learn to evaluate links before clicking.",
        "pass_percent": 75.0,
        "questions": [
            {
                "text": "A padlock icon in the address bar means:",
                "options": ["The site is 100% safe", "The connection is encrypted",
                            "The site is government-approved", "Your computer is virus-free"],
                "correct_index": 1,
                "explanation": "HTTPS encrypts traffic but does not prove the site is legitimate.",
            },
            {
                "text": "Which URL is a typosquat attempt?",
                "options": ["https://www.amazon.com", "https://www.amzon.com",
                            "https://aws.amazon.com", "https://www.google.com/maps"],
                "correct_index": 1,
                "explanation": "'amzon.com' is one letter short of Amazon - a classic typosquat.",
            },
            {
                "text": "What is 'quishing'?",
                "options": ["A type of fish", "QR code phishing", "A hacking tool", "A security update"],
                "correct_index": 1,
                "explanation": "Quishing uses QR codes to lead victims to fake login or payment pages.",
            },
        ],
    },
]

SEED_SCENARIOS = [
    {
        "slug": "sms-delivery-fee",
        "title": "The Delivery Fee Trap",
        "category": "Delivery",
        "difficulty": "easy",
        "content": (
            "SMS from +44 77 0000 0000:\n\n"
            "'Your parcel is held at customs. To release it, pay a £3.50 delivery "
            "fee now: http://cutt.ly/parcel-fee'"
        ),
        "options": [
            "Click the link and pay £3.50 to get my parcel",
            "Check tracking on the courier's official website first",
            "Reply with my address so they can deliver without the fee",
            "Send them a screenshot of my payment app",
        ],
        "correct_index": 1,
        "explanation": "Couriers never collect customs fees via shortened links. Real fees are paid on official tracking pages.",
        "red_flags": ["Shortened link", "Urgency fee", "Unknown number", "Money requested by SMS"],
    },
    {
        "slug": "friend-help",
        "title": "The Friend in Trouble",
        "category": "Social Engineering",
        "difficulty": "medium",
        "content": (
            "WhatsApp from your 'boss':\n\n"
            "'I'm in a meeting and my phone broke. Urgently need you to buy 5 gift "
            "cards and send me the codes. It's for a client. Keep it between us.'"
        ),
        "options": [
            "Buy the gift cards immediately - my boss is waiting",
            "Call my boss on their official number to confirm",
            "Send the codes and ask questions later",
            "Transfer the money directly instead of gift cards",
        ],
        "correct_index": 1,
        "explanation": "Gift-card requests from authority figures are a top scam pattern. Always confirm through a second channel.",
        "red_flags": ["Gift cards requested", "Urgency", "Keep it secret", "New number"],
    },
    {
        "slug": "romance-oil-rig",
        "title": "The Oil Rig Romance",
        "category": "Romance",
        "difficulty": "medium",
        "content": (
            "A new online friend says:\n\n"
            "'I am a widowed engineer on an oil rig in the Gulf. I can't access my "
            "bank account. I want to send you a gift of $20,000 - just pay the "
            "$300 transfer fee first, my love.'"
        ),
        "options": [
            "Pay the $300 to receive the $20,000",
            "Block them and report the account",
            "Send my bank details so they can transfer directly",
            "Ask them to send half first as proof",
        ],
        "correct_index": 1,
        "explanation": "The classic romance + advance-fee scam: love bomb first, then a fee before a 'gift'.",
        "red_flags": ["Emotional terms", "Remote worker story", "Upfront fee", "Crypto/wire transfer"],
    },
    {
        "slug": "gov-warrant",
        "title": "The Arrest Warrant",
        "category": "Government",
        "difficulty": "easy",
        "content": (
            "Phone call from 'Officer Miller':\n\n"
            "'This is the federal police. Your tax file is under investigation. If "
            "you don't pay $1,200 in fines within 2 hours, a warrant will be issued "
            "and you will be arrested.'"
        ),
        "options": [
            "Pay immediately to avoid arrest",
            "Hang up and verify with official government channels",
            "Share my ID number so they can check my file",
            "Ask to pay by gift card to keep it fast",
        ],
        "correct_index": 1,
        "explanation": "Real police never demand payment by phone with threats of immediate arrest.",
        "red_flags": ["Immediate arrest threat", "Payment demanded", "Impersonation of police", "Time pressure"],
    },
]

ADMIN_EMAIL = "admin@aegis.local"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@2024!"


def run_seed() -> None:
    db = SessionLocal()
    try:
        # --- rules -----------------------------------------------------------
        rules = RuleRepository(db)
        rules.upsert_defaults(DEFAULT_RULES)

        # --- keywords ----------------------------------------------------------
        keywords = KeywordRepository(db)
        existing = {k.keyword.lower() for k in _iter_keywords(db, keywords)}
        for keyword, category, impact, severity in SEED_KEYWORDS:
            if keyword.lower() not in existing:
                keywords.create({
                    "keyword": keyword, "category": category,
                    "impact": impact, "severity": severity,
                    "description": f"Seed keyword for {category} detection.",
                })

        # --- learning content ---------------------------------------------------
        learning = LearningRepository(db)
        for lesson in SEED_LESSONS:
            if not learning.get_lesson(lesson["slug"]):
                learning.add_lesson(lesson)
        for quiz_data in SEED_QUIZZES:
            if not learning.get_quiz(quiz_data["slug"], with_questions=False):
                learning.add_quiz(quiz_data, quiz_data["questions"])
        _seed_scenarios(learning)

        # --- admin user -----------------------------------------------------------
        users = UserRepository(db)
        admin = users.get_by_email(ADMIN_EMAIL)
        if not admin:
            admin = users.create(
                email=ADMIN_EMAIL, username=ADMIN_USERNAME,
                hashed_password=hash_password(ADMIN_PASSWORD),
                full_name="AEGIS Administrator",
            )
        admin.is_admin = True
        admin.is_verified = True
        users.save(admin)

        # Threat intelligence and public map reports are never fabricated during
        # setup. Remove only the old, content-addressed demonstration records.
        _purge_legacy_demo_reports(db)

        AuditLogRepository(db).add(None, "seed.completed", "system",
                                   "Seed data verified and applied.")
        db.commit()
    finally:
        db.close()


def _iter_keywords(db, repo):
    total, items = repo.list(page=1, page_size=500)
    return items


def _seed_scenarios(learning: LearningRepository) -> None:
    from app.models import SimulatorScenario

    db = learning.db
    existing = {s.slug for s in db.query(SimulatorScenario).all()}
    for scenario in SEED_SCENARIOS:
        if scenario["slug"] not in existing:
            learning.add_scenario(scenario)


def _purge_legacy_demo_reports(db) -> None:
    """Remove only the exact fake map records shipped by older AEGIS versions."""
    from sqlalchemy import delete
    from app.models import ThreatReport

    demo_content = {
        "https://secure-login-refund.info",
        "https://btc-doubler.io",
        "URGENT: your parcel is held in customs, pay the fee now",
        "https://bank-verification-alert.tk",
        "https://payparking-quick.top/pay",
        "https://courier-fee-release.xyz",
    }
    db.execute(
        delete(ThreatReport).where(
            ThreatReport.user_id.is_(None),
            ThreatReport.status == "approved",
            ThreatReport.content.in_(demo_content),
        )
    )
