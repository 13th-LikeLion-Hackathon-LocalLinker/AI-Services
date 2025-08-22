#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
복지로 OpenAPI (목록+상세) → postings / posting_visa_codes 저장 스크립트
- Category: ADMINISTRATION / MEDICAL / HOUSING / EMPLOYMENT / EDUCATION / LIFE_SUPPORT
- Tag: SYSTEM / BENEFIT / PROGRAM (본문 키워드 기반 휴리스틱)
- VisaCodes: 본문 텍스트에서 D-2, F-6 등 추출하여 posting_visa_codes에 저장
"""
import os
import re
import math
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, List, Tuple

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

# 네가 만든 HTTP 클라이언트 사용 (SSL 폴백 포함)
from .http_client import WelfareAPIClient

load_dotenv()

BASE = "https://apis.data.go.kr/B554287/NationalWelfareInformationsV001"
LIST_EP = "NationalWelfarelistV001"
DETAIL_EP = "NationalWelfaredetailedV001"

# -------------------- ENV --------------------
SERVICE_KEY = os.getenv("PUBLIC_DATA_API_KEY")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# 수집 파라미터(필요 시 ENV로 조정)
PER_PAGE = 100  # ≤ 500 권장
MAX_PAGES = 1  # 0이면 전체
RPS = 3              # 30TPS 가이드 → 6rps 권장

# # 제목 차단 키워드 필터
# BLOCK_TITLE_RE = re.compile(r"(북한|탈북)")
#
# def should_skip_title(title: str | None) -> bool:
#     return bool(BLOCK_TITLE_RE.search(title or ""))

# -------------------- 파서 --------------------
def parse_list_xml(xml_text: str) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    root = ET.fromstring(xml_text)
    meta = {
        "resultCode": (root.findtext(".//resultCode") or "").strip(),
        "resultMessage": (root.findtext(".//resultMessage") or "").strip(),
        "totalCount": int(root.findtext(".//totalCount") or "0"),
        "pageNo": int(root.findtext(".//pageNo") or "1"),
        "numOfRows": int(root.findtext(".//numOfRows") or "10"),
    }

    def _t(n, tag):
        el = n.find(tag)
        return (el.text or "").strip() if el is not None and el.text else ""

    items = []
    for it in root.findall(".//servList"):
        items.append({
            "servId": _t(it, "servId"),
            "servNm": _t(it, "servNm"),
            "servDgst": _t(it, "servDgst"),
            "servDtlLink": _t(it, "servDtlLink"),
            "jurMnofNm": _t(it, "jurMnofNm"),
            "jurOrgNm": _t(it, "jurOrgNm"),
            "intrsThemaArray": _t(it, "intrsThemaArray"),  # 라벨/복수 가능
        })
    return meta, items

def parse_detail_xml(xml_text: str) -> Dict[str, Any]:
    root = ET.fromstring(xml_text)
    g = lambda p: (root.findtext(p) or "").strip()
    data = {
        "servId": g(".//servId"),
        "servNm": g(".//servNm"),
        "wlfareInfoOutlCn": g(".//wlfareInfoOutlCn"),  # 개요
        "tgtrDtlCn": g(".//tgtrDtlCn"),                # 지원대상
        "slctCritCn": g(".//slctCritCn"),              # 선정기준
        "alwServCn": g(".//alwServCn"),                # 지원내용
        "aplyMtdCn": g(".//aplyMtdCn"),                # 신청방법(있을 수 있음)
        "aplyPrdCn": g(".//aplyPrdCn"),                # 신청기간(텍스트)
    }
    return data

# -------------------- 매핑 --------------------
# Category 매핑 (네 Enum에 맞춤)
CATEGORY_MAP_CODE = {
    "100": "EDUCATION",
    "040": "HOUSING",
    "050": "EMPLOYMENT",
    "010": "MEDICAL", "020": "MEDICAL",
    "030": "LIFE_SUPPORT", "120": "LIFE_SUPPORT", "130": "LIFE_SUPPORT", "160": "LIFE_SUPPORT",
    "070": "ADMINISTRATION", "140": "ADMINISTRATION",
}
DEFAULT_CATEGORY = "LIFE_SUPPORT"

def pick_category(intrs: str) -> str:
    if not intrs:
        return DEFAULT_CATEGORY
    # 코드 매칭 우선
    for code, enum_name in CATEGORY_MAP_CODE.items():
        if code in intrs:
            return enum_name
    s = intrs.replace(" ", "")
    if any(k in s for k in ["법률","행정","안전","위기"]): return "ADMINISTRATION"
    if any(k in s for k in ["의료","신체건강","정신건강","건강"]): return "MEDICAL"
    if "주거" in s: return "HOUSING"
    if any(k in s for k in ["취업","근로","일자리","고용"]): return "EMPLOYMENT"
    if any(k in s for k in ["교육","훈련"]): return "EDUCATION"
    if any(k in s for k in ["생활지원","보호","돌봄","서민금융","에너지"]): return "LIFE_SUPPORT"
    return DEFAULT_CATEGORY

# Tag 추론 (본문 키워드 휴리스틱) → SYSTEM / BENEFIT / PROGRAM
def pick_tag(text: str) -> str:
    s = (text or "").replace(" ", "")
    system_kw = ["제도", "법령", "고시", "감면제도", "공제", "등록", "인증", "신고", "허가"]
    benefit_kw = ["지원금", "수당", "급여", "장려금", "보조금", "바우처", "환급", "감면", "장학금"]
    program_kw = ["교육", "훈련", "상담", "프로그램", "서비스", "멘토링", "코칭"]

    if any(k in s for k in system_kw):  return "SYSTEM"
    if any(k in s for k in benefit_kw): return "BENEFIT"
    if any(k in s for k in program_kw): return "PROGRAM"
    # 기본값
    return "PROGRAM"

# 날짜 파싱 (YY.MM.DD ~ YY.MM.DD 등)
DATE_PAIR = re.compile(r"(\d{2,4}[./-]\d{1,2}[./-]\d{1,2}).{0,5}(\d{2,4}[./-]\d{1,2}[./-]\d{1,2})")

def _norm_date(s: str) -> datetime | None:
    s = s.strip().replace("년",".").replace("월",".").replace("일","")
    for sep in (".","-","/"):
        p = s.split(sep)
        if len(p) == 3 and all(p):
            y,m,d = p
            if len(y) == 2: y = "20"+y
            try: return datetime(int(y), int(m), int(d))
            except ValueError: return None
    return None

def extract_period(*texts: str) -> Tuple[datetime|None, datetime|None]:
    blob = "  ".join([t for t in texts if t])
    m = DATE_PAIR.search(blob)
    if not m:
        return None, None
    sdt, edt = _norm_date(m.group(1)), _norm_date(m.group(2))
    return sdt, edt

# VisaCode 추출: D-2, F-6, E-7, C-4, H-2, G-1 등
VISA_ENUM_BY_CODE = {  # 문자열 → 네 Enum 이름
    "C-4":"C_4", "D-2":"D_2", "D-4":"D_4", "D-10":"D_10", "E-7":"E_7", "E-9":"E_9",
    "F-1":"F_1", "F-2":"F_2", "F-3":"F_3", "F-4":"F_4", "F-5":"F_5", "F-6":"F_6",
    "H-2":"H_2", "G-1":"G_1"
}
VISA_PAT = re.compile(r"\b([CDEFGH|F])[-\s]?(\d{1,2})\b", re.IGNORECASE)

def extract_visa_codes(*texts: str) -> List[str]:
    s = "  ".join([t for t in texts if t])
    found = set()
    for m in VISA_PAT.finditer(s):
        code = f"{m.group(1).upper()}-{int(m.group(2))}"
        enum_name = VISA_ENUM_BY_CODE.get(code)
        if enum_name:
            found.add(enum_name)
    return sorted(found)

def compose_content(detail: Dict[str,str]) -> str:
    parts = []
    if detail.get("wlfareInfoOutlCn"): parts.append("■ 개요\n"+detail["wlfareInfoOutlCn"])
    if detail.get("tgtrDtlCn"):        parts.append("■ 지원대상\n"+detail["tgtrDtlCn"])
    if detail.get("slctCritCn"):       parts.append("■ 선정기준\n"+detail["slctCritCn"])
    if detail.get("alwServCn"):        parts.append("■ 지원내용\n"+detail["alwServCn"])
    if detail.get("aplyMtdCn"):        parts.append("■ 신청방법\n"+detail["aplyMtdCn"])
    if detail.get("aplyPrdCn"):        parts.append("■ 신청기간(원문)\n"+detail["aplyPrdCn"])
    return "\n\n".join(parts).strip()

# -------------------- DB --------------------
DDL_UNIQUE = """
CREATE UNIQUE INDEX IF NOT EXISTS ux_postings_source_url ON postings(source_url) WHERE source_url IS NOT NULL;
"""
SQL_UPSERT = """
INSERT INTO postings
(title, content, category, tags, eligibility, source_url, apply_start_at, apply_end_at)
VALUES %s
ON CONFLICT (source_url) DO UPDATE
SET title = EXCLUDED.title,
    content = EXCLUDED.content,
    category = EXCLUDED.category,
    tags = EXCLUDED.tags,
    eligibility = EXCLUDED.eligibility,
    apply_start_at = EXCLUDED.apply_start_at,
    apply_end_at = EXCLUDED.apply_end_at
RETURNING posting_id;
"""
# posting_id는 RETURNING 받을 수 있도록 JPA에서 @Id SERIAL(IDENTITY)라고 가정
# (이미 존재해도 해당 row의 id를 얻기 위해서는 별도 SELECT 필요. 여기선 2단계 처리)

def upsert_postings_and_get_ids(conn, rows: List[Dict[str,Any]]) -> List[int]:
    if not rows: return []
    with conn.cursor() as cur:
        cur.execute(DDL_UNIQUE)
        # execute_values 로 values 묶음 삽입
        values = [
            (r["title"], r["content"], r["category"], r["tags"],
             r["eligibility"], r["source_url"], r["apply_start_at"], r["apply_end_at"])
            for r in rows
        ]
        # RETURNING posting_id는 ON CONFLICT UPDATE에서도 한 번에 리스트를 못 받으므로,
        # 먼저 upsert 수행 후, source_url로 id를 조회하는 2단계 전략을 사용.
        execute_values(cur, """
            INSERT INTO postings
            (title, content, category, tags, eligibility, source_url, apply_start_at, apply_end_at)
            VALUES %s
            ON CONFLICT (source_url) DO UPDATE
            SET title=EXCLUDED.title, content=EXCLUDED.content, category=EXCLUDED.category,
                tags=EXCLUDED.tags, eligibility=EXCLUDED.eligibility,
                apply_start_at=EXCLUDED.apply_start_at, apply_end_at=EXCLUDED.apply_end_at;
        """, values, page_size=200)

        # id 재조회
        ids = []
        for r in rows:
            cur.execute("SELECT posting_id FROM postings WHERE source_url = %s", (r["source_url"],))
            row = cur.fetchone()
            if row:
                ids.append(int(row[0]))
        return ids

def replace_visa_codes(conn, posting_id: int, visa_codes: List[str]):
    with conn.cursor() as cur:
        # 기존 코드 제거 후 재삽입 (간단)
        cur.execute("DELETE FROM posting_visa_codes WHERE posting_id = %s", (posting_id,))
        if visa_codes:
            execute_values(cur, """
                INSERT INTO posting_visa_codes (posting_id, visa_code)
                VALUES %s
            """, [(posting_id, code) for code in visa_codes])

# -------------------- 수집/저장 파이프라인 --------------------
def fetch_list_page(client: WelfareAPIClient, page_no=1, num_of_rows=100, **filters):
    xml = client.fetch_welfare_list(page_no=page_no, num_of_rows=num_of_rows, **filters)
    meta, items = parse_list_xml(xml)
    rc = (meta.get("resultCode") or "")
    if rc and not rc.startswith(("0","00")):
        raise RuntimeError(f"OpenAPI error (list): code={rc}, msg={meta.get('resultMessage')}")
    return meta, items

def fetch_detail(client: WelfareAPIClient, serv_id: str) -> Dict[str,Any]:
    xml = client.get(DETAIL_EP, {"callTp":"D", "servId": serv_id})
    data = parse_detail_xml(xml)
    return data

def to_postings_record(list_item: Dict[str,str], detail: Dict[str,Any]) -> Dict[str,Any]:
    title = detail.get("servNm") or list_item.get("servNm") or ""
    content = compose_content(detail)
    eligibility = (detail.get("tgtrDtlCn") or "").strip() or "상세 페이지 참조"
    category = pick_category(list_item.get("intrsThemaArray",""))
    source_url = list_item.get("servDtlLink") or None

    # Tag 추론은 본문 전체 기준
    tag = pick_tag(" ".join([
        detail.get("wlfareInfoOutlCn",""),
        detail.get("alwServCn",""),
        detail.get("aplyMtdCn",""),
        detail.get("tgtrDtlCn",""),
    ]))

    # 기간 파싱
    sdt, edt = extract_period(detail.get("aplyPrdCn",""), detail.get("alwServCn",""))

    # 비자 코드 추출 (eligibility/본문에서)
    visas = extract_visa_codes(
        detail.get("tgtrDtlCn",""),
        detail.get("slctCritCn",""),
        detail.get("wlfareInfoOutlCn",""),
        detail.get("alwServCn",""),
    )

    return {
        "title": title,
        "content": content,
        "category": category,   # enum 문자열 그대로 저장
        "tags": tag,            # enum 문자열 그대로 저장
        "eligibility": eligibility,
        "source_url": source_url,
        "apply_start_at": sdt,
        "apply_end_at": edt,
        "visa_codes": visas,
    }

def ingest(filters: Dict[str,Any]):
    with WelfareAPIClient(BASE, SERVICE_KEY) as client:
        # 1) 목록 첫 페이지
        meta, items = fetch_list_page(client, 1, PER_PAGE, **filters)
        total, per = meta["totalCount"], meta["numOfRows"]
        pages = max(1, math.ceil(total/per)) if total else 1
        if MAX_PAGES and MAX_PAGES > 0:
            pages = min(pages, MAX_PAGES)

        # 나머지 페이지
        all_items = list(items)
        for p in range(2, pages+1):
            time.sleep(1.0/max(RPS,1))
            _, page_items = fetch_list_page(client, p, PER_PAGE, **filters)
            all_items.extend(page_items)

        # 2) 상세 + 매핑
        records = []
        for idx, it in enumerate(all_items, 1):
            if not it.get("servId"):
                continue
            time.sleep(1.0/max(RPS,1))
            d = fetch_detail(client, it["servId"])
            rec = to_postings_record(it, d)
            # content/title/eligibility는 NOT NULL 보장
            if not rec["title"] or not rec["content"] or not rec["eligibility"]:
                continue
            records.append(rec)
            if idx % 20 == 0:
                print(f"[INFO] parsed {idx}/{len(all_items)}")

    # 3) DB 저장 (업서트 + 자식 테이블 교체)
    with psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    ) as conn:
        # 선택: 스키마 보정이 있다면 먼저
        # ensure_schema(conn)

        ids = upsert_postings_and_get_ids(conn, records)
        for rec, pid in zip(records, ids):
            replace_visa_codes(conn, pid, rec.get("visa_codes") or [])

        # with 블록 끝나면 자동 commit
        print(f"[INFO] upserted postings: {len(ids)} rows")

# -------------------- 실행 예시 --------------------
if __name__ == "__main__":
    # 예: 외국인 + 행정 성격(법률/안전) 필터
    # - trgterIndvdlArray=010(다문화·탈북민)
    # - intrsThemaArray=070(안전·위기) 또는 140(법률) → 한 번에 하나만 받는다면, 두 번 돌리거나, 여기선 070로 실행
    filters = {
        "trgterIndvdlArray": "010",
        #"intrsThemaArray": "070",  # 필요 시 140 로 변경, 또는 배치 2회
        "orderBy": "date",  # or "popular"
        # "srchKeyCode": "003",
        # "searchWrd": "외국인",
    }
    ingest(filters)
