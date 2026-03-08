# from app.utils import Logger
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.models.schemas import BankStatementResponse
from app.services.pdf_parser import extract_text_from_pdf, PDFParserError
from app.services.ai import (
    generate_formatted_data,
    validate_json_with_schema,
    AIExtractionError,
)

router = APIRouter()

MAX_SIZE = 16 * 1024 * 1024

logger = logging.getLogger(__name__)


@router.get("/")
def read_root():
    """
    Base endpoint
    """
    logger.info("Health check requested")
    return {"message": "all good!", "status": "200"}


@router.post("/files/upload", response_model=BankStatementResponse)
async def create_upload_file(file: UploadFile = File(...)):
    """
    Upload PDF file of bank statement, extract data, returns structured data.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, detail="invalid file type. only PDF is supported"
        )

    logger.info(f"Reading file: {file.filename}")
    contents = await file.read()

    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="file size exceeds limit")

    try:
        extracted_text = extract_text_from_pdf(contents)
        logger.warning(f"Text length: {len(extracted_text)}")
        formatted_data = generate_formatted_data(extracted_text)
        bank_statement_data = validate_json_with_schema(
            formatted_data, BankStatementResponse
        )

        list_of_transactions = list(bank_statement_data)
        logger.warning("no. of transactions: %d", len(list_of_transactions))
        return bank_statement_data
    except PDFParserError as e:
        raise HTTPException(status_code=400, detail=f"error parsing file: {str(e)}")
    except AIExtractionError as e:
        raise HTTPException(status_code=422, detail=f"error extracting data: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"internal server error: {str(e)}")
    finally:
        await file.close()
