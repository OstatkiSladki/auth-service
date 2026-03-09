from enum import Enum


class UsersRole(str, Enum):
  USER = "user"
  STAFF = "staff"
  ADMIN = "admin"


class StaffRole(str, Enum):
  STAFF = "staff"  # Базовый исполнитель
  MANAGER = "manager"  # Операционное управление
  ADMIN = "admin"  # Полные права на площадку
  OWNER = "owner"  # Владелец площадки (высшая роль)
