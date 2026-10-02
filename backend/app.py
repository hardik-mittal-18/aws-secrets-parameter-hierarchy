from flask import Flask, jsonify
import boto3
import json

app = Flask(__name__)

REGION = "ap-south-1"

ssm = boto3.client("ssm", region_name=REGION)
secrets = boto3.client("secretsmanager", region_name=REGION)
sts = boto3.client("sts", region_name=REGION)


@app.route("/")
def home():
    return jsonify({
        "project": "AWS Secrets and Parameter Hierarchy Design",
        "environment": "DEV",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/config")
def config():
    port = ssm.get_parameter(
        Name="/myapp/dev/app/port"
    )["Parameter"]["Value"]

    log_level = ssm.get_parameter(
        Name="/myapp/dev/app/log_level"
    )["Parameter"]["Value"]

    payment_enabled = ssm.get_parameter(
        Name="/myapp/dev/features/payment_enabled"
    )["Parameter"]["Value"]

    return jsonify({
        "environment": "DEV",
        "configuration": {
            "port": port,
            "log_level": log_level,
            "payment_enabled": payment_enabled
        }
    })


@app.route("/secret-status")
def secret_status():
    response = secrets.get_secret_value(
        SecretId="/myapp/dev/database"
    )

    secret = json.loads(response["SecretString"])

    return jsonify({
        "environment": "DEV",
        "secret_retrieved": True,
        "available_keys": list(secret.keys()),
        "password_exposed": False
    })


@app.route("/identity")
def identity():
    identity = sts.get_caller_identity()

    return jsonify({
        "aws_identity": identity["Arn"],
        "authentication": "EC2 IAM Role"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
)
