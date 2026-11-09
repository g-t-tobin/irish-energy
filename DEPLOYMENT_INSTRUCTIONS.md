# Deployment Instructions for IrishEnergyAnalyticsApi

## Deployment Command
Use the canonical two-phase deployment script from the repository root:
```bash
cd /var/home/gerardthomastobin/Desktop/project/macliammor_it/irish-energy
./deploy_analytics_api.sh
```

A single `cdk deploy` is not safe while the deployed Lambda still has the old fat
code. CloudFormation sends `UpdateFunctionConfiguration` (layers) before
`UpdateFunctionCode`, and Lambda validates layer v3 against the existing fat code:
90,064,061 + 209,290,120 = 299,354,181 bytes, which exceeds 262,144,000. The script
therefore runs two CDK deployments: phase 1 applies the lean code with
`-c attachHeavyLayer=false`, and phase 2 attaches layer version 3.

## Pre-deployment Verification
Run deployment from the repository root. `infrastructure/cdk.json` and
`infrastructure/cdk.out` are a second entrypoint; both now resolve the same lean asset,
but the root configuration is canonical. Previously stale `infrastructure/cdk.out`
output referenced the old 41be... fat asset.

Before running the deployment command, verify:
1. AWS credentials are configured for account 851725545966 in eu-west-1
2. You have sufficient IAM permissions for CDK deployment
3. The synthesized API asset is the lean package, not a package containing boto3:
   `python3 -c "import json; t=json.load(open('cdk.out/IrishEnergyAnalyticsApi.template.json')); print([v['Properties']['Code'] for v in t['Resources'].values() if v['Type']=='AWS::Lambda::Function'])"`
4. The staged API asset extracts to 10,283,252 bytes (3,433,487 compressed)
5. Layer version 3 extracts to 209,290,120 bytes
6. Combined uncompressed size is 219,573,372 bytes, leaving 42,570,628 bytes headroom
   under the 262,144,000-byte limit
7. Layer ARN is correct: arn:aws:lambda:eu-west-1:851725545966:layer:PandasPyArrowLayerE9BA9DDA:3

## Deployment Scope
- Only deploys: IrishEnergyAnalyticsApi stack
- Does NOT deploy: Ingestion, DataLake, Monitoring, Registry stacks
- Does NOT modify: IAM policies, existing layer versions, S3 resources
- Does NOT affect: Unrelated infrastructure

## Post-deployment Verification Steps
1. Confirm CloudFormation stack status is UPDATE_COMPLETE
2. Retrieve actual Lambda function name from CloudFormation outputs
3. Verify Lambda function shows correct layer attached and code size is about 3.4 MB compressed
4. Test all six endpoints:
   - GET /health
   - GET /demand
   - GET /weather
   - GET /generation
   - GET /quality
   - GET /summary
5. Check CloudWatch logs for startup errors
6. Validate that responses contain real Gold data where appropriate
