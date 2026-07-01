import os

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("INGEST_API_KEY", "test-ingest-key")
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/vvt")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
