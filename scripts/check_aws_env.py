#!/usr/bin/env python3
"""Check AWS environment configuration"""

import boto3
import os
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def check_aws_credentials():
    """Check if AWS credentials are properly configured"""
    try:
        # Try to create a session
        session = boto3.Session(profile_name=os.getenv('AWS_PROFILE', 'default'))
        
        # Try to get credentials
        credentials = session.get_credentials()
        if not credentials:
            print("❌ No AWS credentials found")
            return False
            
        # Try to make a simple AWS call
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials are valid")
        print(f"   Account: {identity['Account']}")
        print(f"   User: {identity['Arn']}")
        return True
        
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        return False
    except PartialCredentialsError:
        print("❌ Incomplete AWS credentials")
        return False
    except Exception as e:
        print(f"❌ Error checking AWS credentials: {e}")
        return False

def check_aws_region():
    """Check AWS region configuration"""
    region = os.getenv('AWS_REGION', 'eu-west-1')
    print(f"✅ AWS Region: {region}")
    return True

def main():
    """Main function to check AWS environment"""
    print("Checking AWS Environment Configuration...")
    print("=" * 40)
    
    success = True
    success &= check_aws_credentials()
    success &= check_aws_region()
    
    print("=" * 40)
    if success:
        print("✅ All AWS environment checks passed")
    else:
        print("❌ Some AWS environment checks failed")
    
    return success

if __name__ == "__main__":
    main()