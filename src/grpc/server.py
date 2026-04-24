from __future__ import annotations

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from src.core.config import settings
from src.grpc.generated import auth_identity_pb2_grpc
from src.grpc.service import AuthIdentityGrpcService

_SERVICE_NAME = "ostatki.grpc.v1.AuthIdentityService"


async def start_grpc_server() -> tuple[grpc.aio.Server, health.HealthServicer]:
  server = grpc.aio.server()
  health_servicer = health.aio.HealthServicer()

  auth_identity_pb2_grpc.add_AuthIdentityServiceServicer_to_server(AuthIdentityGrpcService(), server)
  health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

  listen_addr = f"{settings.GRPC_HOST}:{settings.GRPC_PORT}"
  server.add_insecure_port(listen_addr)
  await server.start()

  await health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
  await health_servicer.set(_SERVICE_NAME, health_pb2.HealthCheckResponse.SERVING)
  return server, health_servicer


async def stop_grpc_server(
  server: grpc.aio.Server,
  health_servicer: health.HealthServicer,
) -> None:
  await health_servicer.set(_SERVICE_NAME, health_pb2.HealthCheckResponse.NOT_SERVING)
  await health_servicer.set("", health_pb2.HealthCheckResponse.NOT_SERVING)
  await server.stop(grace=5)
