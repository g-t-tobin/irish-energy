"""
Quality scoring system for Irish Energy Analytics Data Platform
"""
from typing import List, Dict, Any
from .models import QualityRuleResult, QualityStatus


class QualityScorer:
    """
    Manages quality scoring calculations and methodologies
    """

    @staticmethod
    def calculate_score(rule_results: List[QualityRuleResult],
                       rule_weights: Dict[str, float] = None) -> float:
        """
        Calculate weighted quality score based on rule results

        Args:
            rule_results: List of rule execution results
            rule_weights: Optional dictionary of rule weights

        Returns:
            float: Quality score between 0 and 100
        """
        if not rule_results:
            return 100.0

        if rule_weights is None:
            rule_weights = {}

        total_weighted_score = 0.0
        total_weight = 0.0

        for result in rule_results:
            # Get weight for this rule, default to 1.0 if not specified
            weight = rule_weights.get(result.rule_name, 1.0)
            total_weight += weight

            # Calculate contribution based on status
            if result.status == QualityStatus.PASS:
                score_contribution = 1.0 * weight
            elif result.status == QualityStatus.WARNING:
                score_contribution = 0.8 * weight
            elif result.status == QualityStatus.FAIL:
                score_contribution = 0.0 * weight
            else:  # SKIPPED
                score_contribution = 1.0 * weight  # Skipped rules don't penalize

            total_weighted_score += score_contribution

        if total_weight == 0.0:
            return 100.0

        score = (total_weighted_score / total_weight) * 100.0
        return round(score, 2)

    @staticmethod
    def determine_status(rule_results: List[QualityRuleResult]) -> QualityStatus:
        """
        Determine overall quality status based on rule results

        Args:
            rule_results: List of rule execution results

        Returns:
            QualityStatus: Overall quality status
        """
        if not rule_results:
            return QualityStatus.PASS

        # Check for any critical failures (FAIL status)
        critical_failures = [r for r in rule_results if r.status == QualityStatus.FAIL]
        if critical_failures:
            return QualityStatus.FAIL

        # Check for warnings
        warnings = [r for r in rule_results if r.status == QualityStatus.WARNING]
        if warnings:
            return QualityStatus.WARNING

        # All checks passed
        return QualityStatus.PASS

    @staticmethod
    def generate_score_explanation(rule_results: List[QualityRuleResult]) -> str:
        """
        Generate human-readable explanation of the quality score

        Args:
            rule_results: List of rule execution results

        Returns:
            str: Explanation of score calculation
        """
        if not rule_results:
            return "No quality checks were performed"

        passed = sum(1 for r in rule_results if r.status == QualityStatus.PASS)
        failed = sum(1 for r in rule_results if r.status == QualityStatus.FAIL)
        warning = sum(1 for r in rule_results if r.status == QualityStatus.WARNING)
        skipped = sum(1 for r in rule_results if r.status == QualityStatus.SKIPPED)

        explanation = f"Quality assessment: {passed} passed, {warning} warnings, {failed} failed, {skipped} skipped"

        if failed > 0:
            explanation += ". Critical failures detected - data quality is compromised"
        elif warning > 0:
            explanation += ". Warnings detected - data quality may need attention"
        else:
            explanation += ". All checks passed - data quality is acceptable"

        return explanation