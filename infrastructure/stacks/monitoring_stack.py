from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    Duration,
    CfnOutput,
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

        # Create alarm for transformation failures
        transformation_failure_alarm = cloudwatch.Alarm(
            self, "TransformationFailureAlarm",
            alarm_name="IrishEnergyTransformationFailure",
            metric=cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Errors",
                dimensions_map={"FunctionName": "SilverTransformationFunction"},
                statistic="sum",
                period=Duration.minutes(5)
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="Alert when transformation functions fail"
        )

        # Add alarm action
        transformation_failure_alarm.add_alarm_action(cw_actions.SnsAction(alert_topic))

        # Create alarm for data freshness issues
        data_freshness_alarm = cloudwatch.Alarm(
            self, "DataFreshnessAlarm",
            alarm_name="IrishEnergyDataFreshnessIssue",
            metric=cloudwatch.Metric(
                namespace="IrishEnergy/DataFreshness",
                metric_name="LastProcessedDate",
                statistic="average",
                period=Duration.hours(1)
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description="Alert when data freshness exceeds 24 hours"
        )

        # Add alarm action
        data_freshness_alarm.add_alarm_action(cw_actions.SnsAction(alert_topic))

        # Create alarm for data volume issues
        data_volume_alarm = cloudwatch.Alarm(
            self, "DataVolumeAlarm",
            alarm_name="IrishEnergyDataVolumeIssue",
            metric=cloudwatch.Metric(
                namespace="IrishEnergy/DataVolume",
                metric_name="TotalRecordsProcessed",
                statistic="sum",
                period=Duration.hours(1)
            ),
            threshold=1000,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            alarm_description="Alert when data volume is below expected threshold"
        )

        # Add alarm action
        data_volume_alarm.add_alarm_action(cw_actions.SnsAction(alert_topic))

        # Create custom metric for data quality scores
        data_quality_metric = cloudwatch.Metric(
            namespace="IrishEnergy/DataQuality",
            metric_name="DataQualityScore",
            statistic="average",
            period=Duration.hours(1)
        )

        # Create custom metric for transformation success rate
        transformation_success_metric = cloudwatch.Metric(
            namespace="IrishEnergy/Transformation",
            metric_name="TransformationSuccessRate",
            statistic="average",
            period=Duration.hours(1)
        )

        # Create dashboard for monitoring
        dashboard = cloudwatch.Dashboard(
            self, "DataPlatformDashboard",
            dashboard_name="IrishEnergyDataPlatformDashboard"
        )

        # Add widgets to dashboard
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Data Quality Score Over Time",
                left=[data_quality_metric],
                region=self.region,
                width=12,
                height=6
            ),
            cloudwatch.GraphWidget(
                title="Transformation Success Rate",
                left=[transformation_success_metric],
                region=self.region,
                width=12,
                height=6
            ),
            cloudwatch.GraphWidget(
                title="Data Freshness",
                left=[
                    cloudwatch.Metric(
                        namespace="IrishEnergy/DataFreshness",
                        metric_name="LastProcessedDate",
                        statistic="average",
                        period=Duration.hours(1)
                    )
                ],
                region=self.region,
                width=12,
                height=6
            ),
            cloudwatch.GraphWidget(
                title="Data Volume Processed",
                left=[
                    cloudwatch.Metric(
                        namespace="IrishEnergy/DataVolume",
                        metric_name="TotalRecordsProcessed",
                        statistic="sum",
                        period=Duration.hours(1)
                    )
                ],
                region=self.region,
                width=12,
                height=6
            )
        )

        # Output the dashboard URL
        CfnOutput(
            self, "DashboardUrl",
            value=f"https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard.dashboard_name}",
            description="URL to the Data Platform Dashboard"
        )