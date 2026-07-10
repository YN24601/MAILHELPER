"""
LLM analyzer module for email analysis using different providers.
"""

import json
import logging
from typing import Optional
from string import Template
from textwrap import dedent
from litellm import completion

from mail_helper.analysis_models import EmailAnalysisResult, Priority, Category, AnalysisConfig

logger = logging.getLogger(__name__)

# Built once at import instead of per-email in the analysis hot path
_DEFAULT_PROMPT_TEMPLATE = dedent("""You are an efficient email assistant. The email below includes the sender (From), date (Date), subject (Subject) and body (Body); analyze it using all four.

    Email content:
    $email_text

    When assigning priority, combine the sender's identity with how urgent the content is. Apply these rules from top to bottom and stop at the first match:
    - high: sender is a professor/advisor/teaching assistant, or an official notice from your school or company; or the body contains a clear deadline, an interview, a bill/payment, or an account-security alert that you must handle promptly yourself.
    - medium: routine correspondence from classmates, colleagues or friends, or messages that need a reply but are not urgent; general course/project updates.
    - low: advertisements, marketing, subscription digests, social-media notifications, or automated system notices that need no action from you.
    When unsure: if the sender looks like a real personal address, use medium; if it looks automated or bulk (e.g. no-reply, newsletter, notifications), use low.

    Other requirements:
    1. summary: summarize the email in 1-3 concise sentences.
    2. category: classify as work/school/personal/other.
    3. actions_to_take: list concrete follow-up actions only for high priority; otherwise return an empty list [].

    Return strict JSON only, where priority must be exactly one of high, medium, low and category must be exactly one of work, school, personal, other, with no extra explanatory text:
    {
        "summary": "...",
        "priority": "high",
        "category": "school",
        "actions_to_take": ["action1", "action2"]
    }""").strip()


class LLMAnalyzer:
    """LLM analyzer that works with any provider via litellm's unified completion API."""

    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.logger = logger

    def _build_prompt(self, email_text: str) -> str:
        """Build analysis prompt using string.Template to avoid JSON braces conflict."""
        raw_prompt = self.config.prompt_template or _DEFAULT_PROMPT_TEMPLATE

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

    def analyze(self, email_text: str, subject: str, mailbox: str) -> Optional[EmailAnalysisResult]:
        """Analyze email content and return analysis result."""
        try:
            prompt = self._build_prompt(email_text)

            # auto detect provider based on config and call completion function
            response = completion(
                model=self.config.model,  # e.g. "openai/gpt-4", "gemini/gemini-pro"
                messages=[{"role": "user", "content": prompt}],
                api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            response_text = response.choices[0].message.content
            return self._parse_response(response_text, subject, mailbox)

        except Exception as e:
            self.logger.error(f"Analysis error: {str(e)}")
            return None
