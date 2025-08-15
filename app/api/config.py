import os
from dotenv import load_dotenv

# .env 파일 로드 (있으면)
load_dotenv()

# ---------- Qdrant Config ----------
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLL_BENEFITS = os.getenv("QDRANT_BENEFITS", "benefits_programs")

# ---------- Model Config ----------
MODEL_NAME = os.getenv("MODEL_NAME", "intfloat/multilingual-e5-small")

# ---------- CORS Config ----------
ALLOWED = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# ---------- Scoring Config ----------
ALPHA = float(os.getenv("BENEFITS_ALPHA", "0.7"))  # vector
BETA  = float(os.getenv("BENEFITS_BETA", "0.2"))   # featured
GAMMA = float(os.getenv("BENEFITS_GAMMA", "0.1"))  # recency

# ---------- Translation Config ----------
MT_ENABLED = os.getenv("MT_ENABLED", "false").lower() == "true"

# ---------- Supported Languages ----------
LANGS = {"ko", "zh", "th", "en", "vi", "ja", "uz"}
