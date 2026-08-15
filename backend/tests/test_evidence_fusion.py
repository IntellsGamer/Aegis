"""Regression tests for the deterministic Evidence Fusion predictor."""
from __future__ import annotations

import pytest

from app.services.text_scanner import _scan_text_sync
from app.trust_engine.engine import compute_trust_score


def _assess(text: str):
    raw = _scan_text_sync(text)
    return compute_trust_score(raw["findings"]), raw


def test_independent_phishing_evidence_reaches_critical_risk():
    result, raw = _assess(
        "URGENT: your bank account will be locked. Click "
        "http://paypa1-login.example/verify immediately and enter your password."
    )

    assert result.risk_level == "critical"
    assert result.risk_probability >= 0.95
    assert result.confidence >= 0.70
    assert raw["meta"]["predictor"] == "deterministic-evidence-fusion"
    assert {item["code"] for item in raw["findings"]} >= {
        "urgency_words", "typosquatting", "suspicious_keywords_url"
    }


def test_benign_topical_content_is_not_a_bank_impersonation():
    result, raw = _assess(
        "This security article explains how financial institutions protect customers "
        "from fraud and why independently verifying a sender matters."
    )

    assert result.risk_level == "low"
    assert result.risk_probability < 0.25
    assert "bank_impersonation" not in {item["code"] for item in raw["findings"]}


def test_repeated_cue_has_bounded_effect_without_independent_evidence():
    one = compute_trust_score([
        {"code": "urgency_words", "category": "manipulation", "confidence": 0.8,
         "evidence": "urgent", "extra": {"source": "pattern", "match_count": 1}},
    ])
    repeated = compute_trust_score([
        {"code": "urgency_words", "category": "manipulation", "confidence": 0.8,
         "evidence": "urgent", "extra": {"source": "pattern", "match_count": 20}},
    ])

    assert repeated.risk_probability > one.risk_probability
    assert repeated.risk_probability < 0.50
    assert repeated.risk_level in {"low", "medium"}


def test_verified_threat_is_not_cancelled_by_benign_transport_observations():
    result = compute_trust_score([
        {"code": "known_threat", "category": "reputation", "confidence": 0.99,
         "evidence": "https://evil.example", "extra": {"source": "known_threat_feed"}},
        {"code": "https_secure", "category": "transport", "confidence": 0.95,
         "evidence": "TLS", "extra": {"source": "tls_observation"}},
        {"code": "domain_very_old", "category": "reputation", "confidence": 0.8,
         "evidence": "3000 days", "extra": {"source": "url_observation"}},
    ])

    assert result.risk_level == "critical"
    assert result.risk_probability >= 0.95
    assert result.trust_score <= 5.0


def test_empty_evidence_does_not_produce_overconfident_safety():
    result = compute_trust_score([])

    assert result.risk_level == "low"
    assert result.confidence <= 0.38
    assert result.coverage == 0.0


def test_text_scan_keeps_local_link_evidence_without_model_inference():
    result, raw = _assess("Please review https://bit.ly/claim-your-prize today.")

    assert raw["meta"]["link_assessments"]
    assert "shortened_url" in {item["code"] for item in raw["findings"]}
    assert result.risk_level in {"medium", "high", "critical"}


def test_first_rendered_csrf_token_authorizes_a_live_scan_submission():
    """The initial page response must include the same token as its HttpOnly cookie."""
    import re

    from app import create_app

    app = create_app({"TESTING": False, "SECRET_KEY": "evidence-fusion-test-secret"})
    with app.test_client() as production_client:
        page = production_client.get("/scan")
        assert page.status_code == 200
        token_match = re.search(
            rb'<meta name="csrf-token" content="([^"]+)">', page.data
        )
        assert token_match, "The first rendered page must expose a CSRF token"
        token = token_match.group(1).decode()
        assert "aegis_csrf=" in page.headers.get("Set-Cookie", "")

        scan = production_client.post(
            "/api/v1/scans/text",
            json={"text": "URGENT: click http://paypa1-login.example now"},
            headers={"X-CSRF-Token": token},
        )
        assert scan.status_code == 200
        assert scan.get_json()["verdict"] == "threat"


def test_persian_authority_credential_lure_reaches_critical_risk():
    result, raw = _assess(
        "ابلاغیه فوری سامانه ثنا: برای جلوگیری از مسدود شدن پرونده، همین حالا "
        "کد تأیید و شماره کارت ملی خود را در https://paypa1-login.example/ورود وارد کنید."
    )

    codes = {item["code"] for item in raw["findings"]}
    assert result.risk_level == "critical"
    assert {"persian_authority_lure", "requests_otp", "identity_theft"} <= codes
    assert raw["meta"]["predictor"] == "deterministic-evidence-fusion"


def test_persian_delivery_fee_lure_requires_multiple_observable_cues():
    result, raw = _assess(
        "مرسوله شما در انتظار است. برای پرداخت کارمزد تحویل، همین حالا از "
        "https://example.com/پرداخت اقدام کنید."
    )

    codes = {item["code"] for item in raw["findings"]}
    assert "persian_delivery_fee_lure" in codes
    assert "suspicious_keywords_url" in codes
    assert result.risk_level in {"high", "critical"}


def test_persian_safety_article_does_not_trigger_bank_or_otp_impersonation():
    result, raw = _assess(
        "راهنمای بانک ملی درباره امنیت: هرگز رمز یکبار مصرف خود را با کسی "
        "به اشتراک نگذارید. برای اطلاعات بیشتر به وب‌سایت رسمی بانک مراجعه کنید."
    )

    codes = {item["code"] for item in raw["findings"]}
    assert result.risk_level == "low"
    assert "bank_impersonation" not in codes
    assert "requests_otp" not in codes
    assert "persian_authority_lure" not in codes


def test_persian_and_arabic_glyph_variants_normalize_before_matching():
    result, raw = _assess(
        "اطلاعیه فوری: حساب شما مسدود می‌شود. براي تاييد حساب، كد امنيتي خود را همين حالا ارسال كنيد."
    )

    codes = {item["code"] for item in raw["findings"]}
    assert {"urgency_words", "fear_tactics", "requests_otp", "verification_request"} <= codes
    assert result.risk_level in {"high", "critical"}


def test_persian_legal_attachment_lure_reaches_high_risk():
    result, raw = _assess(
        "آخرین هشدار\nپرونده الکترونیکی بر علیه شما ثبت شد.\nرهگیری در پیوست"
    )

    codes = {item["code"] for item in raw["findings"]}
    assert {"persian_legal_case_pressure", "persian_legal_attachment_lure"} <= codes
    assert result.risk_level in {"high", "critical"}
    assert result.risk_probability >= 0.65


def test_persian_familiar_transfer_and_deferred_repayment_lure_reaches_high_risk():
    result, raw = _assess(
        "سلام چطوری خوبی\n\nشرمنده کارتم سقفش پر شده میتونی 5 یا 10 برا کسی جابه جا کنی 12 به بعد برگردونم؟"
    )

    codes = {item["code"] for item in raw["findings"]}
    assert {"persian_familiar_transfer_lure", "persian_deferred_repayment_lure"} <= codes
    assert result.risk_level in {"high", "critical"}
    assert result.risk_probability >= 0.65


@pytest.mark.parametrize(
    ("text", "expected_code"),
    [
        ("صورت‌حساب شما به مبلغ ۱۲,۴۵۰,۰۰۰ تومان معوق شده است. تا ۲۴ ساعت آینده پرداخت کنید، در غیر این صورت اقدام حقوقی خواهد شد.", "persian_invoice_pressure_lure"),
        ("از طرف مدیرعامل: نیاز به انتقال مبلغ ۵۰,۰۰۰,۰۰۰ تومان به شریک جدید داریم. لطفاً بدون مشورت با دیگران انجام دهید.", "persian_executive_transfer_lure"),
        ("هشدار پشتیبانی مایکروسافت: فعالیت مشکوک روی دستگاه شما دیده شده است. برای تأیید با شماره ۰۲۱-۵۵۵۵-۰۱۹۹ تماس بگیرید.", "persian_support_callback_lure"),
        ("ربات معاملاتی ارز دیجیتال با بازده روزانه ۲.۳٪؛ حداقل سرمایه ۵۰,۰۰۰,۰۰۰ تومان و برداشت آنی.", "persian_investment_return_lure"),
        ("تبریک، در قرعه‌کشی برنده شده‌اید. برای دریافت جایزه، هزینه پردازش را به کارشناس واریز کنید.", "persian_reward_fee_lure"),
        ("پروفایل لینکدین شما را دیدیم؛ حقوق ماهیانه عالی است. لطفاً مدارک شناسایی و اطلاعات بانکی را ارسال کنید.", "persian_job_document_lure"),
        ("شرکت مخابرات: بسته اینترنتی شما به علت پرداخت نشده قطع می‌شود. برای پرداخت روی https://example.com/pay کلیک کنید.", "persian_service_cutoff_lure"),
        ("بانک ملت: حساب شما به دلیل فعالیت غیرمجاز مسدود شده است. برای احراز هویت روی https://example.com/verify کلیک کنید.", "persian_bank_lockout_lure"),
        ("سلام، خارج از کشور گیر کردم و کیفم را گم کردم. می‌توانی ۵۰۰,۰۰۰ تومان به حساب دوستم واریز کنی؟ بعداً برمی‌گردونم.", "persian_stranded_friend_lure"),
        ("شما برای تست بتای دستیار هوش مصنوعی جدید ما انتخاب شده‌اید؛ فرم را با اطلاعات پرداخت تکمیل کنید.", "persian_beta_payment_lure"),
    ],
)
def test_common_persian_scam_families_emit_high_specificity_motifs(text, expected_code):
    result, raw = _assess(text)
    codes = {item["code"] for item in raw["findings"]}

    assert expected_code in codes
    assert result.risk_level in {"high", "critical"}


def test_benign_persian_legal_guidance_does_not_trigger_attachment_lure():
    result, raw = _assess(
        "راهنمای عمومی پیگیری پرونده الکترونیکی: برای مشاهده وضعیت، فقط از درگاه رسمی قوه قضائیه استفاده کنید و پیوست‌های ناشناس را باز نکنید."
    )

    codes = {item["code"] for item in raw["findings"]}
    assert "persian_legal_case_pressure" not in codes
    assert "persian_legal_attachment_lure" not in codes
    assert result.risk_level == "low"
