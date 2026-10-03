import time
import boto3
from backend.config_manager import ConfigManager

REGION = "ap-south-1"
PARAMETER = "/myapp/dev/app/port"
ITERATIONS = 20

ssm = boto3.client("ssm", region_name=REGION)

print("=" * 60)
print("PARAMETER STORE BEFORE / AFTER BENCHMARK")
print("=" * 60)

# BEFORE: direct API call every time
start = time.perf_counter()

for _ in range(ITERATIONS):
    ssm.get_parameter(Name=PARAMETER)

direct_time = time.perf_counter() - start

# AFTER: cached configuration
manager = ConfigManager("dev", ttl=60)

start = time.perf_counter()

for _ in range(ITERATIONS):
    manager.get_config()

cached_time = time.perf_counter() - start

print(f"Iterations             : {ITERATIONS}")
print(f"Before - direct SSM    : {direct_time:.4f} seconds")
print(f"After  - cached config : {cached_time:.4f} seconds")

if direct_time > 0:
    reduction = (1 - cached_time / direct_time) * 100
    print(f"Time reduction         : {reduction:.2f}%")

print()
print("BEFORE : application calls Parameter Store repeatedly")
print("AFTER  : application retrieves configuration once and caches it")
print("Retry/backoff protects temporary throttling.")
print("=" * 60)
