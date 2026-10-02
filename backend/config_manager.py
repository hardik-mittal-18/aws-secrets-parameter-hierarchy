import time
import random
import boto3
from botocore.exceptions import ClientError


REGION = "ap-south-1"
BASE_PATH = "/myapp"

CACHE_TTL_SECONDS = 60
MAX_RETRIES = 5
BASE_BACKOFF_SECONDS = 0.5


class ConfigManager:
    """
    Loads application configuration from AWS Systems Manager
    Parameter Store using an environment-specific hierarchy.

    Example:
        /myapp/dev/...
        /myapp/test/...
        /myapp/prod/...
    """

    def __init__(self, environment, region=REGION, cache_ttl=CACHE_TTL_SECONDS):
        environment = environment.lower().strip()

        if environment not in {"dev", "test", "prod"}:
            raise ValueError(
                "Environment must be one of: dev, test, prod"
            )

        self.environment = environment
        self.region = region
        self.cache_ttl = cache_ttl

        self.ssm = boto3.client(
            "ssm",
            region_name=self.region
        )

        self._cache = None
        self._cache_time = 0

    @property
    def parameter_path(self):
        return f"{BASE_PATH}/{self.environment}/"

    def _get_parameters_with_retry(self):
        """
        Retrieve all parameters under the environment path.

        Uses GetParametersByPath to reduce the number of API calls
        and retries throttling/transient AWS errors with exponential
        backoff and jitter.
        """

        parameters = []
        next_token = None

        for attempt in range(MAX_RETRIES):
            try:
                parameters = []
                next_token = None

                while True:
                    request = {
                        "Path": self.parameter_path,
                        "Recursive": True,
                        "WithDecryption": False
                    }

                    if next_token:
                        request["NextToken"] = next_token

                    response = self.ssm.get_parameters_by_path(**request)

                    parameters.extend(response.get("Parameters", []))

                    next_token = response.get("NextToken")

                    if not next_token:
                        break

                return parameters

            except ClientError as error:
                error_code = error.response.get(
                    "Error", {}
                ).get("Code", "")

                retryable_errors = {
                    "ThrottlingException",
                    "TooManyUpdates",
                    "InternalServerError",
                    "ServiceUnavailable"
                }

                if error_code not in retryable_errors:
                    raise

                if attempt == MAX_RETRIES - 1:
                    raise

                delay = (
                    BASE_BACKOFF_SECONDS * (2 ** attempt)
                    + random.uniform(0, 0.25)
                )

                time.sleep(delay)

        return parameters

    def load_config(self, force_refresh=False):
        """
        Load configuration from Parameter Store.

        Cached configuration is returned when the cache is still valid.
        Set force_refresh=True to bypass the cache.
        """

        current_time = time.time()

        cache_valid = (
            self._cache is not None
            and current_time - self._cache_time < self.cache_ttl
        )

        if cache_valid and not force_refresh:
            return self._cache.copy()

        parameters = self._get_parameters_with_retry()

        config = {}

        for parameter in parameters:
            name = parameter["Name"]

            relative_name = name.replace(
                self.parameter_path,
                "",
                1
            )

            config[relative_name] = parameter["Value"]

        self._cache = config
        self._cache_time = time.time()

        return config.copy()

    def clear_cache(self):
        """Clear the in-memory configuration cache."""

        self._cache = None
        self._cache_time = 0


if __name__ == "__main__":
    manager = ConfigManager("dev")

    config = manager.load_config()

    print("Environment:", manager.environment)
    print("Parameter path:", manager.parameter_path)
    print("Parameters loaded:", len(config))

    for key, value in sorted(config.items()):
        print(f"{key} = {value}")

