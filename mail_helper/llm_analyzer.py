"""
LLM analyzer module for email analysis using different providers.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional
from string import Template
from litellm import completion

from mail_helper.analysis_models import EmailAnalysisResult, Priority, Category, AnalysisConfig

logger = logging.getLogger(__name__)


class BaseLLMAnalyzer(ABC):
    """Abstract base class for LLM analyzers."""

    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.logger = logger

    @abstractmethod
    def analyze(self, email_text: str, subject: str, mailbox: str) -> Optional[EmailAnalysisResult]:
        """Analyze email content and return analysis result."""
        pass

    def _build_prompt(self, email_text: str) -> str:
        """Build analysis prompt using string.Template to avoid JSON braces conflict."""
        from textwrap import dedent
        default_template = dedent("""Analyze the following email and provide:
    1. A concise summary (1-3 sentences)
    2. Priority level (high, medium, or low)
    3. Category (work, school, personal, or other)
    4. Specific actions to take (as a list)

    Email content:
    $email_text

    Respond in JSON format:
    {
        "summary": "...",
        "priority": "high|medium|low",
        "category": "work|school|personal|other",
        "actions_to_take": ["action1", "action2"]
    }""").strip()

        raw_prompt = self.config.prompt_template or default_template
        
        # use Template to substitute email_text while keeping JSON structure intact
        return Template(raw_prompt).safe_substitute(email_text=email_text)

    def _parse_response(self, response_text: str, subject: str, mailbox: str) -> Optional[EmailAnalysisResult]:
        """ Universal response parser that can be used by all analyzers. """
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON block found")
            
            data = json.loads(response_text[start:end])
        # TODO: use try-except to set default values for failed fields
            return EmailAnalysisResult(
                subject=subject,
                mailbox=mailbox,
                summary=data.get('summary', ''),
                priority=Priority(data.get('priority', 'medium').lower()),
                category=Category(data.get('category', 'other').lower()),
                actions_to_take=data.get('actions_to_take', []),
            )
        except Exception as e:
            self.logger.error(f"Parse error for {subject}: {e}")
            return None

class UniversalLLMAnalyzer(BaseLLMAnalyzer):
    """Universal LLM analyzer that can work with any provider by using the same prompt and response parsing logic."""

    def analyze(self, email_text: str, subject: str, mailbox: str) -> Optional[EmailAnalysisResult]:
        """Analyze email content and return analysis result."""
        try:
            prompt = self._build_prompt(email_text)
            
            # auto detect provider based on config and call completion function
            response = completion(
                model=self.config.model, # e.g. "openai/gpt-4", "gemini/gemini-pro"
                messages=[{"role": "user", "content": prompt}],
                api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                
            )
            
            response_text = response.choices[0].message.content
            return self._parse_response(response_text, subject, mailbox)
            
        except Exception as e:
            self.logger.error(f"Universal analysis error: {str(e)}")
            return None       


class AnalyzerFactory:
    """Factory for creating LLM analyzers."""
    @staticmethod
    def get_analyzer(config: AnalysisConfig) -> BaseLLMAnalyzer:
        return UniversalLLMAnalyzer(config)
