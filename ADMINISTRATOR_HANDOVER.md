# Irish Energy Analytics - Option B IAM Administrator Handover

## Overview

This document provides the administrative instructions for implementing the Option B IAM architecture for the Irish Energy Analytics Data Platform.

## Required IAM Roles and Policies

### 1. CloudFormation Service Role

**Role Name:** `irish-energy-cfn-service-role`

**Trust Policy** (`irish-energy-cfn-service-role-trust-policy.json`):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudformation.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

**Permissions Policy** (`irish-energy-cfn-service-role-permissions-policy.json`):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::cdk-hnb659fds-assets-851725545966-eu-west-1/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:PassRole"
            ],
            "Resource": [
                "arn:aws:iam::851725545966:role/IngestionRoleFC2D3E97",
                "arn:aws:iam::851725545966:role/TransformationRoleE86D7364"
            ],
            "Condition": {
                "StringEquals": {
                    "iam:PassedToService": [
                        "lambda.amazonaws.com"
                    ]
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:CreateFunction",
                "lambda:UpdateFunctionCode",
                "lambda:DeleteFunction",
                "lambda:GetFunction",
                "lambda:AddPermission",
                "lambda:RemovePermission",
                "lambda:TagResource",
                "lambda:UntagResource"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "events:PutRule",
                "events:DeleteRule",
                "events:DescribeRule",
                "events:PutTargets",
                "events:RemoveTargets"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:GetRole"
            ],
            "Resource": [
                "arn:aws:iam::851725545966:role/IngestionRoleFC2D3E97",
                "arn:aws:iam::851725545966:role/TransformationRoleE86D7364"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:PutRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:AttachRolePolicy",
                "iam:DetachRolePolicy",
                "iam:UpdateAssumeRolePolicy"
            ],
            "Resource": [
                "arn:aws:iam::851725545966:role/IngestionRoleFC2D3E97",
                "arn:aws:iam::851725545966:role/TransformationRoleE86D7364"
            ]
        }
    ]
}
```

### 2. Deployment Principal Permissions

**Permissions Policy** (`irish-energy-deployment-principal-permissions-policy.json`):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateStack",
                "cloudformation:UpdateStack",
                "cloudformation:DeleteStack",
                "cloudformation:DescribeStacks",
                "cloudformation:DescribeStackResources",
                "cloudformation:DescribeStackEvents",
                "cloudformation:GetTemplate",
                "cloudformation:ValidateTemplate",
                "cloudformation:CreateChangeSet",
                "cloudformation:ExecuteChangeSet"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::cdk-hnb659fds-assets-851725545966-eu-west-1/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:PassRole"
            ],
            "Resource": [
                "arn:aws:iam::851725545966:role/irish-energy-cfn-service-role"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:GetRole"
            ],
            "Resource": [
                "arn:aws:iam::851725545966:role/irish-energy-cfn-service-role"
            ]
        }
    ]
}
```

## Deployment Process

### 1. Bootstrap CDK (One-time setup)

The existing bootstrap command will create the necessary CDK roles:
```bash
cdk bootstrap aws://851725545966/eu-west-1 --profile irish-energy-data-platform-dev
```

### 2. Create Service Role (Administrator Action)

Create the CloudFormation service role with the following commands:
```bash
# Create the service role
aws iam create-role \
  --role-name irish-energy-cfn-service-role \
  --assume-role-policy-document file://irish-energy-cfn-service-role-trust-policy.json

# Attach the permissions policy
aws iam put-role-policy \
  --role-name irish-energy-cfn-service-role \
  --policy-name ServiceRolePermissions \
  --policy-document file://irish-energy-cfn-service-role-permissions-policy.json
```

### 3. Deployment Command

After creating the service role, deploy using:
```bash
cdk deploy --all --role-arn arn:aws:iam::851725545966:role/irish-energy-cfn-service-role --profile irish-energy-data-platform-dev
```

## Verification Commands

### Verify Service Role Configuration
```bash
# Verify role exists and has correct trust policy
aws iam get-role --role-name irish-energy-cfn-service-role

# Verify role has required permissions
aws iam list-role-policies --role-name irish-energy-cfn-service-role
```

### Verify Bootstrap Roles
```bash
# List existing CDK bootstrap roles
aws iam list-roles --query "Roles[?contains(RoleName, 'cdk-hnb659fds')]"
```

### Verify IAM Role Existence
```bash
# Verify execution roles exist
aws iam get-role --role-name IngestionRoleFC2D3E97
aws iam get-role --role-name TransformationRoleE86D7364
```

## Required Prerequisites

1. **AWS CLI configured** with profile `irish-energy-data-platform-dev`
2. **Administrator permissions** to create IAM roles and attach policies
3. **Existing S3 assets bucket**: `cdk-hnb659fds-assets-851725545966-eu-west-1`
4. **Existing S3 data buckets**:
   - `irish-energy-bronze-851725545966-eu-west-1`
   - `irish-energy-silver-851725545966-eu-west-1`
   - `irish-energy-gold-851725545966-eu-west-1`
5. **Existing EventBridge default bus**: `arn:aws:events:eu-west-1:851725545966:event-bus/default`

## Deployment Command Summary

```bash
# 1. Bootstrap CDK (if not already done)
cdk bootstrap aws://851725545966/eu-west-1 --profile irish-energy-data-platform-dev

# 2. Create service role (administrator action)
aws iam create-role \
  --role-name irish-energy-cfn-service-role \
  --assume-role-policy-document file://irish-energy-cfn-service-role-trust-policy.json

aws iam put-role-policy \
  --role-name irish-energy-cfn-service-role \
  --policy-name ServiceRolePermissions \
  --policy-document file://irish-energy-cfn-service-role-permissions-policy.json

# 3. Deploy with service role
cdk deploy --all --role-arn arn:aws:iam::851725545966:role/irish-energy-cfn-service-role --profile irish-energy-data-platform-dev
```

## Post-Deployment Verification

After successful deployment, verify:
1. All CloudFormation stacks are created
2. Lambda functions are created with correct roles
3. EventBridge rules and targets are configured
4. S3 buckets have the expected data
5. CloudWatch logs are accessible
