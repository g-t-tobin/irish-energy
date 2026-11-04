from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    Duration,
)
from constructs import Construct

class MonitoringStack(Stack):
    """Creates monitoring infrastructure"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create SNS topic for alerts
        alert_topic = sns.Topic(
            self, "DataPlatformAlerts",
            topic_name="irish-energy-data-platform-alerts"
        )

        # Create alarm for data ingestion failures
        ingestion_failure_alarm = cloudwatch.Alarm(
            self, "IngestionFailureAlarm",
            alarm_name="IrishEnergyIngestionFailure",
            metric=cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Errors",
                dimensions_map={"FunctionName": "EirGridIngestionFunction"},
                statistic="sum",
                period=Duration.minutes(5)
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="Alert when ingestion functions fail"
        )

        # Add alarm action
        ingestion_failure_alarm.add_alarm_action(cw_actions.SnsAction(alert_topic))

        # Create alarm for data quality issues
        data_quality_alarm = cloudwatch.Alarm(
            self, "DataQualityAlarm",
            alarm_name="IrishEnergyDataQualityIssue",
            metric=cloudwatch.Metric(
                namespace="IrishEnergy/DataQuality",
                metric_name="DataQualityScore",
                statistic="average",
                period=Duration.hours(1)
            ),
            threshold=0.9,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            alarm_description="Alert when data quality drops below threshold"
        )

        # Add alarm action
        data_quality_alarm.add_alarm_action(cw_actions.SnsAction(alert_topic))