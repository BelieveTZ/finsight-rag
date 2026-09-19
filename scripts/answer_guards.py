"""Conservative single-report guards, not a general entity or accounting parser."""

import math
import re


def scope_error(question, document=None):
    document = document or {"company": "3M", "aliases": ["3M"], "year": 2018}
    aliases = document["aliases"]
    company = document["company"]
    years = re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", question)
    if not any(re.search(r"\b" + re.escape(alias) + r"\b", question, re.I) for alias in aliases):
        return f"The selected report supports explicit questions about {company} only."
    owners = re.findall(r"\b([\w]+)['\u2019]s\b", question, re.I)
    if any(
        owner.lower() not in {alias.lower().split()[-1] for alias in aliases} for owner in owners
    ):
        return "The question contains an unsupported or ambiguous company reference."
    if re.search(r"\b(compare|versus|vs|companies)\b", question, re.I):
        return "Multi-company or comparative questions are not supported by this prototype."
    allowed_years = {str(document["year"] - offset) for offset in range(3)}
    if len(set(years)) != 1 or years[0] not in allowed_years:
        return (
            f"Ask for one explicit year from {document['year'] - 2} through "
            f"{document['year']} in the selected {company} report."
        )
    return None


def refusal(reason):
    return {
        "status": "insufficient_evidence",
        "answer": reason,
        "value": None,
        "unit": "",
        "document_id": None,
        "pdf_page": None,
        "quote": "",
        "chunk_id": None,
    }


def numeric_evidence(answer, hit):
    if type(answer.get("value")) not in (int, float) or not math.isfinite(answer["value"]):
        return False
    quote = answer.get("quote")
    if not isinstance(quote, str):
        return False
    target_scale = {"USD millions": 1, "USD billions": 1000}.get(answer.get("unit"))
    if target_scale is None:
        return False
    pattern = r"(?<![\w.])(-?\d[\d,]*(?:\.\d+)?)\s*(million|billion)\b"
    amounts = [
        (float(n.replace(",", "")), 1000 if u.lower() == "billion" else 1)
        for n, u in re.findall(pattern, quote, re.I)
    ]
    if not amounts and re.search(r"\(\s*millions\s*\)|in millions", hit["text"], re.I):
        amounts = [
            (float(n.replace(",", "")), 1)
            for n in re.findall(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?", quote)
        ]
    return any(
        math.isclose(abs(n) * scale, abs(answer["value"]) * target_scale, rel_tol=0, abs_tol=0.001)
        for n, scale in amounts
    )


def statement_heading(text, kind):
    patterns = {
        "balance": r"consolidatedbalancesheets?",
        "cash_flow": r"consolidatedstatements?ofcashflows?",
    }
    lines = [line for line in text.splitlines() if line.strip()][:10]
    return any(re.fullmatch(patterns[kind], "".join(line.lower().split())) for line in lines)


def question_checks(question, answer, hit, document=None):
    year = re.search(r"(?:19|20)\d{2}", question)
    text = hit["text"].lower()
    requested_unit = (
        "USD billions" if re.search(r"\bbillions?\b", question, re.I) else "USD millions"
    )
    checks = {
        "requested_unit": answer["unit"] == requested_unit,
        "year_in_evidence": year is not None and year.group() in text,
        "corpus_document": hit["document_id"] == (document or {}).get("document_id", "3M_2018_10K"),
    }
    if re.search(r"\bbalance\s+sheets?\b", question, re.I):
        checks["statement_type"] = statement_heading(hit["text"], "balance")
    if re.search(r"\bcash\s+flow\s+statements?\b", question, re.I):
        checks["statement_type"] = statement_heading(hit["text"], "cash_flow")
    return checks
