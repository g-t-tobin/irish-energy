from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_lambda as _lambda,
    Duration,
    RemovalPolicy,
    CfnOutput,
    ArnFormat,
    aws_lambda_layer as _lambda_layer
)
from constructs import Construct
import json
from pathlib import Path

# Define the build paths to match the ingestion stack
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRANSFORMATION_BUILD_PATH = PROJECT_ROOT / "build" / "transformation_package"

class OrchestrationStack(Stack):
    """Creates infrastructure for automated pipeline orchestration."""

    def __init__(self, scope: Construct, construct_id: str, eirgrid_ingestion_fn: _lambda.IFunction, openmeteo_ingestion_fn: _lambda.IFunction, transformation_fn: _lambda.IFunction, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create DynamoDB table for pipeline state tracking
        pipeline_state_table = dynamodb.Table(
            self,
            "PipelineStateTable",
            table_name="irish-energy-pipeline-state",
            partition_key=dynamodb.Attribute(
                name="execution_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
            time_to_live_attribute="ttl"
        )

        # Add a global secondary index for querying recent executions
        pipeline_state_table.add_global_secondary_index(
            index_name="ExecutionStatusIndex",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="start_time",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Create IAM role for Step Functions execution
        step_functions_role = iam.Role(
            self,
            "PipelineExecutionRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
        )

        # Create transformation role with appropriate permissions for validation
        transformation_role = iam.Role(
            self,
            "TransformationRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # Grant minimal required permissions to the Step Functions role
        # Allow invoking Lambda functions
        step_functions_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "lambda:InvokeFunction"
            ],
            resources=[
                eirgrid_ingestion_fn.function_arn,
                openmeteo_ingestion_fn.function_arn,
                transformation_fn.function_arn
            ]
        ))

        # Grant Step Functions access to the DynamoDB table
        pipeline_state_table.grant_read_write_data(step_functions_role)

        # Grant transformation role access to S3 buckets for validation
        # Since we're using imported buckets, we'll hardcode the bucket names
        # that match the ones defined in the ingestion stack
        transformation_role.add_to_policy(iam.PolicyStatement(
            actions=["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
            resources=[
                "arn:aws:s3:::irish-energy-bronze-851725545966-eu-west-1",
                "arn:aws:s3:::irish-energy-bronze-851725545966-eu-west-1/*",
                "arn:aws:s3:::irish-energy-silver-851725545966-eu-west-1",
                "arn:aws:s3:::irish-energy-silver-851725545966-eu-west-1/*",
                "arn:aws:s3:::irish-energy-gold-851725545966-eu-west-1",
                "arn:aws:s3:::irish-energy-gold-851725545966-eu-west-1/*",
            ],
        ))

        # Create a role for the orchestration Lambda that will be used to trigger workflows
        orchestration_role = iam.Role(
            self,
            "OrchestrationRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # Grant orchestration role access to DynamoDB
        pipeline_state_table.grant_read_write_data(orchestration_role)

        # Create pandas layer for validation function
        pandas_layer = _lambda_layer.LayerVersion(
            self,
            "PandasLayer",
            content="build/lambda_layers/pandas-layer.zip",
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[_lambda.Architecture.X86_64],
            description="Pandas library layer for data validation functions"
        )

        # Create validation function for checking data layers
        validation_function = _lambda.Function(
            self,
            "DataValidationFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="src.validation.lambda_handler.lambda_handler",
            code=_lambda.Code.from_asset(str(TRANSFORMATION_BUILD_PATH)),
            timeout=Duration.minutes(5),
            role=transformation_role,
            environment={
                "BRONZE_BUCKET": "irish-energy-bronze-851725545966-eu-west-1",
                "SILVER_BUCKET": "irish-energy-silver-851725545966-eu-west-1",
                "GOLD_BUCKET": "irish-energy-gold-851725545966-eu-west-1",
            },
            layers=[pandas_layer]
        )

        # Import existing Lambda functions from ingestion stack
        # This assumes the existing infrastructure is already deployed
        # We'll reference the functions by name rather than creating them here
        eirgrid_ingestion_fn_arn = self.format_arn(
            service="lambda",
            resource="function",
            arn_format=ArnFormat.COLON_RESOURCE_NAME,
            resource_name="EirGridIngestionFunction"
        )

        openmeteo_ingestion_fn_arn = self.format_arn(
            service="lambda",
            resource="function",
            arn_format=ArnFormat.COLON_RESOURCE_NAME,
            resource_name="OpenMeteoIngestionFunction"
        )

        transformation_fn_arn = self.format_arn(
            service="lambda",
            resource="function",
            arn_format=ArnFormat.COLON_RESOURCE_NAME,
            resource_name="DataTransformationFunction"
        )

        # Create a Lambda function to update pipeline state
        pipeline_state_updater = _lambda.Function(
            self,
            "PipelineStateUpdater",
            function_name="PipelineStateUpdater",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
from datetime import datetime
from decimal import Decimal

def lambda_handler(event, context):
    # Extract parameters from the event
    execution_id = event.get('execution_id')
    status = event.get('status')
    stage = event.get('stage')
    start_time = event.get('start_time')
    end_time = event.get('end_time')
    error_message = event.get('error_message')

    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('irish-energy-pipeline-state')

    # Prepare update expression
    update_expression = "SET last_updated = :last_updated"
    expression_attribute_values = {
        ':last_updated': datetime.utcnow().isoformat()
    }

    # Update execution-level attributes
    if status:
        update_expression += ", overall_status = :status"
        expression_attribute_values[':status'] = status

    if start_time:
        update_expression += ", started_at = :start_time"
        expression_attribute_values[':start_time'] = start_time

    if end_time:
        update_expression += ", completed_at = :end_time"
        expression_attribute_values[':end_time'] = end_time

    if error_message:
        update_expression += ", error_message = :error_message"
        expression_attribute_values[':error_message'] = error_message

    # Update stage-level attributes if stage is provided
    if stage:
        stage_attr_name = f"{stage}_status"
        update_expression += f", {stage_attr_name} = :stage_status"
        expression_attribute_values[':stage_status'] = status

        if start_time:
            stage_start_attr_name = f"{stage}_started_at"
            update_expression += f", {stage_start_attr_name} = :stage_start_time"
            expression_attribute_values[':stage_start_time'] = start_time

        if end_time:
            stage_end_attr_name = f"{stage}_completed_at"
            update_expression += f", {stage_end_attr_name} = :stage_end_time"
            expression_attribute_values[':stage_end_time'] = end_time

        if error_message:
            stage_error_attr_name = f"{stage}_error_message"
            update_expression += f", {stage_error_attr_name} = :stage_error_message"
            expression_attribute_values[':stage_error_message'] = error_message

    # Update the item
    table.update_item(
        Key={'execution_id': execution_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Pipeline state updated')
    }
            """),
            role=orchestration_role,
            timeout=Duration.seconds(30),
        )

        # Grant the Lambda function access to DynamoDB
        pipeline_state_table.grant_read_write_data(pipeline_state_updater)

        # Create the Step Functions state machine with proper workflow definition
        # Using CDK constructs to build the workflow

        # Start state - initialize execution
        initialize_execution = sfn_tasks.LambdaInvoke(
            self,
            "InitializeExecution",
            lambda_function=pipeline_state_updater,
            payload=sfn.TaskInput.from_object({
                "execution_id.$": "$.execution_id",
                "status": "RUNNING",
                "start_time.$": "$$.Execution.StartTime"
            }),
            result_path="$.initialization_result"
        )

        # Parallel ingestion - EirGrid and Open-Meteo
        eirgrid_ingestion = sfn_tasks.LambdaInvoke(
            self,
            "IngestEirGrid",
            lambda_function=eirgrid_ingestion_fn,
            payload=sfn.TaskInput.from_object({
                "date.$": "$.pipeline_date",
                "execution_id.$": "$.execution_id"
            }),
            result_path="$.eirgrid_result"
        )

        openmeteo_ingestion = sfn_tasks.LambdaInvoke(
            self,
            "IngestOpenMeteo",
            lambda_function=openmeteo_ingestion_fn,
            payload=sfn.TaskInput.from_object({
                "date.$": "$.pipeline_date",
                "execution_id.$": "$.execution_id"
            }),
            result_path="$.openmeteo_result"
        )

        # Parallel state for ingestion
        parallel_ingestion = sfn.Parallel(
            self,
            "ParallelIngestion",
            result_path="$.ingestion_results"
        ).branch(eirgrid_ingestion).branch(openmeteo_ingestion)

        # Bronze validation
        bronze_validation = sfn_tasks.LambdaInvoke(
            self,
            "ValidateBronzeData",
            lambda_function=validation_function,
            payload=sfn.TaskInput.from_object({
                "validation_type": "bronze",
                "data_type.$": "$.data_type",
                "date.$": "$.pipeline_date",
                "execution_id.$": "$.execution_id"
            }),
            result_path="$.validation_bronze_result"
        )

        # Process demand data first (since it's handled by EirGrid ingestion)
        demand_transformation = sfn_tasks.LambdaInvoke(
            self,
            "TransformDemandToSilver",
            lambda_function=transformation_fn,
            payload=sfn.TaskInput.from_object({
                "transformation_type": "silver",
                "data_type": "demand",
                "date.$": "$.pipeline_date",
                "execution_id.$": "$.execution_id"
            }),
            result_path="$.demand_transformation_result"
        )

        # Process weather data (handled by Open-Meteo ingestion)
        weather_transformation = sfn_tasks.LambdaInvoke(
            self,
            "TransformWeatherToSilver",
            lambda_function=transformation_fn,
            payload=sfn.TaskInput.from_object({
                "transformation_type": "silver",
                "data_type": "weather",
                "date.$": "$.pipeline_date",
                "execution_id.$": "$.execution_id"
            }),
            result_path="$.weather_transformation_result"
        )

        # Process generation data (handled by EirGrid ingestion)
        generation_transformation = sfn_tasks.LambdaInvoke(
            self,
            "TransformGenerationToSilver",
            lambda_function=transformation_fn,
            payload=sfn.TaskInput.from_object({
                "transformation_type": "silver",
                "data_type": "generation",
                "date.$": "$.pipeline_date",
                "execution_id.$": "$.execution_id"
            }),
            result_path="$.generation_transformation_result"
        )

        # Process all transformations in parallel
        parallel_silver_transformations = sfn.Parallel(
            self,
            "ParallelSilverTransformations",
            result_path="$.silver_transformations_results"
        ).branch(demand_transformation).branch(weather_transformation).branch(generation_transformation)

        # Silver validation
        silver_validation = sfn_tasks.LambdaInvoke(
            self,
            "ValidateSilverData",
            lambda_function=validation_function,
            payload=sfn.TaskInput.from_object({
                "validation_type": "silver",
                "data_type.$": "$.data_type",
                "date.$": "$.pipeline_date",
                "execution_id.$": "$.execution_id"
            }),
            result_path="$.validation_silver_result"
        )

        # Process gold transformations for each data type
        gold_demand_transformation = sfn_tasks.LambdaInvoke(
            self,
            "GenerateGoldDemand",
            lambda_function=transformation_fn,
            payload=sfn.TaskInput.from_object({
                "transformation_type": "gold",
                "data_type": "demand",
                "date.$": "$.pipeline_date",
                "execution_id.$": "$.execution_id"
            }),
            result_path="$.gold_demand_transformation_result"
        )

        gold_weather_transformation = sfn_tasks.LambdaInvoke(
            self,
            "GenerateGoldWeather",
            lambda_function=transformation_fn,
            payload=sfn.TaskInput.from_object({
                "transformation_type": "gold",
                "data_type": "weather",
                "date.$": "$.pipeline_date",
                "execution_id.$": "$.execution_id"
            }),
            result_path="$.gold_weather_transformation_result"
        )

        gold_generation_transformation = sfn_tasks.LambdaInvoke(
            self,
            "GenerateGoldGeneration",
            lambda_function=transformation_fn,
            payload=sfn.TaskInput.from_object({
                "transformation_type": "gold",
                "data_type": "generation",
                "date.$": "$.pipeline_date",
                "execution_id.$": "$.execution_id"
            }),
            result_path="$.gold_generation_transformation_result"
        )

        # Process all gold transformations in parallel
        parallel_gold_transformations = sfn.Parallel(
            self,
            "ParallelGoldTransformations",
            result_path="$.gold_transformations_results"
        ).branch(gold_demand_transformation).branch(gold_weather_transformation).branch(gold_generation_transformation)

        # Gold validation
        gold_validation = sfn_tasks.LambdaInvoke(
            self,
            "ValidateGoldData",
            lambda_function=validation_function,
            payload=sfn.TaskInput.from_object({
                "validation_type": "gold",
                "data_type.$": "$.data_type",
                "date.$": "$.pipeline_date",
                "execution_id.$": "$.execution_id"
            }),
            result_path="$.validation_gold_result"
        )

        # Final state - mark execution successful
        mark_successful = sfn_tasks.LambdaInvoke(
            self,
            "MarkExecutionSuccessful",
            lambda_function=pipeline_state_updater,
            payload=sfn.TaskInput.from_object({
                "execution_id.$": "$.execution_id",
                "status": "SUCCEEDED",
                "end_time.$": "$$.State.EnteredTime"
            }),
            result_path="$.mark_success_result"
        )

        # Error handling - update execution failure
        update_execution_failure = sfn_tasks.LambdaInvoke(
            self,
            "UpdateExecutionFailure",
            lambda_function=pipeline_state_updater,
            payload=sfn.TaskInput.from_object({
                "execution_id.$": "$.execution_id",
                "status": "FAILED",
                "error_message.$": "$.Error",
                "end_time.$": "$$.State.EnteredTime"
            }),
            result_path="$.update_failure_result"
        )

        # Create the complete workflow definition
        definition = sfn.Chain.start(initialize_execution)\
            .next(parallel_ingestion)\
            .next(bronze_validation)\
            .next(parallel_silver_transformations)\
            .next(silver_validation)\
            .next(parallel_gold_transformations)\
            .next(gold_validation)\
            .next(mark_successful)

        # Create the state machine
        state_machine = sfn.StateMachine(
            self,
            "PipelineStateMachine",
            definition=definition,
            state_machine_name="IrishEnergyPipelineStateMachine",
            role=step_functions_role,
            timeout=Duration.hours(2),
        )

        # Output the state machine ARN
        CfnOutput(
            self,
            "StateMachineArn",
            value=state_machine.state_machine_arn,
            description="ARN of the pipeline state machine"
        )

        # Output the DynamoDB table name
        CfnOutput(
            self,
            "PipelineStateTableName",
            value=pipeline_state_table.table_name,
            description="Name of the pipeline state tracking table"
        )