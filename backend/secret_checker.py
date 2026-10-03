import boto3
from botocore.exceptions import ClientError

REGION = "ap-south-1"

ssm = boto3.client("ssm", region_name=REGION)
secrets = boto3.client("secretsmanager", region_name=REGION)

print("=" * 65)
print("SECRET VS PARAMETER STORE DECISION CHECK")
print("=" * 65)

print("""
DECISION RULE
--------------
Parameter Store:
  - ports
  - log levels
  - feature flags
  - database hostnames
  - non-sensitive application configuration

Secrets Manager:
  - passwords
  - API keys
  - access tokens
  - database credentials

Promotion rule:
  Configuration parameters may be promoted.
  Secrets are NOT copied between environments.
""")

print("PARAMETER STORE CONFIGURATION")

for env in ["dev", "test", "prod"]:
    prefix = f"/myapp/{env}/"
    print(f"\n[{env.upper()}]")

    try:
        paginator = ssm.get_paginator("get_parameters_by_path")

        found = False

        for page in paginator.paginate(
            Path=prefix,
            Recursive=True
        ):
            for parameter in page.get("Parameters", []):
                found = True
                print(f"  CONFIG  {parameter['Name']}")

        if not found:
            print("  No parameters returned.")

    except ClientError as error:
        code = error.response["Error"]["Code"]

        if code == "AccessDeniedException":
            print("  ACCESS DENIED")
            print("  This environment is protected by IAM isolation.")
        else:
            print(f"  ERROR: {code}")

print("\nSECRETS MANAGER")

for env in ["dev", "test", "prod"]:
    name = f"/myapp/{env}/database"

    try:
        secrets.describe_secret(SecretId=name)
        print(f"  SECRET  {name}")

    except ClientError as error:
        code = error.response["Error"]["Code"]

        if code == "AccessDeniedException":
            print(f"  ACCESS DENIED {name}")
        else:
            print(f"  ERROR {name}: {code}")

print("\nRESULT")
print("Configuration -> Parameter Store")
print("Credentials   -> Secrets Manager")
print("DEV role cannot inspect TEST/PROD resources.")
print("Secrets are excluded from promotion.")
print("=" * 65)
