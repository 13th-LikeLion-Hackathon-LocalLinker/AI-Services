
import os
import sys
import json
import xml.etree.ElementTree as ET
from .http_client import WelfareAPIClient

BASE = "https://apis.data.go.kr/B554287/NationalWelfareInformationsV001"

def parse_list_xml(xml_text: str):
    """목록 XML → (meta, items)"""
    root = ET.fromstring(xml_text)
    meta = {
        "resultCode": (root.findtext(".//resultCode") or "").strip(),
        "resultMessage": (root.findtext(".//resultMessage") or "").strip(),
        "totalCount": int(root.findtext(".//totalCount") or "0"),
        "pageNo": int(root.findtext(".//pageNo") or "1"),
        "numOfRows": int(root.findtext(".//numOfRows") or "10"),
    }

    def _t(node, tag):
        el = node.find(tag)
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
            "intrsThemaArray": _t(it, "intrsThemaArray"),
            "lifeArray": _t(it, "lifeArray"),
            "trgterIndvdlArray": _t(it, "trgterIndvdlArray"),
            "onapPsbltYn": _t(it, "onapPsbltYn"),
        })
    return meta, items

def fetch_list_page(service_key: str, page_no=1, num_of_rows=20, **filters):
    """목록 1페이지 호출"""
    with WelfareAPIClient(BASE, service_key) as client:
        xml_text = client.fetch_welfare_list(page_no, num_of_rows, **filters)
        return parse_list_xml(xml_text)

if __name__ == "__main__":
    # API 키 설정 (환경변수 또는 하드코딩)
    SERVICE_KEY = os.getenv("PUBLIC_DATA_API_KEY")
    
    print(f"사용할 API 키: {SERVICE_KEY}...")  # 키의 일부만 출력
    
    # 추가 필터 옵션들 (주석 해제해서 사용)
    filters = {
        "trgterIndvdlArray": "010",
        "intrsThemaArray": "100",  # 관심주제: 100=교육, 040=주거, 050=일자리, 030=생활지원, 010/020=의료
        #"srchKeyCode": "003",      # 001 제목 / 002 내용 / 003 제목+내용
        #"searchWrd": "외국인",
        "orderBy": "date"      # or "popular"
    }

    try:
        print(f"API 호출 중... (Base URL: {BASE})")
        print(f"필터: {filters}")
        
        meta, items = fetch_list_page(SERVICE_KEY, page_no=1, num_of_rows=20, **filters)

        # 메타/아이템 출력
        print("# META")
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        print(f"\n# ITEMS (page 1) - 총 {len(items)}개")
        print(json.dumps(items, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"오류 발생: {type(e).__name__}: {e}", file=sys.stderr)
        print("API 호출에 실패했습니다.", file=sys.stderr)
        
        # SSL 에러인 경우 추가 정보 제공
        if "SSL" in str(e):
            print("SSL 관련 오류입니다. 네트워크 설정이나 방화벽을 확인해주세요.", file=sys.stderr)
        
        import traceback
        traceback.print_exc()
        sys.exit(1)