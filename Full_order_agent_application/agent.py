"""
Order Extraction Agent
Main LangChain agent that orchestrates the extraction workflow
"""

import json
import logging
from typing import Dict, Any, List, Optional, Iterator
from datetime import datetime

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish

from schema import (
    Order, ExtractionResult, OrderItem,
    validate_order_completeness, calculate_overall_confidence,
    CRITICAL_FIELDS, CONFIDENCE_THRESHOLD_HIGH
)
from tools import AGENT_TOOLS
from prompts import SYSTEM_PROMPT, get_extraction_prompt
from pdf_processor import PDFProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderExtractionAgent:
    """
    Main agent for extracting order information from unstructured text
    """
    
    def __init__(
        self,
        model_name: str = "llama3.2:latest",
        temperature: float = 0.1,
        ollama_base_url: str = "http://localhost:11434",
        verbose: bool = True
    ):
        """
        Initialize the order extraction agent
        
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
        self.pdf_processor = PDFProcessor()
        
        # Agent state
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
            # Step 1: Initial extraction using LLM
            self._log_step("Analyzing input and extracting fields")
            extracted_data = self._extract_with_llm(input_text)
            
            # Step 2: Use tools for specific field extraction
            self._log_step("Refining extraction with specialized tools")
            refined_data = self._refine_with_tools(input_text, extracted_data)
            
            # Step 3: Validate extracted data
            self._log_step("Validating extracted data")
            validation_result = self._validate_extraction(refined_data)
            
            # Step 4: Calculate confidence scores
            self._log_step("Calculating confidence scores")
            confidence_scores = self._calculate_confidence(refined_data, input_text)
            
            # Step 5: Create final order object
            self._log_step("Building final order structure")
            order = self._build_order(refined_data)
            
            # Step 6: Determine if order can be created
            is_valid, missing_critical = validate_order_completeness(order)
            
            # Calculate overall confidence
            overall_confidence = calculate_overall_confidence(confidence_scores)
            
            # Build result
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
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            return self._create_error_result(str(e))
    
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
            # Step 1: Initial extraction
            yield {"status": "extracting", "message": "Analyzing input with LLM"}
            extracted_data = self._extract_with_llm(input_text)
            yield {"status": "progress", "data": extracted_data, "step": 1, "total_steps": 5}
            
            # Step 2: Refine with tools
            yield {"status": "refining", "message": "Refining with specialized tools"}
            refined_data = self._refine_with_tools(input_text, extracted_data)
            yield {"status": "progress", "data": refined_data, "step": 2, "total_steps": 5}
            
            # Step 3: Validate
            yield {"status": "validating", "message": "Validating extracted data"}
            validation_result = self._validate_extraction(refined_data)
            yield {"status": "progress", "data": validation_result, "step": 3, "total_steps": 5}
            
            # Step 4: Calculate confidence
            yield {"status": "scoring", "message": "Calculating confidence scores"}
            confidence_scores = self._calculate_confidence(refined_data, input_text)
            yield {"status": "progress", "data": confidence_scores, "step": 4, "total_steps": 5}
            
            # Step 5: Build final result
            yield {"status": "finalizing", "message": "Building final order"}
            order = self._build_order(refined_data)
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
            
            yield {"status": "complete", "result": result.model_dump(), "step": 5, "total_steps": 5}
            
        except Exception as e:
            logger.error(f"Error during streaming extraction: {e}")
            yield {"status": "error", "error": str(e)}
    
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
    
    def _refine_with_tools(self, text: str, initial_data: Dict) -> Dict[str, Any]:
        """Use tools to refine and fill gaps in extracted data"""
        refined = initial_data.copy()
        
        # Import tool functions
        from tools import (
            extract_customer_info, extract_items, extract_addresses,
            extract_dates, extract_financial_info
        )
        
        # Refine customer info if missing
        if not refined.get("customer_name"):
            customer_result = extract_customer_info.invoke({"text": text})
            customer_data = json.loads(customer_result)
            refined.update({k: v for k, v in customer_data.items() if v})
        
        # Refine items if missing or incomplete
        if not refined.get("items") or len(refined["items"]) == 0:
            items_result = extract_items.invoke({"text": text})
            items_data = json.loads(items_result)
            if items_data:
                refined["items"] = items_data
        
        # Add addresses
        if not refined.get("shipping_address"):
            address_result = extract_addresses.invoke({"text": text})
            address_data = json.loads(address_result)
            refined.update({k: v for k, v in address_data.items() if v})
        
        # Add dates
        if not refined.get("order_date"):
            dates_result = extract_dates.invoke({"text": text})
            dates_data = json.loads(dates_result)
            refined.update({k: v for k, v in dates_data.items() if v})
        
        # Add financial info
        if not refined.get("total_amount"):
            financial_result = extract_financial_info.invoke({"text": text})
            financial_data = json.loads(financial_result)
            refined.update({k: v for k, v in financial_data.items() if v})
        
        return refined
    
    def _validate_extraction(self, data: Dict) -> Dict[str, Any]:
        """Validate the extracted data"""
        from tools import validate_order_data
        
        validation_result = validate_order_data.invoke({
            "order_json": json.dumps(data)
        })
        
        return json.loads(validation_result)
    
    def _calculate_confidence(self, data: Dict, original_text: str) -> Dict[str, float]:
        """Calculate confidence scores for extracted fields"""
        from tools import calculate_confidence
        
        confidence_result = calculate_confidence.invoke({
            "extracted_data": json.dumps(data),
            "original_text": original_text
        })
        
        result = json.loads(confidence_result)
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
        logger.info("Processing PDF file")
        
        # Process PDF
        pdf_result = self.pdf_processor.process_pdf(pdf_file)
        
        if not pdf_result["success"]:
            return self._create_error_result(f"PDF processing failed: {pdf_result.get('error')}")
        
        # Extract from text
        text = pdf_result["text"]
        
        # Add table data if present
        if pdf_result["tables"]:
            table_text = self.pdf_processor.format_tables_as_text(pdf_result["tables"])
            text = f"{text}\n\n{table_text}"
        
        # Extract order
        result = self.extract_order(text, source_type="pdf")
        
        # Add PDF metadata
        result["extraction_metadata"]["pdf_info"] = {
            "num_pages": pdf_result["metadata"].get("num_pages"),
            "num_chunks": pdf_result["num_chunks"],
            "num_tables": len(pdf_result["tables"])
        }
        
        return result
