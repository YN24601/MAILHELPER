"""
Email analysis pipeline: load -> preprocess -> analyze -> store.
"""

import json
import logging
from typing import List, Optional
from pathlib import Path

from mail_helper.analysis_models import EmailAnalysisResult, AnalysisConfig
from mail_helper.text_processor import TextProcessor
from mail_helper.llm_analyzer import LLMAnalyzer

logger = logging.getLogger(__name__)


class EmailPipeline:
    """Pipeline for analyzing emails and storing results."""

    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.analyzer = LLMAnalyzer(config)
        self.results: List[EmailAnalysisResult] = []

    def process_emails(self, emails: List[dict], output_file: str = None) -> List[EmailAnalysisResult]:
        """Analyze a list of email dicts and optionally save the results.

        Args:
            emails: Fetched emails as dicts (each may carry a 'mailbox' field)
            output_file: Optional path to save results

        Returns:
            List of analysis results
        """
        self.results = []
        try:
            logger.info(f"Processing {len(emails)} emails")

            for email_data in emails:
                result = self._process_single_email(email_data)
                if result:
                    self.results.append(result)

            if output_file:
                self._save_results(output_file)

            logger.info(f"Successfully analyzed {len(self.results)} emails")
            return self.results

        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            return []

    def process_email_file(self, input_file: str, output_file: str = None) -> List[EmailAnalysisResult]:
        """Process all emails from a JSON file.

        Args:
            input_file: Path to JSON file with fetched emails
            output_file: Optional path to save results

        Returns:
            List of analysis results
        """
        try:
            emails = self._load_emails(input_file)
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            return []
        return self.process_emails(emails, output_file)

    def _process_single_email(self, email_data: dict) -> Optional[EmailAnalysisResult]:
        """Process a single email through the analysis pipeline."""
        try:
            # Extract email subject and mailbox
            subject = email_data.get('subject', 'No Subject')
            mailbox = email_data.get('mailbox', 'Unknown')
                        
            # Preprocess text
            prepared_text = TextProcessor.prepare_for_analysis(email_data)
            logger.debug(f"Prepared text for analysis: {prepared_text}...") 
            # Analyze with LLM
            result = self.analyzer.analyze(prepared_text, subject, mailbox)
            
            if result:
                logger.debug(f"Analyzed email {subject}: priority={result.priority.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing email: {str(e)}")
            return None

    @staticmethod
    def _load_emails(input_file: str) -> List[dict]:
        """Load emails from JSON file."""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Support both list and dict with 'emails' key
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'emails' in data:
                return data['emails']
            else:
                raise ValueError("Invalid JSON format")
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file not found: {input_file}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in file: {input_file}")

    def _save_results(self, output_file: str) -> None:
        """Save analysis results to JSON file."""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            results_data = [result.to_dict() for result in self.results]
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Results saved to {output_file}")

        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
