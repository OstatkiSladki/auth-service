from __future__ import annotations

import grpc
import jwt

from src.core.security import decode_token
from src.db.repositories.staff import StaffProfileRepository
from src.db.repositories.user import UserRepository
from src.db.session import async_session_factory
from src.grpc.generated import auth_identity_pb2, auth_identity_pb2_grpc


class AuthIdentityGrpcService(auth_identity_pb2_grpc.AuthIdentityServiceServicer):
  async def ValidateToken(
    self,
    request: auth_identity_pb2.ValidateTokenRequest,
    context: grpc.aio.ServicerContext,
  ) -> auth_identity_pb2.ValidateTokenResponse:
    try:
      payload = decode_token(request.token)
    except jwt.InvalidTokenError as exc:
      await context.abort(grpc.StatusCode.UNAUTHENTICATED, f"Invalid token: {exc}")

    if payload.get("type") != "access":
      await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Unsupported token type")

    try:
      user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
      await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token subject is invalid")

    async with async_session_factory() as session:
      user = await UserRepository(session).get_by_id(user_id)
      if user is None:
        await context.abort(grpc.StatusCode.NOT_FOUND, "User not found")

      return auth_identity_pb2.ValidateTokenResponse(
        is_valid=True,
        user_id=int(user.id),
        role=str(user.role.value),
        is_active=bool(user.is_active),
        is_verified=bool(user.is_verified),
      )

  async def GetUserById(
    self,
    request: auth_identity_pb2.GetUserByIdRequest,
    context: grpc.aio.ServicerContext,
  ) -> auth_identity_pb2.GetUserByIdResponse:
    async with async_session_factory() as session:
      user = await UserRepository(session).get_by_id(int(request.user_id))
      if user is None:
        await context.abort(grpc.StatusCode.NOT_FOUND, "User not found")

      return auth_identity_pb2.GetUserByIdResponse(
        user_id=int(user.id),
        email=str(user.email),
        role=str(user.role.value),
        is_active=bool(user.is_active),
        is_verified=bool(user.is_verified),
      )

  async def CheckUserExists(
    self,
    request: auth_identity_pb2.CheckUserExistsRequest,
    context: grpc.aio.ServicerContext,
  ) -> auth_identity_pb2.CheckUserExistsResponse:
    async with async_session_factory() as session:
      user = await UserRepository(session).get_by_id(int(request.user_id))
      return auth_identity_pb2.CheckUserExistsResponse(exists=user is not None)

  async def RevokeStaffAccess(
    self,
    request: auth_identity_pb2.RevokeStaffAccessRequest,
    context: grpc.aio.ServicerContext,
  ) -> auth_identity_pb2.RevokeStaffAccessResponse:
    if not request.reason.strip():
      await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "reason is required")

    async with async_session_factory() as session:
      revoked_count = await StaffProfileRepository(session).delete_by_venue_id(int(request.venue_id))
      await session.commit()
      return auth_identity_pb2.RevokeStaffAccessResponse(revoked_count=revoked_count)
