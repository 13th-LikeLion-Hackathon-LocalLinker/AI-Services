import functools
from typing import List, Dict, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from sentence_transformers import SentenceTransformer

from app.api.config import QDRANT_URL, MODEL_NAME, MT_ENABLED, ALPHA, BETA, GAMMA, COLL_BENEFITS
from app.api.utils import recency_boost
from app.api.dtos.response import BenefitHit

# 클라이언트 초기화
qdrant = QdrantClient(url=QDRANT_URL)
embedder = SentenceTransformer(MODEL_NAME)

def embed_one(text: str) -> List[float]:
    """텍스트를 벡터로 임베딩"""
    return embedder.encode([text], normalize_embeddings=True)[0].tolist()

def mt_translate(text: str, target: str) -> str:
    """자동번역 (실제 MT API 연동이 필요한 부분)"""
    # 실제 MT 연동 위치. 기본은 미사용(원문 반환).
    return text

@functools.lru_cache(maxsize=10_000)
def translate_cached(text: str, lang: str) -> str:
    """캐시된 번역 함수"""
    if not text or not MT_ENABLED:  # MT 비활성화면 원문 그대로
        return text
    return mt_translate(text, lang)

def pick_text(payload: Dict, lang: str) -> Tuple[str, str]:
    """
    payload에서 요청 언어의 name/desc를 꺼내고, 없으면 ko → (옵션) MT 폴백
    """
    i18n = payload.get("i18n") or {}
    # 1) 요청 언어
    if isinstance(i18n, dict) and lang in i18n:
        name = i18n[lang].get("name") or payload.get("name_ko") or ""
        desc = i18n[lang].get("desc") or payload.get("desc_ko") or ""
        return name, desc
    # 2) ko 원문
    name_ko = payload.get("name_ko") or ""
    desc_ko = payload.get("desc_ko") or ""
    # 3) MT 폴백(옵션)
    if lang != "ko" and MT_ENABLED:
        return translate_cached(name_ko, lang), translate_cached(desc_ko, lang)
    # 4) 최종 ko
    return name_ko, desc_ko


def search_benefits(query: str,
                    lang: str,
                    visa: str = None,
                    jurisdiction: str = None,
                    category: str = None,
                    k: int = 30) -> List[Tuple[float, BenefitHit]]:
    """혜택 프로그램 검색"""
    # 1) 질의 임베딩
    vec = embed_one(query)

    # 2) 필터 조합
    must_filters = []
    if jurisdiction:
        must_filters.append(qm.FieldCondition(key="jurisdiction", match=qm.MatchValue(value=jurisdiction)))
    if category:
        must_filters.append(qm.FieldCondition(key="category", match=qm.MatchValue(value=category)))
    if visa:
        # visa_in 배열에 req.visa 포함 (Qdrant 1.8+ MatchAny 사용)
        must_filters.append(qm.FieldCondition(key="visa_in", match=qm.MatchAny(any=[visa])))

    qfilter = qm.Filter(must=must_filters) if must_filters else None

    # 3) Qdrant 의미 검색
    hits = qdrant.search(
        collection_name=COLL_BENEFITS,
        query_vector=vec,
        query_filter=qfilter,
        limit=k,
        with_payload=True
    )

    # 4) 재랭킹 (vector + featured + recency)
    scored: List[Tuple[float, BenefitHit]] = []
    for h in hits:
        pl = h.payload or {}
        featured = bool(pl.get("featured", False))
        updated_at = pl.get("updated_at")
        rec_boost = recency_boost(updated_at)
        vector_score = float(h.score or 0.0)
        final = ALPHA * vector_score + BETA * (1.0 if featured else 0.0) + GAMMA * rec_boost

        name, desc = pick_text(pl, lang)

        scored.append((
            final,
            BenefitHit(
                program_id=str(pl.get("program_id") or pl.get("id") or h.id),
                authority=pl.get("authority"),
                jurisdiction=pl.get("jurisdiction"),
                category=pl.get("category"),
                name=name,
                desc=desc[:600] if desc else None,  # 너무 길면 슬라이스
                apply_url=pl.get("apply_url"),
                source_url=pl.get("source_url"),
                featured=featured,
                updated_at=updated_at,
                score=final
            )
        ))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored
