"""Conservative, opt-in financial query normalization; no corpus or label access."""

import re


def prepare_query(question, mode="baseline"):
    if mode == "baseline":
        return question
    if mode != "financial-v1":
        raise ValueError("Unknown query mode")
    text = re.sub(
        r"^\s*Assume that you are a (?:public equities|financial) analyst\.\s*",
        "",
        question,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"Answer the following question by primarily using information that is shown in the "
        r"(balance sheet|cash flow statement|income statement):\s*",
        r"\1: ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"Give a response to the question by relying on the details shown in the\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\bFY\s*(\d{4})\b", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:PPNE|PP&E)\b", "property, plant and equipment", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\b(?:capex|capital expenditures?)\b",
        "capital expenditures purchases of property, plant and equipment",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\brevenue\b", "revenue net sales", text, flags=re.IGNORECASE)
    return " ".join(text.split())
