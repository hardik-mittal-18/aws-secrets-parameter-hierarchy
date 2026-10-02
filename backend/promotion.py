import argparse
import boto3

REGION = "ap-south-1"
ACCOUNT_ID = "840941914492"
PROMOTION_ROLE_ARN = (
    f"arn:aws:iam::{ACCOUNT_ID}:role/MyApp-Promotion-Role"
)

BASE_PATH = "/myapp"


def get_promotion_clients():
    sts = boto3.client("sts", region_name=REGION)

    assumed = sts.assume_role(
        RoleArn=PROMOTION_ROLE_ARN,
        RoleSessionName="parameter-promotion"
    )

    credentials = assumed["Credentials"]

    ssm = boto3.client(
        "ssm",
        region_name=REGION,
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"]
    )

    return ssm


def get_parameters(ssm, environment):
    path = f"{BASE_PATH}/{environment}/"

    paginator = ssm.get_paginator("get_parameters_by_path")

    parameters = {}

    for page in paginator.paginate(
        Path=path,
        Recursive=True,
        WithDecryption=True
    ):
        for item in page["Parameters"]:
            name = item["Name"]
            relative_name = name.replace(path, "", 1)

            parameters[relative_name] = {
                "value": item["Value"],
                "type": item["Type"]
            }

    return parameters


def compare_environments(ssm, source, target):
    source_params = get_parameters(ssm, source)
    target_params = get_parameters(ssm, target)

    all_keys = sorted(
        set(source_params) | set(target_params)
    )

    changes = []

    for key in all_keys:
        source_item = source_params.get(key)
        target_item = target_params.get(key)

        source_value = source_item["value"] if source_item else None
        target_value = target_item["value"] if target_item else None

        if source_value != target_value:
            changes.append({
                "parameter": key,
                "source": source_value,
                "target": target_value
            })

    return changes, source_params


def promote(ssm, source, target, changes, source_params):
    for change in changes:
        key = change["parameter"]
        source_item = source_params[key]

        parameter_name = f"{BASE_PATH}/{target}/{key}"

        ssm.put_parameter(
            Name=parameter_name,
            Value=source_item["value"],
            Type=source_item["type"],
            Overwrite=True
        )

        print(f"PROMOTED: {parameter_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Safe parameter promotion between environments"
    )

    parser.add_argument("source", choices=["dev", "test"])
    parser.add_argument("target", choices=["test", "prod"])
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Approve and apply the promotion"
    )

    args = parser.parse_args()

    if args.source == args.target:
        raise SystemExit("Source and target environments must differ.")

    print(
        f"Using promotion role: {PROMOTION_ROLE_ARN}"
    )

    ssm = get_promotion_clients()

    print()
    print(
        f"Comparing {args.source.upper()} -> {args.target.upper()}"
    )
    print("=" * 50)

    changes, source_params = compare_environments(
        ssm,
        args.source,
        args.target
    )

    if not changes:
        print("No configuration changes detected.")
        return

    print(f"Changes detected: {len(changes)}")
    print()

    for change in changes:
        print(f"Parameter: {change['parameter']}")
        print(f"  {args.source.upper()}: {change['source']}")
        print(f"  {args.target.upper()}: {change['target']}")
        print()

    if not args.approve:
        print("DRY RUN ONLY.")
        print("No parameters were modified.")
        print()
        print(
            f"Run: python3 backend/promotion.py "
            f"{args.source} {args.target} --approve"
        )
        return

    print("APPROVAL RECEIVED.")
    print(
        f"Promoting {args.source.upper()} -> "
        f"{args.target.upper()}..."
    )

    promote(
        ssm,
        args.source,
        args.target,
        changes,
        source_params
    )

    print()
    print("Promotion completed successfully.")


if __name__ == "__main__":
    main()
