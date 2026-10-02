from flask import Flask, jsonify
import boto3
import json

from backend.config_manager import ConfigManager

app = Flask(__name__)

REGION = "ap-south-1"

secrets = boto3.client(
    "secretsmanager",
    region_name=REGION
)

sts = boto3.client(
    "sts",
    region_name=REGION
)

# Configuration is loaded from Parameter Store
# and cached for 60 seconds.
config_manager = ConfigManager(
    environment="dev",
    ttl=60
)


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
    configuration = config_manager.get_config()

    return jsonify({
        "environment": "DEV",
        "configuration": {
            "port": configuration.get("app/port"),
            "log_level": configuration.get("app/log_level"),
            "payment_enabled": configuration.get(
                "features/payment_enabled"
            )
        },
        "source": "AWS Parameter Store",
        "cache_ttl_seconds": 60
    })


@app.route("/config/refresh")
def refresh_config():
    configuration = config_manager.refresh()

    return jsonify({
        "environment": "DEV",
        "status": "configuration refreshed",
        "parameters_loaded": len(configuration)
    })


@app.route("/secret-status")
def secret_status():
    response = secrets.get_secret_value(
        SecretId="/myapp/dev/database"
    )

    secret = json.loads(
        response["SecretString"]
    )

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
