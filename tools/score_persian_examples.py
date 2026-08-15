from app.services.text_scanner import _scan_text_sync
from app.trust_engine.engine import compute_trust_score

EXAMPLES = {
    "legal_attachment_lure": "آخرین هشدار\nپرونده الکترونیکی بر علیه شما ثبت شد.\nرهگیری در پیوست",
    "familiar_transfer_lure": "سلام چطوری خوبی\n\nشرمنده کارتم سقفش پر شده میتونی 5 یا 10 برا کسی جابه جا کنی 12 به بعد برگردونم؟",
}

for name, text in EXAMPLES.items():
    raw = _scan_text_sync(text)
    result = compute_trust_score(raw["findings"])
    print(name)
    print(f"  trust_score={result.trust_score} risk={result.risk_level} probability={result.risk_probability:.3f} confidence={result.confidence:.3f}")
    for finding in raw["findings"]:
        print(f"  - {finding['code']}: {finding.get('evidence', '')}")
