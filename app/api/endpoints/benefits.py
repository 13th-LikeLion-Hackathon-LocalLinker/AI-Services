from fastapi import APIRouter
from app.api.dtos import BenefitsSearchReq, BenefitsSearchRes
from app.api.services import search_benefits
from app.api.config import QDRANT_URL, COLL_BENEFITS, MT_ENABLED

router = APIRouter()

@router.post("/semantic/benefits/search", response_model=BenefitsSearchRes)
def semantic_benefits_search(req: BenefitsSearchReq):
    """혜택 프로그램 시맨틱 검색"""
    scored = search_benefits(
        query=req.query,
        lang=req.lang,
        visa=req.visa,
        jurisdiction=req.jurisdiction,
        category=req.category,
        k=req.k
    )

    # 페이지네이션
    start = req.page * req.size
    end = start + req.size
    items = [item for _, item in scored[start:end]]

    return BenefitsSearchRes(
        total=len(scored),
        page=req.page,
        size=req.size,
        items=items
    )

@router.get("/health")
def benefits_health():
    """혜택 서비스 헬스체크 엔드포인트"""
    return {
        "ok": True,
        "qdrant": QDRANT_URL,
        "collection": COLL_BENEFITS,
        "mt_enabled": MT_ENABLED
    }
