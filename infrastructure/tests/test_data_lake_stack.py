"""Tests for Data Lake Stack"""

import unittest
from aws_cdk import (
    App,
    Environment,
    assertions
)
from stacks.data_lake_stack import DataLakeStack


class TestDataLakeStack(unittest.TestCase):

    def test_stack_creation(self):
        """Test that DataLakeStack can be created"""
        app = App()
        env = Environment(account="123456789012", region="eu-west-1")

        # Create stack
        stack = DataLakeStack(app, "TestStack", env=env)

        # Synthesize
        template = assertions.Template.from_stack(stack)

        # Assert that S3 bucket is created
        template.resource_count_is("AWS::S3::Bucket", 1)

        # Assert bucket properties
        template.has_resource_properties("AWS::S3::Bucket", {
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [
                    {
                        "ServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        }
                    }
                ]
            },
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True
            }
        })

        # Assert outputs
        template.has_output("DataLakeBucketName", {})
        template.has_output("DataLakeBucketArn", {})
        template.has_output("BronzePrefix", {})
        template.has_output("SilverPrefix", {})
        template.has_output("GoldPrefix", {})


if __name__ == '__main__':
    unittest.main()