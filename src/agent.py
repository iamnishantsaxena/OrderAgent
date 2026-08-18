"""
Order Extraction Pipeline
Runs the fixed extraction pipeline: LLM extraction, regex-tool refinement,
validation, confidence scoring, and assembly.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Iterator
from datetime import datetime

from langchain_ollama import OllamaLLM

from .schema import (
    Order, ExtractionResult, OrderItem,
    validate_order_completeness, calculate_overall_confidence,
    CRITICAL_FIELDS, CONFIDENCE_THRESHOLD_HIGH
)
from .prompts import get_extraction_prompt
from .pdf_processor import PDFProcessor
from .config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderExtractionPipeline:
    """
    Runs the fixed pipeline that turns unstructured text into structured order data
    """

    def __init__(
        self,
        model_name: str = config.DEFAULT_MODEL,
        temperature: float = config.LLM_TEMPERATURE,
        ollama_base_url: str = config.OLLAMA_BASE_URL,
        verbose: bool = True
    ):
        """
        Initialize the order extraction pipeline

        Args:
            model_name: Ollama model to use
            temperature: LLM temperature (lower = more deterministic)
            ollama_base_url: Base URL for Ollama API
            verbose: Whether to print detailed logs
        """
        self.model_name = model_name
        self.temperature = temperature
        self.verbose = verbose

        # Initialize LLM
        logger.info(f"Initializing Ollama with model: {model_name}")
        self.llm = OllamaLLM(
            model=model_name,
            base_url=ollama_base_url,
            temperature=temperature,
        )

        # Initialize PDF processor
        self.pdf_processor = PDFProcessor(
            chunk_size=config.PDF_CHUNK_SIZE,
            chunk_overlap=config.PDF_CHUNK_OVERLAP
        )

        # Pipeline state
        self.extraction_steps = []

    def extract_order(
        self,
        input_text: str,
        source_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Main extraction method

        Args:
            input_text: Text to extract order from
            source_type: Type of input (text, email, pdf)

        Returns:
            ExtractionResult as dictionary
        """
        logger.info(f"Starting order extraction from {source_type}")
        self.extraction_steps = []

        try:
            self._log_step("Analyzing input and extracting fields")
            extracted_data = self._extract_with_llm(input_text)
        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            return self._create_error_result(str(e))

        event = self._last(self._run_pipeline_streaming(extracted_data, input_text, source_type))
        return event["result"] if event["status"] == "complete" else self._create_error_result(event["error"])

    def extract_order_streaming(
        self,
        input_text: str,
        source_type: str = "text"
    ) -> Iterator[Dict[str, Any]]:
        """
        Extract order with streaming updates

        Yields progress updates as extraction proceeds
        """
        yield {"status": "starting", "message": "Initializing extraction"}

        self.extraction_steps = []

        try:
            yield {"status": "extracting", "message": "Analyzing input with LLM"}
            extracted_data = self._extract_with_llm(input_text)
            yield {"status": "progress", "data": extracted_data, "step": 1, "total_steps": 5}
        except Exception as e:
            logger.error(f"Error during streaming extraction: {e}")
            yield {"status": "error", "error": str(e)}
            return

        yield from self._run_pipeline_streaming(extracted_data, input_text, source_type)

    def _run_pipeline_streaming(
        self,
        extracted_data: Dict[str, Any],
        input_text: str,
        source_type: str
    ) -> Iterator[Dict[str, Any]]:
        """
        Steps 2-6: refine, validate, score, build, assemble.
        Single shared implementation behind extract_order/extract_order_streaming/process_pdf.
        """
        try:
            # Step 2: Use tools for specific field extraction
            yield {"status": "refining", "message": "Refining with specialized tools"}
            refined_data = self._refine_with_tools(input_text, extracted_data)
            yield {"status": "progress", "data": refined_data, "step": 2, "total_steps": 5}

            # Step 3: Validate extracted data
            yield {"status": "validating", "message": "Validating extracted data"}
            validation_result = self._validate_extraction(refined_data)
            yield {"status": "progress", "data": validation_result, "step": 3, "total_steps": 5}

            # Step 4: Calculate confidence scores
            yield {"status": "scoring", "message": "Calculating confidence scores"}
            confidence_scores = self._calculate_confidence(refined_data, input_text)
            yield {"status": "progress", "data": confidence_scores, "step": 4, "total_steps": 5}

            # Step 5: Build final result
            yield {"status": "finalizing", "message": "Building final order"}
            order = self._build_order(refined_data)

            # Step 6: Determine if order can be created
            is_valid, missing_critical = validate_order_completeness(order)
            overall_confidence = calculate_overall_confidence(confidence_scores)

            result = ExtractionResult(
                can_create_order=is_valid,
                confidence=overall_confidence,
                missing_fields=missing_critical,
                order=order,
                field_confidence=confidence_scores,
                warnings=validation_result.get("warnings", []),
                extraction_metadata={
                    "source_type": source_type,
                    "model": self.model_name,
                    "timestamp": datetime.now().isoformat(),
                    "steps": self.extraction_steps
                }
            )

            logger.info(f"Extraction complete. Can create order: {is_valid}")
            yield {"status": "complete", "result": result.model_dump(), "step": 5, "total_steps": 5}

        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            yield {"status": "error", "error": str(e)}

    def _last(self, events: Iterator[Dict[str, Any]]) -> Dict[str, Any]:
        """Drain a streaming generator and return its final yielded event"""
        event = None
        for event in events:
            pass
        return event

    def _extract_with_llm(self, text: str) -> Dict[str, Any]:
        """Use LLM to extract initial structured data"""
        prompt = get_extraction_prompt(text)

        # Call LLM
        response = self.llm.invoke(prompt)

        # Try to parse JSON from response
        try:
            # Extract JSON from response (may be wrapped in markdown)
            json_str = self._extract_json_from_response(response)
            data = json.loads(json_str)
            return data
        except Exception as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            # Return minimal structure
            return {
                "customer_name": None,
                "items": [],
                "raw_response": response
            }

    def _extract_with_llm_chunked_streaming(self, chunks: List[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """Run LLM extraction per chunk and merge, yielding progress per chunk (PDFs too long for one prompt)"""
        merged: Dict[str, Any] = {}
        all_items = []

        for chunk in chunks:
            message = f"Analyzing chunk {chunk['chunk_id'] + 1}/{len(chunks)}"
            self._log_step(message)
            yield {"status": "progress", "message": message}

            data = self._extract_with_llm(chunk["text"])

            items = data.pop("items", None)
            if items:
                all_items.extend(items)

            for key, value in data.items():
                if value and not merged.get(key):
                    merged[key] = value

        merged["items"] = self._dedupe_items(all_items)
        yield {"status": "complete", "data": merged}

    def _extract_with_llm_chunked(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Collect the chunked-streaming extraction into a single merged dict"""
        return self._last(self._extract_with_llm_chunked_streaming(chunks))["data"]

    def _dedupe_items(self, items: List[Dict]) -> List[Dict]:
        """Drop items repeated across overlapping chunks"""
        seen = set()
        deduped = []
        for item in items:
            key = (item.get("name"), item.get("quantity"), item.get("price"))
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        return deduped

    def _refine_with_tools(self, text: str, initial_data: Dict) -> Dict[str, Any]:
        """Use tools to refine and fill gaps in extracted data"""
        refined = initial_data.copy()

        from .tools import (
            extract_customer_info, extract_items, extract_addresses,
            extract_dates, extract_financial_info
        )

        # Refine customer info if missing
        if not refined.get("customer_name"):
            customer_data = extract_customer_info(text)
            refined.update({k: v for k, v in customer_data.items() if v})

        # Refine items if missing or incomplete
        if not refined.get("items") or len(refined["items"]) == 0:
            items_data = extract_items(text)
            if items_data:
                refined["items"] = items_data

        # Add addresses
        if not refined.get("shipping_address"):
            address_data = extract_addresses(text)
            refined.update({k: v for k, v in address_data.items() if v})

        # Add dates
        if not refined.get("order_date"):
            dates_data = extract_dates(text)
            refined.update({k: v for k, v in dates_data.items() if v})

        # Add financial info
        if not refined.get("total_amount"):
            financial_data = extract_financial_info(text)
            refined.update({k: v for k, v in financial_data.items() if v})

        return refined

    def _validate_extraction(self, data: Dict) -> Dict[str, Any]:
        """Validate the extracted data"""
        from .tools import validate_order_data
        return validate_order_data(data)

    def _calculate_confidence(self, data: Dict, original_text: str) -> Dict[str, float]:
        """Calculate confidence scores for extracted fields"""
        from .tools import calculate_confidence
        result = calculate_confidence(data, original_text)
        return result.get("field_confidence", {})

    def _build_order(self, data: Dict) -> Order:
        """Build Order object from extracted data"""
        # Build items
        items = []
        for item_data in data.get("items", []):
            items.append(OrderItem(**item_data))

        # Build order
        order_dict = {
            "customer_name": data.get("customer_name"),
            "customer_email": data.get("customer_email"),
            "customer_phone": data.get("customer_phone"),
            "company_name": data.get("company_name"),
            "contact_person": data.get("contact_person"),
            "items": items,
            "shipping_address": data.get("shipping_address"),
            "billing_address": data.get("billing_address"),
            "order_date": data.get("order_date"),
            "delivery_date": data.get("delivery_date"),
            "due_date": data.get("due_date"),
            "subtotal": data.get("subtotal"),
            "tax_amount": data.get("tax_amount"),
            "shipping_cost": data.get("shipping_cost"),
            "discount": data.get("discount"),
            "total_amount": data.get("total_amount"),
            "currency": data.get("currency", "USD"),
            "payment_terms": data.get("payment_terms"),
            "payment_method": data.get("payment_method"),
            "order_number": data.get("order_number"),
            "invoice_number": data.get("invoice_number"),
            "reference": data.get("reference"),
            "notes": data.get("notes"),
            "special_instructions": data.get("special_instructions"),
            "extras": data.get("extras", {})
        }

        return Order(**order_dict)

    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from LLM response (may be wrapped in markdown)"""
        # Remove markdown code blocks if present
        response = response.strip()

        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()

        # Find JSON object boundaries
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1

        if start_idx != -1 and end_idx != 0:
            return response[start_idx:end_idx]

        return response

    def _log_step(self, message: str):
        """Log an extraction step"""
        step = {
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        self.extraction_steps.append(step)
        logger.info(f"Step: {message}")

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result"""
        return {
            "can_create_order": False,
            "confidence": 0.0,
            "missing_fields": CRITICAL_FIELDS,
            "order": Order().model_dump(),
            "field_confidence": {},
            "warnings": [f"Extraction failed: {error_message}"],
            "extraction_metadata": {
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            }
        }

    def process_pdf(self, pdf_file) -> Dict[str, Any]:
        """
        Process PDF and extract order

        Args:
            pdf_file: PDF file path or file-like object

        Returns:
            Extraction result
        """
        result = None
        pdf_info = None

        for event in self.process_pdf_streaming(pdf_file):
            if "pdf_info" in event:
                pdf_info = event["pdf_info"]
            if event["status"] == "complete":
                result = event["result"]
            elif event["status"] == "error":
                result = self._create_error_result(event["error"])

        if pdf_info:
            result["extraction_metadata"]["pdf_info"] = pdf_info

        return result

    def process_pdf_streaming(self, pdf_file) -> Iterator[Dict[str, Any]]:
        """
        Process PDF and extract order, yielding progress updates as extraction proceeds
        (same event shape as extract_order_streaming, plus per-chunk progress for long PDFs)
        """
        yield {"status": "starting", "message": "Initializing extraction"}
        logger.info("Processing PDF file")

        yield {"status": "extracting", "message": "Processing PDF"}
        pdf_result = self.pdf_processor.process_pdf(pdf_file)

        if not pdf_result["success"]:
            error = f"PDF processing failed: {pdf_result.get('error')}"
            logger.error(error)
            yield {"status": "error", "error": error}
            return

        text = pdf_result["text"]
        table_text = ""

        if pdf_result["tables"]:
            table_text = self.pdf_processor.format_tables_as_text(pdf_result["tables"])
            text = f"{text}\n\n{table_text}"

        pdf_info = {
            "num_pages": pdf_result["metadata"].get("num_pages"),
            "num_chunks": pdf_result["num_chunks"],
            "num_tables": len(pdf_result["tables"])
        }

        self.extraction_steps = []
        try:
            chunks = pdf_result["chunks"]
            if len(chunks) > 1:
                logger.info(f"PDF split into {len(chunks)} chunks for extraction")
                if table_text:
                    # keep tables visible to the LLM by folding them into the last chunk
                    chunks = chunks[:-1] + [{**chunks[-1], "text": chunks[-1]["text"] + "\n\n" + table_text}]

                extracted_data = None
                for chunk_event in self._extract_with_llm_chunked_streaming(chunks):
                    if chunk_event["status"] == "complete":
                        extracted_data = chunk_event["data"]
                    else:
                        yield {"status": "extracting", "message": chunk_event.get("message", "Analyzing chunk")}
            else:
                self._log_step("Analyzing input and extracting fields")
                extracted_data = self._extract_with_llm(text)

            yield {"status": "progress", "data": extracted_data, "step": 1, "total_steps": 5, "pdf_info": pdf_info}
        except Exception as e:
            logger.error(f"Error during PDF extraction: {e}")
            yield {"status": "error", "error": str(e), "pdf_info": pdf_info}
            return

        for event in self._run_pipeline_streaming(extracted_data, text, source_type="pdf"):
            if "pdf_info" not in event:
                event["pdf_info"] = pdf_info
            yield event
