import os
from pydantic_settings import BaseSettings

# config.py lives at <repo>/backend/app/core/config.py
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_REPO_ROOT = os.path.dirname(_BACKEND_ROOT)


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://hormoneos:hormoneos@localhost:5432/hormoneos"
    HSF_MODEL_VERSION: str = "hsf-v1"
    EMBEDDING_DIM: int = 128
    UPLOAD_DIR: str = "/tmp/hormoneos_uploads"
    OPENAI_API_KEY: str = ""

    # Comma-separated allowed CORS origins. "*" allows all (dev only).
    CORS_ORIGINS: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # Location of the standalone HSF PyTorch module (ml/src) and the trained
    # checkpoint produced by ml/src/train.py. Both are resolved relative to the
    # repository root so the backend works regardless of the current directory.
    ML_SRC_DIR: str = os.path.join(_REPO_ROOT, "ml", "src")
    HSF_WEIGHTS_PATH: str = os.path.join(_REPO_ROOT, "ml", "src", "weights", "hsf_128d.pt")

    class Config:
        # Resolve .env file absolutely relative to the backend root directory
        env_file = os.path.join(_BACKEND_ROOT, ".env")


settings = Settings()
