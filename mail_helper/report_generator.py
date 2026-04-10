"""
Report generator for email analysis results.
"""

import logging
from typing import List
from pathlib import Path

from mail_helper.analysis_models import EmailAnalysisResult

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate Markdown reports from analysis results."""

    @staticmethod
    def generate_report(
        results: List[EmailAnalysisResult],
        output_file: str = None,
        sort_by_priority: bool = True
    ) -> str:
        """Generate Markdown report from analysis results.
        
        Args:
            results: List of EmailAnalysisResult objects
            output_file: Optional path to save report
            sort_by_priority: If True, sort by priority (high to low)
            
        Returns:
            Markdown report as string
        """
        if not results:
            report = "# Email Analysis Report\n\nNo emails to analyze.\n"
        else:
            # Sort results if requested
            if sort_by_priority:
                priority_order = {'high': 0, 'medium': 1, 'low': 2}
                results = sorted(results, key=lambda r: priority_order.get(r.priority.value, 3))
            
            report = ReportGenerator._build_report(results)
        
        # Save to file if specified
        if output_file:
            ReportGenerator._save_report(report, output_file)
        
        return report

    @staticmethod
    def _build_report(results: List[EmailAnalysisResult]) -> str:
        """Build Markdown report content."""
        lines = [
            "# Email Analysis Report\n",
            f"**Total Emails Analyzed:** {len(results)}\n",
        ]
        
        # Summary statistics
        stats = ReportGenerator._calculate_stats(results)
        lines.append("\n## Summary Statistics\n")
        
        lines.append("### By Mailbox")
        for mailbox, count in stats['by_mailbox'].items():
            lines.append(f"- **{mailbox}:** {count}")
        
        lines.append("\n### By Priority")
        for priority, count in stats['by_priority'].items():
            lines.append(f"- **{priority.capitalize()}:** {count}")
        
        lines.append("\n### By Category")
        for category, count in stats['by_category'].items():
            lines.append(f"- **{category.capitalize()}:** {count}")
        
        # Detailed results
        lines.append("\n## Analysis Details\n")
        
        current_priority = None
        for result in results:
            # Add priority header when priority changes
            if result.priority.value != current_priority:
                current_priority = result.priority.value
                lines.append(f"\n### {current_priority.upper()} Priority Emails\n")
            
            lines.extend(ReportGenerator._format_email_result(result))
        
        return '\n'.join(lines)

    @staticmethod
    def _format_email_result(result: EmailAnalysisResult) -> List[str]:
        """Format a single email result as Markdown."""
        lines = [
            f"#### {result.subject or 'No Subject'}",
            f"- **Mailbox:** {result.mailbox}",
            f"- **Category:** {result.category.value.capitalize()}",
            f"- **Summary:** {result.summary}",
        ]
        
        if result.actions_to_take:
            lines.append("- **Actions to Take:**")
            for action in result.actions_to_take:
                lines.append(f"  - {action}")
        
        lines.append("")  # Empty line for spacing
        return lines

    @staticmethod
    def _calculate_stats(results: List[EmailAnalysisResult]) -> dict:
        """Calculate summary statistics."""
        stats = {
            'by_priority': {'high': 0, 'medium': 0, 'low': 0},
            'by_category': {'work': 0, 'school': 0, 'personal': 0, 'other': 0},
            'by_mailbox': {},
        }
        
        for result in results:
            stats['by_priority'][result.priority.value] += 1
            stats['by_category'][result.category.value] += 1
            
            # Count by mailbox
            mailbox = result.mailbox
            if mailbox not in stats['by_mailbox']:
                stats['by_mailbox'][mailbox] = 0
            stats['by_mailbox'][mailbox] += 1
        
        return stats

    @staticmethod
    def _save_report(report: str, output_file: str) -> None:
        """Save report to Markdown file."""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"Report saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
