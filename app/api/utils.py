import math
from datetime import datetime, timezone
from typing import Optional

def parse_iso(ts: Optional[str]) -> Optional[datetime]:
    """ISO 형식의 타임스탬프를 datetime 객체로 파싱"""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None

def recency_boost(updated_at: Optional[str]) -> float:
    """최신성 점수 계산 (30일 기준 지수 감소)"""
    dt = parse_iso(updated_at)
    if not dt:
        return 0.0
    days = (datetime.now(timezone.utc) - dt).days
    return math.exp(-days / 30.0)
