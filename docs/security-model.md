# Security Model

## Environment Isolation

The project follows least-privilege IAM access.

DEV resources are accessible only by the DEV role.
TEST resources are accessible only by the TEST role.
PROD resources are accessible only by the PROD role.

## Parameter Store

Parameter Store is used for non-sensitive configuration such as:

- Application ports
- Log levels
- Feature flags
- Database hostnames

## Secrets Manager

Secrets Manager is used for sensitive information such as:

- Database passwords
- API keys
- Access tokens
- Database credentials

## Encryption

Secrets are encrypted using AWS KMS.

## Credential Management

The application does not contain hardcoded AWS access keys. EC2 obtains AWS permissions through its IAM role.

## Promotion Security

Configuration promotion requires a dry run and explicit approval.

Secrets are not automatically copied between environments.

## Rollback

Parameter versions are used to restore previous configuration values when required.
