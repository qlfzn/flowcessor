import os
import json
from app.utils.logger import Logger
from typing import Type, Dict, List
from dotenv import load_dotenv
from groq import Groq
from app.models.schemas import BankStatementResponse
from pydantic import BaseModel, ValidationError
from app.config import MAX_CHARS_PER_CHUNK, SYSTEM_PROMPT

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(
    api_key=API_KEY,
    max_retries=3,
)


class AIExtractionError(Exception):
    pass


class SchemaValidationError(Exception):
    pass


logger = Logger(__name__)


def split_into_chunks(text: str, max_chars: int) -> List[str]:
    """
    Split text into chunks by line boundaries
    """
    lines = text.splitlines()

    header_lines = []
    for line in lines[:10]:
        if line.strip():
            header_lines.append(line)
        if len(header_lines) >= 3:
            break
    header = "\n".join(header_lines) + "\n"

    chunks = []
    current_chunk_lines = []
    current_length = len(header)

    for line in lines:
        line_len = len(line) + 1
        if current_length + line_len > max_chars and current_chunk_lines:
            chunks.append(header + "\n".join(current_chunk_lines))
            current_chunk_lines = [line]
            current_length = len(header) + line_len
        else:
            current_chunk_lines.append(line)
            current_length += line_len

    if current_chunk_lines:
        chunks.append(header + "\n".join(current_chunk_lines))

    return chunks


def extract_transactions_from_chunk(chunk: str, response_schema: dict) -> List[Dict]:
    """
    Send a single chunk to the LLM and return the list of transactions.
    """
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"{SYSTEM_PROMPT}\nSchema to follow: {json.dumps(response_schema, indent=2)}",
            },
            {
                "role": "user",
                "content": f"Now extract from this statement chunk:\n\n{chunk}",
            },
        ],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    message = chat_completion.choices[0].message
    response_text = message.content

    usage = chat_completion.usage

    if usage:
        logger.warning(
            "Groq usage — prompt_tokens: %d, completion_tokens: %d, total_tokens: %d",
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.total_tokens,
        )

    try:
        parsed = json.loads(str(response_text))
        return parsed.get("transactions", [])
    except json.JSONDecodeError as e:
        raise AIExtractionError(f"failed to parse LLM response as JSON: {e}\n")


def generate_formatted_data(parsed_text: str) -> Dict:
    """
    Extract structured transaction data from raw text.
    Automatically chunks large statements to stay within token limits.
    """
    response_schema = BankStatementResponse.model_json_schema()

    try:
        if len(parsed_text) <= MAX_CHARS_PER_CHUNK:
            logger.warning("Text fits in single chunk (%d chars)", len(parsed_text))
            transactions = extract_transactions_from_chunk(parsed_text, response_schema)
        else:
            chunks = split_into_chunks(parsed_text, MAX_CHARS_PER_CHUNK)
            logger.warning(
                "Text split into %d chunks (total %d chars, ~%d chars each)",
                len(chunks),
                len(parsed_text),
                MAX_CHARS_PER_CHUNK,
            )

            all_chunks_text = "\n\n---NEXT CHUNK---\n\n".join(chunks)
            transactions = extract_transactions_from_chunk(
                all_chunks_text, response_schema
            )

        return {"transactions": transactions}

    except Exception as e:
        if isinstance(e, AIExtractionError):
            raise
        raise AIExtractionError(f"failed to extract receipt data: {e}")


def validate_json_with_schema(parsed_json: dict, schema: Type[BaseModel]) -> BaseModel:
    try:
        receipt = schema(**parsed_json)
        return receipt
    except ValidationError as e:
        raise SchemaValidationError(f"failed to validate json to schema: {e}")
