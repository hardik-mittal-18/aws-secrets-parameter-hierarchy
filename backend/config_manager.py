import time
import random
import threading
import boto3
from botocore.exceptions import ClientError

REGION = "ap-south-1"

class ConfigManager:
    def __init__(self, environment="dev", ttl=60):
        self.environment = environment
        self.prefix = f"/myapp/{environment}/"
        self.ttl = ttl

        self.ssm = boto3.client(
            "ssm",
            region_name=REGION
        )

        self._cache = None
        self._cache_time = 0
        self._lock = threading.Lock()

    def _load_from_ssm(self):
        parameters = {}

        paginator = self.ssm.get_paginator(
            "get_parameters_by_path"
        )

        for attempt in range(5):
            try:
                pages = paginator.paginate(
                    Path=self.prefix,
                    Recursive=True,
                    WithDecryption=True
                )

                for page in pages:
                    for parameter in page.get("Parameters", []):
                        key = parameter["Name"].replace(
                            self.prefix, ""
                        )
                        parameters[key] = parameter["Value"]

                return parameters

            except ClientError as error:
                error_code = error.response["Error"]["Code"]

                if error_code not in (
                    "ThrottlingException",
                    "TooManyRequestsException",
                    "ProvisionedThroughputExceededException"
                ):
                    raise

                if attempt == 4:
                    raise

                delay = (2 ** attempt) + random.uniform(0, 0.5)

                print(
                    f"SSM throttled. "
                    f"Retrying in {delay:.2f}s..."
                )

                time.sleep(delay)

    def get_config(self):
        now = time.time()

        if (
            self._cache is not None
            and now - self._cache_time < self.ttl
        ):
            return self._cache

        with self._lock:
            now = time.time()

            if (
                self._cache is not None
                and now - self._cache_time < self.ttl
            ):
                return self._cache

            self._cache = self._load_from_ssm()
            self._cache_time = time.time()

            return self._cache

    def refresh(self):
        with self._lock:
            self._cache = self._load_from_ssm()
            self._cache_time = time.time()

        return self._cache

    def clear_cache(self):
        with self._lock:
            self._cache = None
            self._cache_time = 0


if __name__ == "__main__":
    manager = ConfigManager("dev", ttl=60)

    config = manager.get_config()

    print("Environment: DEV")
    print("Loaded parameters:")

    for key, value in sorted(config.items()):
        print(f"{key} = {value}")
