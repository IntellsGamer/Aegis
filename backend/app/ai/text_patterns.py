"""Pattern knowledge base used by the text scanner.

Each entry maps to a finding `code` that the trust engine understands.
Patterns are also stored/editable as `keywords` in the database (admin panel).
"""
from __future__ import annotations

import re
import unicodedata
from typing import Pattern

# Persian messages are routinely written with a mixture of Arabic and Persian
# code points (for example ي/ی and ك/ک), optional diacritics and half spaces.
# Normalize only for matching: the original submitted content remains the
# evidence record shown to the user.
_PERSIAN_TRANSLATION = str.maketrans({
    "ي": "ی", "ى": "ی", "ك": "ک", "ة": "ه", "ۀ": "ه", "ؤ": "و",
    "إ": "ا", "أ": "ا", "ٱ": "ا", "ـ": "", "\u200c": " ",
})


def normalize_persian_for_matching(value: str) -> str:
    """Normalize common Persian/Arabic presentation variants for deterministic matching."""
    normalized = unicodedata.normalize("NFKC", value or "").translate(_PERSIAN_TRANSLATION)
    return "".join(char for char in normalized if not unicodedata.category(char).startswith("M"))


# --------------------------------------------------------------------------
# Urgency / pressure
# --------------------------------------------------------------------------
URGENCY_TERMS: list[str] = [
    "urgent", "immediately", "immediate action", "act now", "right away",
    "as soon as possible", "before it's too late", "expires today",
    "last chance", "limited time", "hurry", "don't delay", "only today",
    "within 24 hours", "final notice", "respond now", "do not wait",
    "time sensitive", "urgently required", "immediately required",
    "click now", "confirm now", "verify now", "update now",
    # Persian (Farsi) urgency terms
    "فوری", "هر چه سریعتر", "بلافاصله", "الان", "همین الان",
    "امروز", "قبل از اینکه دیر شود", "آخرین فرصت", "عجله کن",
    "تأخیر نکن", "تا ۲۴ ساعت", "تا 24 ساعت", "اخطار نهایی", "همین حالا",
    "کلیک کن", "کلیک کنید", "تأیید کن", "تایید کنید", "به‌روزرسانی کنید", "بروزرسانی کن",
]

# --------------------------------------------------------------------------
# Fear / intimidation
# --------------------------------------------------------------------------
FEAR_TERMS: list[str] = [
    "account will be closed", "account suspended", "account deactivated",
    "account will be locked", "your account is on hold", "temporarily blocked",
    "suspicious activity", "unusual activity", "security breach",
    "your account has been compromised", "unauthorized access",
    "legal action", "lawsuit", "arrest warrant", "police will",
    "fbi", "interpol", "tax fraud", "penalty", "fine will be imposed",
    "criminal charges", "you will be prosecuted", "bail", "warrant",
    "freeze your assets", "seize your account", "identity theft has been detected",
    "violation of", "terminated", "permanently suspended",
    # Persian (Farsi) fear terms
    "حساب شما مسدود خواهد شد", "حساب شما مسدود می‌شود", "حساب شما مسدود میشود", "حساب شما تعلیق شد", "حساب شما غیرفعال شد",
    "حساب شما قفل خواهد شد", "حساب شما در حالت تعلیق", "موقتاً مسدود شد",
    "فعالیت مشکوک", "فعالیت غیرعادی", "نفوذ امنیتی",
    "حساب شما در معرض خطر است", "دسترسی غیرمجاز",
    "اقدام قانونی", "دعوی قضایی", "حکم دستگیری", "پلیس",
    "کلاهبرداری مالیاتی", "جریمه", "جریمه اعمال خواهد شد",
    "اتهامات جنایی", "تحت تعقیب قرار خواهید گرفت", "قرار وثیقه",
    "مسدود کردن دارایی‌ها", "توقیف حساب", "سرقت هویت",
    "نقض قوانین", "لغو شد", "به طور دائم تعلیق شد",
]

# --------------------------------------------------------------------------
# Rewards / prizes
# --------------------------------------------------------------------------
REWARD_TERMS: list[str] = [
    "you have won", "congratulations you", "winner", "winning",
    "claim your prize", "prize money", "gift card", "free gift",
    "you have been selected", "lucky winner", "jackpot", "cash prize",
    "reward of", "you are eligible", "exclusive reward", "free iphone",
    # Persian (Farsi) reward terms
    "شما برنده شدید", "تبریک", "برنده", "برنده شدن",
    "جایزه خود را دریافت کنید", "جایزه نقدی", "کارت هدیه", "هدیه رایگان",
    "شما انتخاب شده‌اید", "برنده خوش شانس", "جکپات", "جایزه نقدی",
    "پاداش", "شما واجد شرایط هستید", "پاداش اختصاصی", "آیفون رایگان",
]

# --------------------------------------------------------------------------
# Lottery
# --------------------------------------------------------------------------
LOTTERY_TERMS: list[str] = [
    "lottery", "mega millions", "powerball", "national lottery",
    "winning numbers", "lottery commission", "claims agent", "lottery ticket",
    "sweepstakes", "draw number", "bank draft",
    # Persian (Farsi) lottery terms
    "قرعه‌کشی", "بخت‌آزمایی", "لوتاری", "میلیونر",
    "اعداد برنده", "کمیسیون قرعه‌کشی", "نماینده ادعا", "بلیط قرعه‌کشی",
    "مسابقه", "شماره قرعه", "برنده شدن",
]

# --------------------------------------------------------------------------
# Investment / guaranteed returns
# --------------------------------------------------------------------------
INVESTMENT_TERMS: list[str] = [
    "guaranteed return", "guaranteed profit", "double your money",
    "triple your investment", "high returns", "risk free investment",
    "investment opportunity", "trading signals", "get rich quick",
    "passive income", "monthly income of", "minimum deposit",
    "forex expert", "investment group", "profit sharing",
    # Persian (Farsi) investment terms
    "بازگشت تضمینی", "سود تضمینی", "پول خود را دو برابر کنید",
    "سرمایه خود را سه برابر کنید", "بازده بالا", "سرمایه‌گذاری بدون ریسک",
    "فرصت سرمایه‌گذاری", "سیگنال‌های معاملاتی", "ثروتمند شدن سریع",
    "درآمد غیرفعال", "درآمد ماهانه", "حداقل واریز",
    "کارشناس فارکس", "گروه سرمایه‌گذاری", "تقسیم سود",
]

# --------------------------------------------------------------------------
# Crypto
# --------------------------------------------------------------------------
CRYPTO_TERMS: list[str] = [
    "bitcoin", "btc", "ethereum", "eth", "usdt", "tether", "dogecoin",
    "crypto wallet", "wallet address", "send crypto", "cryptocurrency",
    "mining pool", "smart contract", "defi", "airdrop", "bnb",
    # Persian (Farsi) crypto terms
    "بیت‌کوین", "بیت کوین", "اتریوم", "تتر", "دوج‌کوین",
    "کیف پول رمزارز", "آدرس کیف پول", "ارسال رمزارز", "ارز دیجیتال",
    "استخراج", "قرارداد هوشمند", "دیفای", "ایردراپ",
]

# --------------------------------------------------------------------------
# Fake jobs / work from home
# --------------------------------------------------------------------------
FAKE_JOB_TERMS: list[str] = [
    "work from home", "remote job", "data entry job", "earn from home",
    "no experience needed", "easy money", "get paid to", "salary of",
    "signing bonus", "task based payment", "click jobs", "rated task",
    "online job", "virtual assistant needed",
    # Persian (Farsi) fake job terms
    "کار در خانه", "کار از راه دور", "وارد کردن داده", "درآمد از خانه",
    "بدون نیاز به تجربه", "پول آسان", "حقوق", "پاداش",
    "پرداخت بر اساس کار", "کار کلیکی", "کار آنلاین", "دستیار مجازی",
]

# --------------------------------------------------------------------------
# Romance / relationship manipulation
# --------------------------------------------------------------------------
ROMANCE_TERMS: list[str] = [
    "my love", "my dear", "soulmate", "beautiful lady", "handsome man",
    "fall in love", "marry you", "you are the one", "military officer",
    "deployed in", "oil rig worker", "unfortunately i cannot", "please trust me",
    "my heart", "true love", "i have feelings",
    # Persian (Farsi) romance terms
    "عشق من", "جانم", "همنفس", "دوست عزیز", "همسر آینده",
    "عاشق شدن", "ازدواج با شما", "تو همانی هستی", "افسر نظامی",
    "مستقر در", "کارگر سکوی نفتی", "متاسفانه نمی‌توانم", "لطفاً به من اعتماد کن",
    "قلب من", "عشق واقعی", "من احساس دارم",
]

# --------------------------------------------------------------------------
# Government impersonation
# --------------------------------------------------------------------------
GOVERNMENT_TERMS: list[str] = [
    "irs", "internal revenue", "social security administration",
    "tax authority", "customs", "government of", "ministry of",
    "police department", "court of", "immigration", "citizenship and",
    "electoral commission", "national insurance", "department of revenue",
    # Persian (Farsi) government terms
    "سازمان مالیاتی", "اداره مالیات", "تامین اجتماعی",
    "مرجع مالیاتی", "گمرک", "دولت", "وزارت",
    "پلیس", "دادگاه", "مهاجرت", "تابعیت",
    "کمیسیون انتخابات", "بیمه ملی", "سازمان مالیات",
]

# --------------------------------------------------------------------------
# Bank impersonation
# --------------------------------------------------------------------------
BANK_TERMS: list[str] = [
    "your bank", "bank verification", "bank security team", "fraud department",
    "card services", "bank of", "visa", "mastercard", "paypal",
    "neteller", "wise", "revolut", "stripe", "debit card", "credit card",
    # Persian (Farsi) bank terms
    "بانک شما", "تاییدیه بانک", "تیم امنیتی بانک", "بخش کلاهبرداری",
    "خدمات کارت", "بانک", "ویزا", "مسترکارت", "پی پال",
    "کارت عابر بانک", "کارت اعتباری", "رمز ورود", "رمز کارت",
    "اطلاعات بانکی", "حساب بانکی", "تراکنش", "واریز", "برداشت",
]

# --------------------------------------------------------------------------
# Verification codes / passwords / credentials
# --------------------------------------------------------------------------
OTP_TERMS: list[str] = [
    "verification code", "one time password", "otp", "confirmation code",
    "security code", "activation code", "auth code", "sms code",
    "authentication code", "2fa code", "two factor code",
    "the code", "your code is", "enter the code",
    # Persian (Farsi) OTP terms
    "رمز تایید", "رمز تأیید", "رمز یکبار مصرف", "رمز یک بار مصرف", "کد تایید", "کد تأیید", "کد امنیتی",
    "کد فعال‌سازی", "کد فعال سازی", "کد احراز هویت", "کد پیامکی", "کد پویا",
    "رمز ورود شما", "کد را وارد کنید", "کد را ارسال کنید", "کد را بفرستید",
]

PASSWORD_TERMS: list[str] = [
    "your password", "enter your password", "password to confirm",
    "current password", "password reset link", "confirm your password",
    # Persian (Farsi) password terms
    "رمز عبور شما", "رمز ورود خود را وارد کنید", "رمز عبور را تایید کنید",
    "رمز عبور فعلی", "لینک بازنشانی رمز عبور", "رمز عبور خود را تایید کنید",
    "رمز ورود", "پسورد", "کلمه عبور",
]

VERIFICATION_TERMS: list[str] = [
    "verify your account", "account verification", "confirm your identity",
    "re-verify", "klick to verify", "update your account", "confirm your details",
    "validate your account", "identity confirmation",
    # Persian (Farsi) verification terms
    "حساب خود را تایید کنید", "حساب خود را تأیید کنید", "تایید حساب", "تأیید حساب", "تایید هویت", "تأیید هویت",
    "مجدداً تایید کنید", "مجدداً تأیید کنید", "برای تایید کلیک کنید", "برای تأیید کلیک کنید", "حساب خود را بروزرسانی کنید",
    "حساب خود را به‌روزرسانی کنید", "اطلاعات خود را تایید کنید", "اطلاعات خود را تأیید کنید", "احراز هویت",
]

# --------------------------------------------------------------------------
# Identity theft
# --------------------------------------------------------------------------
IDENTITY_TERMS: list[str] = [
    "copy of your passport", "national id", "driver's license",
    "id card", "social security number", "date of birth",
    "mother's maiden name", "bank statement copy", "proof of address",
    # Persian (Farsi) identity terms
    "کپی پاسپورت", "کارت ملی", "گواهینامه رانندگی",
    "کارت شناسایی", "شماره تامین اجتماعی", "تاریخ تولد",
    "نام مادر", "کپی صورت حساب بانکی", "مدارک شناسایی",
]

# --------------------------------------------------------------------------
# Remote access
# --------------------------------------------------------------------------
REMOTE_ACCESS_TERMS: list[str] = [
    "install anydesk", "install teamviewer", "download anydesk",
    "remote access", "screen share", "remote support", "allow control",
    "go to anydesk.com", "install now", "open the app and give me the code",
    # Persian (Farsi) remote access terms
    "نصب انی دسک", "نصب تیم‌ویور", "دانلود انی دسک",
    "دسترسی از راه دور", "اشتراک صفحه", "پشتیبانی از راه دور", "اجازه کنترل",
    "برو به anydesk.com", "همین حالا نصب کن", "برنامه را باز کن و کد را بده",
]

# --------------------------------------------------------------------------
# Generic manipulation / social engineering
# --------------------------------------------------------------------------
SOCIAL_ENGINEERING_TERMS: list[str] = [
    "trust me", "i'm in trouble", "emergency", "my daughter", "my son",
    "i'm stuck", "wire transfer", "western union", "moneygram",
    "i need your help", "confidential", "do not tell anyone", "secret",
    "only you can help", "kindly", "i am requesting", "be discreet",
    # Persian (Farsi) social engineering terms
    "به من اعتماد کن", "من در مشکل هستم", "اضطراری", "دخترم", "پسرم",
    "من گیر کردم", "حواله", "وایر", "مانی‌گرام",
    "به کمک شما نیاز دارم", "محرمانه", "به هیچکس نگو", "راز",
    "فقط تو می‌توانی کمک کنی", "لطفاً", "من درخواست می‌کنم",
]

# --------------------------------------------------------------------------
# Money transfer
# --------------------------------------------------------------------------
MONEY_TRANSFER_TERMS: list[str] = [
    "western union", "moneygram", "wire transfer", "send money",
    "cash app", "zelle", "venmo", "pay advance", "processing fee",
    "clearing fee", "transfer fee", "delivery fee", "tax to release",
    # Persian (Farsi) money transfer terms
    "وایر", "مانی‌گرام", "حواله", "پول بفرست", "کارت به کارت",
    "کارمزد", "کارمزد انتقال", "کارمزد تحویل", "مالیات برای آزادسازی", "هزینه فعال‌سازی", "هزینه فعال سازی",
    "واریز وجه", "مبلغ را واریز کنید", "انتقال پول",
]

# --------------------------------------------------------------------------
# Legitimate markers (positive signals)
# --------------------------------------------------------------------------
LEGIT_SIGNALS: list[str] = [
    "dear valued customer", "this is an automated notification",
    "if this email was sent to you in error", "you can safely delete",
    "contact us at support", "read our privacy policy", "unsubscribe at any time",
    # Persian (Farsi) legitimate signals
    "مشتری عزیز", "این یک اعلان خودکار است",
    "اگر این ایمیل به اشتباه برای شما ارسال شده است", "می‌توانید با خیال راحت حذف کنید",
    "با پشتیبانی تماس بگیرید", "سیاست حفظ حریم خصوصی", "در هر زمان لغو اشتراک",
]

# --------------------------------------------------------------------------
# URLs embedded in text
# --------------------------------------------------------------------------
URL_RE = re.compile(r"https?://[^\s<>'\"\]]+", re.IGNORECASE)
SHORTENER_HOSTS = {
    "bit.ly", "t.co", "tinyurl.com", "goo.gl", "is.gd", "buff.ly",
    "ow.ly", "shorturl.at", "rb.gy", "cutt.ly", "rebrand.ly", "t.ly",
    "s.id", "zurl.co", "tiny.cc", "shorte.st", "tny.im", "lnkd.in",
    "qrco.de", "taplink.cc", "onlyfans.com/f",
}
SHORTENER_RE = re.compile(
    r"https?://(?:www\.)?(?P<host>[\w.-]+)(?P<path>/[^\s]*)?", re.IGNORECASE
)

IP_ADDR_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")

# Phrase-level matchers that need word boundaries. Persian letters are Unicode
# word characters, so the same boundary logic works after normalization.
WORD_RE = re.compile(r"[a-z0-9\u0600-\u06FF']+", re.IGNORECASE)


def build_compiled(terms: list[str]) -> list[Pattern]:
    return [
        re.compile(rf"(?<!\w){re.escape(normalize_persian_for_matching(term))}(?!\w)", re.IGNORECASE)
        for term in terms
        if len(normalize_persian_for_matching(term)) > 2
    ]


# Cached compiled matchers
_URGENCY_PATTERNS = build_compiled(URGENCY_TERMS)
_FEAR_PATTERNS = build_compiled(FEAR_TERMS)
_REWARD_PATTERNS = build_compiled(REWARD_TERMS)
_LOTTERY_PATTERNS = build_compiled(LOTTERY_TERMS)
_INVESTMENT_PATTERNS = build_compiled(INVESTMENT_TERMS)
_CRYPTO_PATTERNS = build_compiled(CRYPTO_TERMS)
_FAKE_JOB_PATTERNS = build_compiled(FAKE_JOB_TERMS)
_ROMANCE_PATTERNS = build_compiled(ROMANCE_TERMS)
_GOV_PATTERNS = build_compiled(GOVERNMENT_TERMS)
_BANK_PATTERNS = build_compiled(BANK_TERMS)
_OTP_PATTERNS = build_compiled(OTP_TERMS)
_PASSWORD_PATTERNS = build_compiled(PASSWORD_TERMS)
_VERIFICATION_PATTERNS = build_compiled(VERIFICATION_TERMS)
_IDENTITY_PATTERNS = build_compiled(IDENTITY_TERMS)
_REMOTE_PATTERNS = build_compiled(REMOTE_ACCESS_TERMS)
_SOCIAL_PATTERNS = build_compiled(SOCIAL_ENGINEERING_TERMS)
_MONEY_PATTERNS = build_compiled(MONEY_TRANSFER_TERMS)
_LEGIT_PATTERNS = build_compiled(LEGIT_SIGNALS)


def match_count(patterns: list[Pattern], text: str) -> int:
    return sum(1 for p in patterns if p.search(text))


def find_matches(patterns: list[Pattern], text: str) -> list[str]:
    """Return the observed phrase, not the implementation regex."""
    matches: list[str] = []
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            observed = match.group(0).strip()
            if observed and observed not in matches:
                matches.append(observed)
    return matches


# Mentioning a bank, government, cryptocurrency, or remote work is not itself a
# threat.  These topics become meaningful scam evidence when paired with an
# attempted action, financial solicitation, pressure, or a credential request.
_ACTION_REQUEST_RE = re.compile(
    r"\b(?:click|open|visit|login|log in|sign in|verify|confirm|update|"
    r"enter|send|pay|transfer|share|download|install|reply|call)\b|"
    r"(?:کلیک(?:\s*(?:کن(?:ید)?|نمایید))?|باز\s*(?:کن(?:ید)?|نمایید)|"
    r"وارد\s*(?:کن(?:ید)?|نمایید)|(?:تایید|تأیید)\s*(?:کن(?:ید)?|نمایید)?|"
    r"احراز\s+هویت\s*(?:کن(?:ید)?|نمایید)?|ارسال\s*(?:کن(?:ید)?|نمایید)|"
    r"پرداخت\s*(?:کن(?:ید)?|نمایید)|انتقال\s*(?:دهید|کن(?:ید)?|نمایید)|"
    r"دانلود\s*(?:کن(?:ید)?|نمایید)|نصب\s*(?:کن(?:ید)?|نمایید)|"
    r"تماس\s*(?:بگیر(?:ید)?|بگیرید)|ثبت\s+نام\s*(?:کن(?:ید)?|نمایید)|"
    r"اقدام\s*(?:کن(?:ید)?|نمایید)|(?:به\s+)?روزرسانی\s*(?:کن(?:ید)?|نمایید))",
    re.IGNORECASE,
)


def has_request_context(text: str) -> bool:
    return bool(_ACTION_REQUEST_RE.search(text))


_PERSIAN_AUTHORITY_RE = re.compile(
    r"(?:سازمان\s+مالیاتی|اداره\s+مالیات|قوه\s+قضائیه|سامانه\s+ثنا|پلیس\s+فتا|"
    r"شاپرک|همراه\s*بانک|بانک\s*(?:ملی|ملت|صادرات|تجارت|پاسارگاد|سامان|پارسیان|آینده))"
)
_PERSIAN_DELIVERY_RE = re.compile(r"(?:مرسوله|بسته(?:\s+شما)?|کد\s+رهگیری|پست(?:\s+پیشتاز)?)")
_PERSIAN_WELFARE_RE = re.compile(r"(?:یارانه|سهام\s+عدالت|کالابرگ)")
_PERSIAN_PAYMENT_RE = re.compile(r"(?:کارت\s+به\s+کارت|شماره\s+کارت|کارمزد|هزینه(?:\s+فعالسازی|\s+فعال‌سازی)?|پرداخت|واریز(?:\s+وجه)?|انتقال(?:\s+(?:وجه|مبلغ))?)")
_PERSIAN_CREDENTIAL_RE = re.compile(r"(?:رمز\s*(?:عبور|ورود|یک\s*بار\s*مصرف|تایید|تأیید)|کد\s*(?:تایید|تأیید|پویا|امنیتی|پیامکی)|کارت\s+ملی)")
_PERSIAN_PRESSURE_RE = re.compile(r"(?:فوری|بلافاصله|همین\s+حالا|اخطار\s+نهایی|آخرین\s+هشدار|هشدار\s+نهایی|تا\s*24\s*ساعت|تا\s*۲۴\s*ساعت)")
# Legal-themed scam texts frequently omit a named authority but combine a case
# against the recipient with a fabricated attachment or tracking instruction.
# Requiring all of these cues avoids treating ordinary legal discussion as fraud.
_PERSIAN_LEGAL_CASE_RE = re.compile(
    r"(?:پرونده(?:\s+الکترونیک(?:ی)?)?.{0,42}?(?:بر\s+)?علیه\s+شما.{0,36}?ثبت\s+شد|"
    r"(?:بر\s+)?علیه\s+شما.{0,24}?پرونده(?:\s+الکترونیک(?:ی)?)?.{0,30}?ثبت\s+شد)"
)
_PERSIAN_LEGAL_WARNING_RE = re.compile(r"(?:آخرین\s+هشدار|هشدار\s+نهایی|ابلاغ(?:یه)?\s+فوری)")
_PERSIAN_ATTACHMENT_TRACKING_RE = re.compile(
    r"(?:رهگیری(?:\s+\S+){0,3}\s+(?:در|به)\s+پیوست|"
    r"پیوست(?:\s+را)?\s*(?:باز|مشاهده|بررسی)\s*(?:کن(?:ید)?|نمایید)?|فایل\s+پیوست)"
)
# A common account-takeover/social-engineering pretext in Persian is a familiar
# person whose card limit is allegedly full, asking the recipient to transfer
# funds to another party and promising repayment later.
_PERSIAN_CARD_LIMIT_RE = re.compile(
    r"(?:کارت(?:م|ت|ش)?\s+سقف(?:ش)?\s+پر\s+(?:شده|شد|ه)|"
    r"سقف(?:\s+کارت(?:م|ت|ش)?)?\s+پر\s+(?:شده|شد|ه))"
)
_PERSIAN_TRANSFER_DELEGATION_RE = re.compile(
    r"(?:برا|برای)\s+(?:\S+\s+){0,3}(?:جابه\s*جا|کارت\s*به\s*کارت|انتقال|واریز)\s*"
    r"(?:کن(?:ی|ید)?|بدی|بدهید|میدی|می\s*دی)"
)
_PERSIAN_DEFERRED_REPAYMENT_RE = re.compile(
    r"(?:\d{1,2})\s+به\s+بعد\s+(?:بر(?:می)?[‌\s]*گردون(?:م|یم)|پس\s*(?:می)?دم|واریز\s*(?:می)?کنم|می\s*دم)|"
    r"(?:بعداً|بعدا)\s+(?:بر(?:می)?[‌\s]*گردون(?:م|یم)|پس\s*(?:می)?دم|واریز\s*(?:می)?کنم|می\s*دم)"
)

# Additional real-world Persian scam families require tightly coupled cues rather
# than a single topical word. This keeps a real invoice, job posting, or bank
# notification from being labelled fraudulent without the coercive action.
_PERSIAN_INVOICE_RE = re.compile(r"(?:صورت\s*[\-‌]?حساب|فاکتور|بدهی\s+معوق|مبلغ\s+معوق)")
_PERSIAN_LEGAL_THREAT_RE = re.compile(r"(?:اقدام\s+(?:حقوقی|قانونی)|ارجاع\s+به\s+(?:بخش|واحد)\s+حقوقی)")
_PERSIAN_EXECUTIVE_RE = re.compile(r"(?:مدیرعامل|مدیر\s+(?:شرکت|مجموعه))")
_PERSIAN_SECRECY_RE = re.compile(r"(?:بدون\s+مشورت|به\s+کسی\s+نگو(?:یید)?|محرمانه|بین\s+خودمان)")
_PERSIAN_SUPPORT_RE = re.compile(r"(?:پشتیبانی\s+(?:مایکروسافت|فنی)|مایکروسافت|آنتی[\-‌]?ویروس)")
_PERSIAN_COMPROMISE_RE = re.compile(r"(?:فعالیت\s+مشکوک|ویروس|تغییر\s+رمز|خرید\s+غیرمجاز|ورود\s+مشکوک)")
_PERSIAN_CALLBACK_RE = re.compile(r"(?:با\s+شماره\s+[^\n]{0,28}\s+تماس\s+بگیر(?:ید)?|تماس\s+بگیر(?:ید)?\s*(?:تا|برای))")
_PERSIAN_INVESTMENT_RETURN_RE = re.compile(r"(?:ربات\s+معاملاتی|بازده\s+(?:روزانه|تضمینی)|سود\s+(?:روزانه|تضمینی)|سیگنال[‌\s]*های?\s+روزانه)")
_PERSIAN_REWARD_RE = re.compile(r"(?:قرعه[‌\s]*کشی|برنده(?:\s+شد(?:ه|ید))?|کارت\s+هدیه|جایزه)")
_PERSIAN_ADVANCE_FEE_RE = re.compile(r"(?:هزینه\s*(?:پردازش|اداری|ترخیص|ارسال\s+مجدد)|پیش[‌\s]*پرداخت|بیعانه|ودیعه|کارمزد)")
_PERSIAN_JOB_RE = re.compile(r"(?:پروفایل\s+لینکدین|حقوق\s+(?:ماهیانه|ماهانه)|فرصت\s+همکاری|نماینده\s+در\s+ایران|نقش\s+(?:مدیر|کارشناس))")
_PERSIAN_DOCUMENT_RE = re.compile(r"(?:مدارک(?:\s+شناسایی)?|اطلاعات\s+بانکی|کد\s+ملی)")
_PERSIAN_SERVICE_RE = re.compile(r"(?:مخابرات|شرکت\s+(?:گاز|برق)|بیمه(?:\s+خودرو)?)")
_PERSIAN_CUTOFF_RE = re.compile(r"(?:قطع\s+می[‌\s]*شود|پرداخت\s+نشده|معوق\s+است|منقضی\s+شده)")
_PERSIAN_BANK_LOCKOUT_RE = re.compile(r"(?:حساب\s+شما.{0,32}?(?:مسدود|فعالیت\s+غیرمجاز)|رفع\s+مسدودی|احراز\s+هویت)")
_PERSIAN_STRANDED_RE = re.compile(r"(?:خارج\s+از\s+کشور.{0,36}?(?:گیر\s+کرد|کیف(?:م|م\s+را)?\s+گم)|کیف(?:م|م\s+را)?\s+گم\s+کرد)")
_PERSIAN_BETA_PAYMENT_RE = re.compile(r"(?:تست\s+بتا|بتای\s+(?:دستیار|هوش\s+مصنوعی)).{0,96}?(?:اطلاعات\s+پرداخت|کارت\s+بانکی)")


def persian_scam_motifs(text: str, request_context: bool) -> list[dict]:
    """Return high-specificity Persian scam motifs from observable co-occurrences.

    Each motif requires multiple independently meaningful cues. A named service,
    a delivery notice, or a welfare benefit alone never produces one of these
    findings, which keeps ordinary Persian news and account notifications from
    being treated as scams.
    """
    if not re.search(r"[\u0600-\u06FF]", text):
        return []

    has_authority = bool(_PERSIAN_AUTHORITY_RE.search(text))
    has_delivery = bool(_PERSIAN_DELIVERY_RE.search(text))
    has_welfare = bool(_PERSIAN_WELFARE_RE.search(text))
    has_payment = bool(_PERSIAN_PAYMENT_RE.search(text))
    has_credential = bool(_PERSIAN_CREDENTIAL_RE.search(text))
    has_pressure = bool(_PERSIAN_PRESSURE_RE.search(text))
    has_legal_case = bool(_PERSIAN_LEGAL_CASE_RE.search(text))
    has_legal_warning = bool(_PERSIAN_LEGAL_WARNING_RE.search(text))
    has_attachment_tracking = bool(_PERSIAN_ATTACHMENT_TRACKING_RE.search(text))
    has_card_limit = bool(_PERSIAN_CARD_LIMIT_RE.search(text))
    has_transfer_delegation = bool(_PERSIAN_TRANSFER_DELEGATION_RE.search(text))
    has_deferred_repayment = bool(_PERSIAN_DEFERRED_REPAYMENT_RE.search(text))
    has_invoice = bool(_PERSIAN_INVOICE_RE.search(text))
    has_legal_threat = bool(_PERSIAN_LEGAL_THREAT_RE.search(text))
    has_executive = bool(_PERSIAN_EXECUTIVE_RE.search(text))
    has_secrecy = bool(_PERSIAN_SECRECY_RE.search(text))
    has_support = bool(_PERSIAN_SUPPORT_RE.search(text))
    has_compromise = bool(_PERSIAN_COMPROMISE_RE.search(text))
    has_callback = bool(_PERSIAN_CALLBACK_RE.search(text))
    has_investment_return = bool(_PERSIAN_INVESTMENT_RETURN_RE.search(text))
    has_reward = bool(_PERSIAN_REWARD_RE.search(text))
    has_advance_fee = bool(_PERSIAN_ADVANCE_FEE_RE.search(text))
    has_job = bool(_PERSIAN_JOB_RE.search(text))
    has_document = bool(_PERSIAN_DOCUMENT_RE.search(text))
    has_service = bool(_PERSIAN_SERVICE_RE.search(text))
    has_cutoff = bool(_PERSIAN_CUTOFF_RE.search(text))
    has_bank_lockout = bool(_PERSIAN_BANK_LOCKOUT_RE.search(text))
    has_stranded = bool(_PERSIAN_STRANDED_RE.search(text))
    has_beta_payment = bool(_PERSIAN_BETA_PAYMENT_RE.search(text))
    motifs: list[dict] = []

    def add(code: str, title: str, description: str, evidence: list[str], category: str = "fraud") -> None:
        motifs.append({
            "category": category,
            "code": code,
            "title": title,
            "description": description,
            "evidence": "; ".join(evidence)[:500],
            "severity": _severity_for_code(code),
            "impact": 0.0,
            "confidence": 0.91,
            "extra": {"source": "persian_contextual_pattern", "match_count": len(evidence)},
        })

    if has_authority and request_context and (has_payment or has_credential):
        add(
            "persian_authority_lure",
            "Persian authority credential or payment lure",
            "A claimed Persian authority is paired with a request for money or sensitive credentials.",
            ["ادعای نهاد رسمی", "درخواست اقدام", "درخواست پرداخت یا اطلاعات حساس"],
        )
    if has_delivery and request_context and has_payment and (has_pressure or URL_RE.search(text)):
        add(
            "persian_delivery_fee_lure",
            "Persian delivery-fee lure",
            "A delivery notice combines a payment request with pressure or a link.",
            ["اعلان تحویل", "درخواست پرداخت", "فشار زمانی یا پیوند"],
        )
    if has_welfare and request_context and (has_payment or has_credential) and (has_pressure or URL_RE.search(text)):
        add(
            "persian_benefit_lure",
            "Persian benefit-claim lure",
            "A public-benefit claim is paired with a pressured request for money or credentials.",
            ["ادعای مزایای عمومی", "درخواست اقدام", "درخواست پرداخت یا اطلاعات حساس"],
        )
    if has_legal_case and has_legal_warning:
        add(
            "persian_legal_case_pressure",
            "Persian legal-case pressure lure",
            "A purported case filed against the recipient is paired with a final-warning pressure cue.",
            ["پروندهٔ ادعایی علیه مخاطب", "هشدار نهایی یا فوری"],
            category="manipulation",
        )
    if has_legal_case and has_attachment_tracking:
        add(
            "persian_legal_attachment_lure",
            "Persian legal attachment lure",
            "A purported legal case directs the recipient to tracking or an attachment, a common delivery lure.",
            ["پروندهٔ ادعایی علیه مخاطب", "رهگیری یا پیوست"],
        )
    if has_card_limit and has_transfer_delegation:
        add(
            "persian_familiar_transfer_lure",
            "Persian familiar-person transfer lure",
            "An alleged card-limit problem is used to ask the recipient to move money for another person.",
            ["بهانهٔ سقف کارت", "درخواست جابه‌جایی پول برای شخص دیگر"],
        )
    if has_transfer_delegation and has_deferred_repayment:
        add(
            "persian_deferred_repayment_lure",
            "Persian deferred-repayment pressure",
            "A money-transfer request is paired with a promise to repay later, a common impersonation pretext.",
            ["درخواست جابه‌جایی پول", "وعدهٔ بازپرداخت بعدی"],
            category="manipulation",
        )
    if has_invoice and has_payment and (has_pressure or has_legal_threat):
        add("persian_invoice_pressure_lure", "Persian invoice-pressure lure",
            "An overdue invoice claim is paired with an immediate payment or legal-pressure demand.",
            ["صورت‌حساب یا بدهی ادعایی", "درخواست پرداخت", "فشار حقوقی یا زمانی"])
    if has_executive and has_payment and has_secrecy:
        add("persian_executive_transfer_lure", "Persian executive-transfer lure",
            "A claimed executive requests a confidential money transfer without independent confirmation.",
            ["ادعای مدیرعامل", "درخواست انتقال پول", "فشار برای پنهان‌کاری"])
    if has_support and has_compromise and has_callback:
        add("persian_support_callback_lure", "Persian support-callback lure",
            "A technical-security warning directs the recipient to call an unverified support number.",
            ["هشدار فنی یا امنیتی", "ادعای پشتیبانی", "درخواست تماس با شمارهٔ پیام"])
    if has_investment_return and (has_payment or "سرمایه" in text or "برداشت" in text):
        add("persian_investment_return_lure", "Persian investment-return lure",
            "An investment pitch claims recurring or guaranteed returns while soliciting capital.",
            ["ادعای بازده یا سود غیرعادی", "درخواست سرمایه یا واریز"])
    if has_reward and has_advance_fee and has_payment:
        add("persian_reward_fee_lure", "Persian reward-fee lure",
            "A prize or reward claim requires an advance processing or administrative fee.",
            ["ادعای برنده‌شدن", "هزینهٔ پیش‌پرداخت", "درخواست واریز"])
    if has_job and has_document and request_context:
        add("persian_job_document_lure", "Persian job-document lure",
            "A job approach requests identity or banking documents before a verified hiring process.",
            ["پیشنهاد شغلی", "درخواست مدارک یا اطلاعات بانکی", "درخواست اقدام"])
    if has_service and has_cutoff and request_context and (has_payment or URL_RE.search(text)):
        add("persian_service_cutoff_lure", "Persian service-cutoff lure",
            "A utility, telecom, or insurance cutoff notice directs an immediate payment or link action.",
            ["ادعای قطع سرویس", "درخواست اقدام", "پرداخت یا پیوند"])
    if has_authority and has_bank_lockout and request_context and (URL_RE.search(text) or has_credential):
        add("persian_bank_lockout_lure", "Persian bank-lockout lure",
            "A claimed bank account lockout requests identity verification through message-provided details or a link.",
            ["ادعای مسدودی حساب", "درخواست احراز هویت", "پیوند یا دادهٔ حساس"])
    if has_stranded and has_payment and has_deferred_repayment:
        add("persian_stranded_friend_lure", "Persian stranded-friend transfer lure",
            "A familiar-person emergency abroad is paired with a money transfer and repayment promise.",
            ["بهانهٔ گیر افتادن یا گم‌شدن کیف", "درخواست انتقال پول", "وعدهٔ بازپرداخت"])
    if has_beta_payment:
        add("persian_beta_payment_lure", "Persian beta-access payment lure",
            "A beta-access invitation requests payment details before providing access.",
            ["دعوت به تست بتا", "درخواست اطلاعات پرداخت"])
    return motifs


def analyze_language_quality(text: str) -> dict:
    """Heuristics for grammar/spelling quality and message structure."""
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    words = WORD_RE.findall(text.lower())
    total_words = len(words)
    caps_ratio = sum(1 for w in words if w.isupper()) / max(total_words, 1)
    all_caps_sentences = sum(
        1 for s in sentences if len(s.split()) >= 3 and s.isupper()
    )
    has_greeting = bool(
        re.search(r"\b(dear|hello|hi|good (morning|afternoon|evening))\b", text, re.I)
    )
    exclamations = text.count("!")
    quality = "good"
    reasons: list[str] = []
    if total_words and caps_ratio > 0.15:
        quality = "poor"
        reasons.append("excessive capitalization")
    if all_caps_sentences:
        quality = "poor"
        reasons.append("sentences in ALL CAPS")
    if exclamations >= 3:
        quality = "poor"
        reasons.append("heavy use of exclamation marks")
    return {
        "quality": quality,
        "sentence_count": len(sentences),
        "word_count": total_words,
        "caps_ratio": round(caps_ratio, 3),
        "all_caps_sentences": all_caps_sentences,
        "exclamations": exclamations,
        "has_greeting": has_greeting,
        "reasons": reasons,
    }


# Map of category -> (code, title, base explanation)
CATEGORY_MAP: dict[str, tuple[str, str, str]] = {
    "urgency": (
        "urgency_words",
        "Urgency language detected",
        "The message uses pressure language designed to make you act without thinking.",
    ),
    "fear": (
        "fear_tactics",
        "Fear tactics detected",
        "The message threatens negative consequences to scare you into compliance.",
    ),
    "reward": (
        "reward_scam",
        "Too-good-to-be-true reward",
        "The message promises prizes or winnings you did not enter for.",
    ),
    "lottery": (
        "lottery_scam",
        "Lottery scam pattern",
        "The message claims you won a lottery you never entered.",
    ),
    "investment": (
        "investment_scam",
        "Investment offer with guaranteed returns",
        "The message promotes an investment with guaranteed or unusually high returns.",
    ),
    "crypto": (
        "crypto_scam",
        "Cryptocurrency request",
        "The message asks you to send or invest cryptocurrency.",
    ),
    "fake_job": (
        "fake_job",
        "Fake job offer pattern",
        "The message offers a job with unusual or too-good conditions.",
    ),
    "romance": (
        "romance_scam",
        "Romance scam pattern",
        "The message uses emotional language typical of romance scams.",
    ),
    "government": (
        "gov_impersonation",
        "Government impersonation",
        "The message pretends to be from a government agency.",
    ),
    "bank": (
        "bank_impersonation",
        "Bank impersonation",
        "The message pretends to be from a bank or financial institution.",
    ),
    "otp": (
        "requests_otp",
        "Requests verification code",
        "The message asks for a verification or one-time code.",
    ),
    "password": (
        "requests_password",
        "Requests password",
        "The message asks for your password or login credentials.",
    ),
    "verification": (
        "verification_request",
        "Account verification request",
        "The message asks you to verify your account through a provided link.",
    ),
    "identity": (
        "identity_theft",
        "Identity theft attempt",
        "The message asks for personal documents or data that can be used to steal your identity.",
    ),
    "remote": (
        "remote_access",
        "Remote access request",
        "The message asks you to install software or allow remote access.",
    ),
    "social": (
        "social_engineering",
        "Social engineering",
        "The message manipulates you using emotion, urgency, or authority.",
    ),
    "money": (
        "money_transfer",
        "Money transfer request",
        "The message asks you to send money through irreversible services.",
    ),
}


def sanitize_text(text: str) -> str:
    """Remove invisible/non-printable characters and normalize unicode.
    
    Handles:
    - Zero-width spaces (U+200B, U+200C, U+200D)
    - Zero-width joiners/non-joiners
    - Unicode control characters
    - Bidirectional control characters
    - Invisible separators
    - Confusables (homoglyphs)
    """
    if not text:
        return text

    text = normalize_persian_for_matching(text)

    # Complete list of invisible/control characters to strip
    # This covers all known invisible unicode characters
    invisible_chars = re.compile(
        r'[' +
        # Zero-width characters
        '\u200B\u200C\u200D\u200E\u200F' +
        # Byte order mark
        '\uFEFF' +
        # Bidirectional control
        '\u202A\u202B\u202C\u202D\u202E' +
        # Invisible mathematical operators
        '\u2060\u2061\u2062\u2063\u2064' +
        # Invisible formatting
        '\u2066\u2067\u2068\u2069' +
        # Braille pattern blank
        '\u2800' +
        # Mongolian vowel separator
        '\u180E' +
        # Arabic formatting
        '\u061C' +
        # Hebrew punctuation
        '\u05BE\u05C0\u05C3\u05C6' +
        # Invisible separators
        '\u00AD\u034F\u115F\u1160\u17B4\u17B5' +
        # Variation selectors
        '\uFE00\uFE01\uFE02\uFE03\uFE04\uFE05\uFE06\uFE07\uFE08\uFE09\uFE0A\uFE0B\uFE0C\uFE0D\uFE0E\uFE0F' +
        # Invisible space variations
        '\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A' +
        # Line separator, paragraph separator
        '\u2028\u2029' +
        # Zero-width non-joiner alternatives
        '\u202F\u205F' +
        # Specials
        '\uFFF9\uFFFA\uFFFB' +
        # Deprecated formatting
        '\u206A\u206B\u206C\u206D\u206E\u206F' +
        ']'
    )
    text = invisible_chars.sub('', text)
    
    # Replace common confusable characters
    confusables = {
        # Persian/Arabic digits
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
        # Full-width Latin
        'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E',
        'Ｆ': 'F', 'Ｇ': 'G', 'Ｈ': 'H', 'Ｉ': 'I', 'Ｊ': 'J',
        'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N', 'Ｏ': 'O',
        'Ｐ': 'P', 'Ｑ': 'Q', 'Ｒ': 'R', 'Ｓ': 'S', 'Ｔ': 'T',
        'Ｕ': 'U', 'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X', 'Ｙ': 'Y',
        'Ｚ': 'Z', 'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd',
        'ｅ': 'e', 'ｆ': 'f', 'ｇ': 'g', 'ｈ': 'h', 'ｉ': 'i',
        'ｊ': 'j', 'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n',
        'ｏ': 'o', 'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's',
        'ｔ': 't', 'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x',
        'ｙ': 'y', 'ｚ': 'z',
        # Cyrillic that looks like Latin (common in phishing)
        'А': 'A', 'В': 'B', 'С': 'C', 'Е': 'E', 'Н': 'H',
        'К': 'K', 'М': 'M', 'О': 'O', 'Р': 'P', 'Т': 'T',
        'Х': 'X', 'а': 'a', 'с': 'c', 'е': 'e', 'о': 'o',
        'р': 'p', 'х': 'x', 'у': 'y',
        # Greek that looks like Latin
        'Α': 'A', 'Β': 'B', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'H',
        'Ι': 'I', 'Κ': 'K', 'Μ': 'M', 'Ν': 'N', 'Ο': 'O',
        'Ρ': 'P', 'Τ': 'T', 'Υ': 'Y', 'Χ': 'X',
        'α': 'a', 'β': 'b', 'ε': 'e', 'ο': 'o', 'ρ': 'p',
        # Special characters
        '℘': 'p', 'ℑ': 'I', 'ℜ': 'R', 'ℵ': 'aleph',
        'ℂ': 'C', 'ℍ': 'H', 'ℕ': 'N', 'ℙ': 'P', 'ℚ': 'Q',
        'ℝ': 'R', 'ℤ': 'Z',
        # Superscripts/subscripts
        '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
        '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
        '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
        '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
    }
    for old, new in confusables.items():
        text = text.replace(old, new)
    
    # Normalize unicode (NFKC decomposes and recomposes)
    text = unicodedata.normalize('NFKC', text)
    
    # Remove any remaining control characters except newline and tab
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Remove extra whitespace (keep single spaces)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def scan_patterns(text: str) -> tuple[list[dict], int]:
    """Run the pattern engine. Returns (findings, signal_count)."""
    # Sanitize text first
    text = sanitize_text(text)
    
    findings: list[dict] = []
    total_signals = 0
    evidence_parts: list[str] = []

    checks = [
        ("urgency", _URGENCY_PATTERNS),
        ("fear", _FEAR_PATTERNS),
        ("reward", _REWARD_PATTERNS),
        ("lottery", _LOTTERY_PATTERNS),
        ("investment", _INVESTMENT_PATTERNS),
        ("crypto", _CRYPTO_PATTERNS),
        ("fake_job", _FAKE_JOB_PATTERNS),
        ("romance", _ROMANCE_PATTERNS),
        ("government", _GOV_PATTERNS),
        ("bank", _BANK_PATTERNS),
        ("otp", _OTP_PATTERNS),
        ("password", _PASSWORD_PATTERNS),
        ("verification", _VERIFICATION_PATTERNS),
        ("identity", _IDENTITY_PATTERNS),
        ("remote", _REMOTE_PATTERNS),
        ("social", _SOCIAL_PATTERNS),
        ("money", _MONEY_PATTERNS),
    ]

    request_context = has_request_context(text)
    for category, patterns in checks:
        count = match_count(patterns, text)
        if count == 0:
            continue
        code, title, desc = CATEGORY_MAP[category]
        examples = find_matches(patterns, text)[:4]

        # Generic topical language is deliberately weak until the message asks
        # the recipient to do something. This prevents false positives such as
        # a news article that mentions Bitcoin or an ordinary bank newsletter.
        # High-risk topics become evidence only when the message asks the reader
        # to do something. This is especially important in Persian, where words
        # such as «بانک», «کد» and «پرداخت» are common in legitimate notices.
        action_gated = {"bank", "government", "crypto", "fake_job", "romance", "otp", "password", "verification", "identity", "remote", "money"}
        requires_action = category in action_gated
        contextual = request_context or not requires_action
        if requires_action and not contextual:
            continue

        evidence = "; ".join(examples)
        findings.append(
            {
                "category": category,
                "code": code,
                "title": title,
                "description": desc,
                "evidence": evidence[:500],
                "severity": _severity_for_code(code),
                "impact": 0.0,  # calibrated by the trust engine
                "confidence": min(0.95, 0.55 + 0.08 * count + (0.08 if request_context else 0.0)),
                "extra": {
                    "source": "pattern",
                    "match_count": count,
                    "matched_terms": examples,
                    "request_context": request_context,
                },
            }
        )
        total_signals += count
        evidence_parts.extend(examples)

    motifs = persian_scam_motifs(text, request_context)
    findings.extend(motifs)
    total_signals += len(motifs)

    # Grammar / language quality
    quality = analyze_language_quality(text)
    if quality["quality"] == "poor":
        findings.append(
            {
                "category": "language",
                "code": "bad_grammar",
                "title": "Poor grammar / broken language",
                "description": "The message has language problems typical of bulk scam messages.",
                "evidence": ", ".join(quality["reasons"][:4]),
                "severity": "low",
                "impact": 0.0,
                "confidence": 0.6,
                "extra": {"source": "pattern", "match_count": 1},
            }
        )

    # Positive signal
    legit_count = match_count(_LEGIT_PATTERNS, text)
    if legit_count > 0 and total_signals == 0:
        findings.append(
            {
                "category": "analysis",
                "code": "no_scam_patterns",
                "title": "No scam patterns found",
                "description": "No known scam indicators were found in the content.",
                "evidence": None,
                "severity": "safe",
                "impact": 0.0,
                "confidence": 0.7,
                "extra": {"source": "pattern", "match_count": legit_count},
            }
        )

    return findings, total_signals


def _severity_for_code(code: str) -> str:
    mapping = {
        "requests_otp": "critical",
        "requests_password": "critical",
        "identity_theft": "critical",
        "gov_impersonation": "critical",
        "bank_impersonation": "critical",
        "investment_scam": "critical",
        "crypto_scam": "critical",
        "phishing_link": "critical",
        "remote_access": "critical",
        "persian_authority_lure": "critical",
        "persian_delivery_fee_lure": "high",
        "persian_benefit_lure": "high",
        "persian_legal_case_pressure": "high",
        "persian_legal_attachment_lure": "critical",
        "persian_familiar_transfer_lure": "critical",
        "persian_deferred_repayment_lure": "high",
        "romance_scam": "high",
        "verification_request": "high",
        "urgency_words": "high",
        "fear_tactics": "high",
        "social_engineering": "high",
        "fake_job": "high",
        "reward_scam": "high",
        "lottery_scam": "high",
        "money_transfer": "high",
        "bad_grammar": "low",
    }
    return mapping.get(code, "medium")
