from __future__ import annotations

import json
import time

import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc

from src.core.config import settings
from src.grpc.generated import venue_directory_pb2, venue_directory_pb2_grpc

_RETRYABLE_STATUS_CODES = ("UNAVAILABLE",)
_SERVICE_CONFIG = json.dumps(
  {
    "methodConfig": [
      {
        "name": [{}],
        "retryPolicy": {
          "maxAttempts": 4,
          "initialBackoff": "0.2s",
          "maxBackoff": "2s",
          "backoffMultiplier": 2,
          "retryableStatusCodes": list(_RETRYABLE_STATUS_CODES),
        },
      }
    ]
  }
)
_CHANNEL_OPTIONS = (
  ("grpc.enable_retries", 1),
  ("grpc.service_config", _SERVICE_CONFIG),
)
_SERVICE_NAME = "ostatki.grpc.v1.VenueDirectoryService"


class CircuitBreakerOpenError(RuntimeError):
  pass


class VenueServiceUnavailableError(RuntimeError):
  pass


class _CircuitBreaker:
  def __init__(self, failure_threshold: int, reset_timeout: float) -> None:
    self._failure_threshold = failure_threshold
    self._reset_timeout = reset_timeout
    self._consecutive_failures = 0
    self._opened_at: float | None = None
    self._state = "closed"

  def before_call(self) -> None:
    if self._state != "open":
      return
    now = time.monotonic()
    if self._opened_at is not None and (now - self._opened_at) >= self._reset_timeout:
      self._state = "half-open"
      return
    raise CircuitBreakerOpenError("Venue gRPC circuit breaker is open")

  def record_success(self) -> None:
    self._state = "closed"
    self._consecutive_failures = 0
    self._opened_at = None

  def record_failure(self) -> None:
    if self._state == "half-open":
      self._open()
      return

    self._consecutive_failures += 1
    if self._consecutive_failures >= self._failure_threshold:
      self._open()

  def _open(self) -> None:
    self._state = "open"
    self._opened_at = time.monotonic()
    self._consecutive_failures = 0


class VenueDirectoryClient:
  def __init__(
    self,
    *,
    host: str,
    port: int,
    timeout: float,
    failure_threshold: int,
    reset_timeout: float,
  ) -> None:
    self._target = f"{host}:{port}"
    self._timeout = timeout
    self._breaker = _CircuitBreaker(failure_threshold, reset_timeout)
    self._channel = grpc.aio.insecure_channel(self._target, options=_CHANNEL_OPTIONS)
    self._stub = venue_directory_pb2_grpc.VenueDirectoryServiceStub(self._channel)
    self._health_stub = health_pb2_grpc.HealthStub(self._channel)

  @classmethod
  def from_settings(cls) -> "VenueDirectoryClient":
    return cls(
      host=settings.GRPC_VENUE_SERVICE_HOST,
      port=settings.GRPC_VENUE_SERVICE_PORT,
      timeout=settings.GRPC_STARTUP_CHECK_TIMEOUT,
      failure_threshold=settings.GRPC_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
      reset_timeout=settings.GRPC_CIRCUIT_BREAKER_RESET_TIMEOUT,
    )

  async def close(self) -> None:
    await self._channel.close()

  async def wait_until_serving(self) -> None:
    try:
      response = await self._health_stub.Check(
        health_pb2.HealthCheckRequest(service=_SERVICE_NAME),
        timeout=self._timeout,
        wait_for_ready=True,
      )
    except grpc.RpcError as exc:
      raise VenueServiceUnavailableError("Venue gRPC health check failed") from exc

    if response.status != health_pb2.HealthCheckResponse.SERVING:
      raise VenueServiceUnavailableError("Venue gRPC service is not serving")

  async def check_venue_exists(self, venue_id: int) -> bool:
    self._breaker.before_call()
    try:
      response = await self._stub.CheckVenueExists(
        venue_directory_pb2.CheckVenueExistsRequest(venue_id=venue_id),
        timeout=self._timeout,
        wait_for_ready=True,
      )
    except grpc.RpcError as exc:
      self._breaker.record_failure()
      raise VenueServiceUnavailableError("Venue gRPC request failed") from exc

    self._breaker.record_success()
    return bool(response.exists)
