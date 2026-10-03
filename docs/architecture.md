# AWS Secrets and Parameter Hierarchy Design

## Overview

This project provides a secure configuration and secrets management architecture for DEV, TEST, and PROD environments using AWS-native services.

## Architecture

- AWS Systems Manager Parameter Store stores non-sensitive configuration.
- AWS Secrets Manager stores passwords, database credentials, API keys, and tokens.
- AWS KMS provides encryption for sensitive secrets.
- IAM provides environment-specific access control.
- EC2 hosts the Flask backend.
- Boto3 allows the backend to securely access AWS services through the EC2 IAM role.

## Environment Hierarchy

/myapp/dev/
/myapp/test/
/myapp/prod/

Each environment has its own IAM permissions.

## Application Flow

Application
→ Flask Backend
→ Configuration Manager
→ Parameter Store / Secrets Manager
→ KMS

## Performance

The Configuration Manager uses GetParametersByPath for batch retrieval, a TTL cache to reduce repeated requests, and exponential backoff with jitter for throttling conditions.
