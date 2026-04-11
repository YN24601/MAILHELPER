"""
Data models for email analysis results.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import List


class Priority(str, Enum):
    """Email priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(str, Enum):
    """Email categories."""
    WORK = "work"
    SCHOOL = "school"
    PERSONAL = "personal"
    OTHER = "other"


@dataclass
class EmailAnalysisResult:
    """Standard format for email analysis results."""
    subject: str
    mailbox: str
    summary: str
    priority: Priority
    category: Category
    actions_to_take: List[str]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['category'] = self.category.value
        return data


@dataclass
class AnalysisConfig:
    """Configuration for email analysis."""
    model: str
    temperature: float = 0.7
    max_tokens: int = 500
    prompt_template: str = ""
    api_key: str = None
