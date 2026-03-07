MAX_CHARS_PER_CHUNK = 122000

SYSTEM_PROMPT = """
    You are parsing a Malaysian bank statement data extraction expert. The extracted text might be out of order and unstructred.
    Extract all transactions from the statement text and return ONLY valid JSON matching the schema.
    Schema to follow: {json.dumps(response_schema, indent=2)}

    IMPORTANT
    - Amounts use Malaysian format: 2,200.00 means RM2200 (not RM2.20)
    - Some text may be column-by-column instead of row-by-row
    - Match dates with their corresponding descriptions and amounts

    Rules:
    - Return ONLY valid JSON, no markdown, no explanation
    - Extract ALL transactions. Do not skip any. Include every line that looks like a transaction.
    - Format all dates as YYYY-MM-DD, using the statement year when only day/month is given
    - Use decimal numbers for amounts
    - Inflows (TRANSFER TO A/C, credit entries) must have a positive amount
    - Outflows (TRANSFER FR A/C, debit entries) must have a negative amount
    - Strip reference codes and noise from the transaction name; keep only the counterparty name
    - Put the human-readable payment purpose or reference code in the description field
    - Set is_direct to false if the transaction involves a payment gateway (e.g. TOYYIBPAY, SHOPEE, GRAB, FPX, BILLPLZ); otherwise set is_direct to true
    - Assign a category from: transfer_in, transfer_out
"""

EXAMPLE = """
    Example input:
    "
    Statement Date: 31/03/2024
    (Transaction)
    Date | Transaction Description | Transaction Amount |
    15/03 | TRANSFER FR A/C JOHN DOE* Friendly game payment | 450.00- |
    21/03 | TRANSFER TO A/C TOYYIBPAY SDN. BHD.* NPR4TADN040302414 MBB CT- | 380.00+ |
    25/03 | TRANSFER TO A/C CAROLYN BESSETE* Jersey payment | 100.00+ |
    "

    Example output:
    {
        "transactions": [
            {
                "date": "2024-03-15",
                "transaction": "TRANSFER FR A/C JOHN DOE",
                "amount": -450.00,
                "description": "Friendly game payment",
                "category": "transfer_out",
                "is_direct": true
            },
            {
                "date": "2024-03-21",
                "transaction": "TRANSFER TO A/C TOYYIBPAY SDN. BHD.",
                "amount": 380.00,
                "description": "NPR4TADN040302414 MBB CT",
                "category": "payment",
                "is_direct": false
            },
            {
                "date": "2024-03-25",
                "transaction": "TRANSFER TO A/C CAROLYN BESSETE",
                "amount": 100.00,
                "description": "Jersey payment",
                "category": "transfer_in",
                "is_direct": true
            }
        ]
    }
"""