import boto3
import sys

REGION = "ap-south-1"
ACCOUNT_ID = "840941914492"
PROMOTION_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/MyApp-Promotion-Role"


def get_ssm_client():
    sts = boto3.client("sts", region_name=REGION)

    assumed = sts.assume_role(
        RoleArn=PROMOTION_ROLE_ARN,
        RoleSessionName="parameter-rollback"
    )

    credentials = assumed["Credentials"]

    return boto3.client(
        "ssm",
        region_name=REGION,
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"]
    )


def rollback(environment, parameter, version):
    ssm = get_ssm_client()

    parameter_name = f"/myapp/{environment}/{parameter}"

    previous = ssm.get_parameter(
        Name=f"{parameter_name}:{version}",
        WithDecryption=True
    )

    value = previous["Parameter"]["Value"]

    ssm.put_parameter(
        Name=parameter_name,
        Value=value,
        Type="String",
        Overwrite=True
    )

    print("ROLLBACK COMPLETED")
    print(f"Environment : {environment.upper()}")
    print(f"Parameter   : {parameter}")
    print(f"Restored from version: {version}")
    print(f"New parameter version created.")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: python3 scripts/rollback.py "
            "<environment> <parameter> <version>"
        )
        print(
            "Example: python3 scripts/rollback.py "
            "prod app/log_level 1"
        )
        sys.exit(1)

    rollback(
        sys.argv[1],
        sys.argv[2],
        int(sys.argv[3])
    )
