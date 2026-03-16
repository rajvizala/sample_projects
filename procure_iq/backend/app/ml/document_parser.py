"""
NLP-powered document parser for procurement documents.
Extracts structured data from unstructured invoice and PO text using
regex patterns, rule-based NER, and optional LLM-assisted parsing.
"""

import re
from datetime import datetime

from app.schemas.procurement import DocumentParseResponse, ParsedLineItem


DATE_PATTERNS = [
    r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
    r'\b(\w+ \d{1,2},?\s*\d{4})\b',
    r'\b(\d{4}-\d{2}-\d{2})\b',
]

MONEY_PATTERN = r'\$?\s*([\d,]+\.?\d{0,2})'

VENDOR_INDICATORS = [
    r'(?:from|vendor|supplier|company|billed?\s*by|sold\s*by|ship\s*from)[:\s]+([A-Z][A-Za-z0-9\s&.,]+?)(?:\n|$)',
    r'^([A-Z][A-Z\s&.,]+(?:Inc|LLC|Ltd|Corp|Co|GmbH|SA|BV)\.?)[\s,]',
]

INVOICE_NUM_PATTERNS = [
    r'(?:invoice|inv)\s*(?:#|no|number|num)?[:\s]*([A-Za-z0-9-]+)',
    r'(?:bill)\s*(?:#|no|number)?[:\s]*([A-Za-z0-9-]+)',
]

PO_NUM_PATTERNS = [
    r'(?:purchase\s*order|po)\s*(?:#|no|number|num)?[:\s]*([A-Za-z0-9-]+)',
    r'(?:order)\s*(?:#|no|number)?[:\s]*([A-Za-z0-9-]+)',
]

PAYMENT_TERMS_PATTERNS = [
    r'(?:payment\s*terms?|terms?)[:\s]*(net\s*\d+|due\s*(?:on|upon)\s*receipt|cod|cia|\d+\s*days?)',
    r'\b(net\s*\d+)\b',
]

LINE_ITEM_PATTERN = r'([A-Za-z][A-Za-z0-9\s/()-]+?)\s+(\d+)\s+(?:\$\s*)?([\d,]+\.?\d*)\s+(?:\$\s*)?([\d,]+\.?\d*)'


def parse_document(text: str, doc_type: str = "invoice") -> DocumentParseResponse:
    """Parse unstructured procurement document text into structured data."""
    text_clean = text.strip()
    text_lower = text_clean.lower()

    vendor = _extract_first_match(text_clean, VENDOR_INDICATORS)
    if vendor:
        vendor = vendor.strip().rstrip(",.")

    invoice_num = _extract_first_match(text_lower, INVOICE_NUM_PATTERNS)
    po_num = _extract_first_match(text_lower, PO_NUM_PATTERNS)

    dates = _extract_dates(text_clean)
    doc_date = dates[0] if dates else None
    due_date = dates[1] if len(dates) > 1 else None

    payment_terms = _extract_first_match(text_lower, PAYMENT_TERMS_PATTERNS)

    line_items = _extract_line_items(text_clean)

    amounts = _extract_amounts(text_lower)
    subtotal = amounts.get("subtotal")
    tax = amounts.get("tax")
    total = amounts.get("total")

    if total is None and line_items:
        total = sum(item.total for item in line_items)
    if subtotal is None and line_items:
        subtotal = sum(item.total for item in line_items)

    currency = "USD"
    if any(c in text_lower for c in ["eur", "euro"]):
        currency = "EUR"
    elif any(c in text_lower for c in ["gbp", "pound"]):
        currency = "GBP"

    filled_fields = sum(1 for v in [vendor, invoice_num or po_num, doc_date, total, line_items] if v)
    confidence = filled_fields / 5.0

    raw_entities = {
        "dates_found": dates,
        "amounts_found": amounts,
        "line_items_count": len(line_items),
    }

    return DocumentParseResponse(
        vendor_name=vendor,
        invoice_number=invoice_num,
        po_number=po_num,
        date=doc_date,
        due_date=due_date,
        subtotal=subtotal,
        tax=tax,
        total=total,
        currency=currency,
        payment_terms=payment_terms,
        line_items=line_items,
        confidence=round(confidence, 2),
        raw_entities=raw_entities,
    )


def _extract_first_match(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None


def _extract_dates(text: str) -> list[str]:
    dates = []
    for pattern in DATE_PATTERNS:
        matches = re.findall(pattern, text)
        dates.extend(matches)
    return dates[:4]


def _extract_line_items(text: str) -> list[ParsedLineItem]:
    items = []
    for match in re.finditer(LINE_ITEM_PATTERN, text):
        try:
            name = match.group(1).strip()
            qty = int(match.group(2))
            unit_price = float(match.group(3).replace(",", ""))
            total = float(match.group(4).replace(",", ""))
            if qty > 0 and unit_price > 0:
                items.append(ParsedLineItem(
                    item_name=name, quantity=qty, unit_price=unit_price, total=total,
                ))
        except (ValueError, IndexError):
            continue
    return items


def _extract_amounts(text: str) -> dict:
    amounts = {}

    total_match = re.search(
        r'(?:total|amount\s*due|balance\s*due|grand\s*total)[:\s]*\$?\s*([\d,]+\.?\d*)',
        text, re.IGNORECASE,
    )
    if total_match:
        amounts["total"] = float(total_match.group(1).replace(",", ""))

    subtotal_match = re.search(
        r'(?:subtotal|sub[\s-]*total)[:\s]*\$?\s*([\d,]+\.?\d*)',
        text, re.IGNORECASE,
    )
    if subtotal_match:
        amounts["subtotal"] = float(subtotal_match.group(1).replace(",", ""))

    tax_match = re.search(
        r'(?:tax|vat|gst|hst)[:\s]*\$?\s*([\d,]+\.?\d*)',
        text, re.IGNORECASE,
    )
    if tax_match:
        amounts["tax"] = float(tax_match.group(1).replace(",", ""))

    return amounts
