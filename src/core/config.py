from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  PROJECT_NAME: str = "Auth Service"
  VERSION: str = "1.2.0"
  ENVIRONMENT: str = "development"
  PORT: int = 8000
  HOST: str = "0.0.0.0"
  GRPC_HOST: str = "0.0.0.0"
  GRPC_PORT: int = 50053
  GRPC_VENUE_SERVICE_HOST: str = "venue-service"
  GRPC_VENUE_SERVICE_PORT: int = 50052
  GRPC_STARTUP_CHECK_TIMEOUT: float = 30.0
  GRPC_CALL_TIMEOUT: float = 5.0
  GRPC_CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
  GRPC_CIRCUIT_BREAKER_RESET_TIMEOUT: float = 30.0
  GRPC_STARTUP_CHECKS_ENABLED: bool = True
  APP_ROOT_PATH: str = ""

  # Database
  POSTGRES_HOST: str
  POSTGRES_PORT: int
  POSTGRES_USER: str
  POSTGRES_PASSWORD: str
  POSTGRES_DB: str

  @computed_field
  @property
  def DATABASE_URL(self) -> str:
    return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

  # JWT
  JWT_SECRET_KEY: str
  JWT_ALGORITHM: str = "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
  REFRESH_TOKEN_EXPIRE_DAYS: int = 30

  # CORS
  CORS_ORIGINS: list[str] | str = []

  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=True,
    extra="ignore",
  )

  # @field_validator("CORS_ORIGINS")
  # def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
  #     if isinstance(v, str) and not v.startswith("["):
  #         return [i.strip() for i in v.split(",")]
  #     elif isinstance(v, (list, str)):
  #         return v
  #     raise ValueError(v)


settings = Settings()
