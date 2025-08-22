"""
HTTP 요청을 처리하는 클라이언트 모듈
"""

import requests
from typing import Dict, Any, Optional
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CustomHTTPSAdapter(HTTPAdapter):
    """커스텀 HTTPS 어댑터 - SSL 문제 해결"""
    
    def init_poolmanager(self, *args, **kwargs):
        try:
            ctx = create_urllib3_context()
            ctx.check_hostname = False  # 호스트명 체크 먼저 비활성화
            ctx.verify_mode = ssl.CERT_NONE  # 그 다음 인증서 검증 비활성화
            ctx.set_ciphers('DEFAULT@SECLEVEL=1')  # 낮은 보안 레벨로 설정
            kwargs['ssl_context'] = ctx
        except Exception as e:
            print(f"SSL 컨텍스트 설정 실패: {e}")
            # 기본 설정으로 폴백
            pass
        return super().init_poolmanager(*args, **kwargs)


class WelfareAPIClient:
    """복지 정보 API를 위한 HTTP 클라이언트"""
    
    def __init__(self, base_url: str, service_key: str):
        """
        Args:
            base_url: API 기본 URL
            service_key: 서비스 키
        """
        self.base_url = base_url
        self.service_key = service_key
        self.session = requests.Session()
        
        # SSL 관련 설정
        self.session.verify = False  # SSL 검증 비활성화
        
        # User-Agent 설정 (일부 API에서 요구)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 커스텀 HTTPS 어댑터 마운트 (에러 발생 시 스킵)
        try:
            self.session.mount('https://', CustomHTTPSAdapter())
        except Exception as e:
            print(f"커스텀 HTTPS 어댑터 설정 실패, 기본 설정 사용: {e}")
        
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30) -> str:
        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        
        # 기본 파라미터에 서비스 키 추가
        request_params = {"serviceKey": self.service_key}
        if params:
            request_params.update(params)
        
        # 디버깅용 요청 URL 출력
        print(f"요청 URL: {url}")
        print(f"요청 파라미터: {request_params}")
        
        # HTTPS 시도
        try:
            response = self.session.get(url, params=request_params, timeout=timeout)
            response.raise_for_status()
            
            # 인코딩 설정
            response.encoding = response.apparent_encoding or "utf-8"
            """
            HTTP 요청을 처리하는 클라이언트 모듈
            """

            import requests
            from typing import Dict, Any, Optional
            import urllib3
            import ssl
            from requests.adapters import HTTPAdapter
            from urllib3.util.ssl_ import create_urllib3_context

            # SSL 경고 비활성화
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            class CustomHTTPSAdapter(HTTPAdapter):
                """커스텀 HTTPS 어댑터 - SSL 문제 해결"""

                def init_poolmanager(self, *args, **kwargs):
                    try:
                        ctx = create_urllib3_context()
                        ctx.check_hostname = False  # 호스트명 체크 먼저 비활성화
                        ctx.verify_mode = ssl.CERT_NONE  # 그 다음 인증서 검증 비활성화
                        ctx.set_ciphers('DEFAULT@SECLEVEL=1')  # 낮은 보안 레벨로 설정
                        kwargs['ssl_context'] = ctx
                    except Exception as e:
                        print(f"SSL 컨텍스트 설정 실패: {e}")
                        # 기본 설정으로 폴백
                        pass
                    return super().init_poolmanager(*args, **kwargs)

            class WelfareAPIClient:
                """복지 정보 API를 위한 HTTP 클라이언트"""

                def __init__(self, base_url: str, service_key: str):
                    """
                    Args:
                        base_url: API 기본 URL
                        service_key: 서비스 키
                    """
                    self.base_url = base_url
                    self.service_key = service_key
                    self.session = requests.Session()

                    # SSL 관련 설정
                    self.session.verify = False  # SSL 검증 비활성화

                    # User-Agent 설정 (일부 API에서 요구)
                    self.session.headers.update({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })

                    # 커스텀 HTTPS 어댑터 마운트 (에러 발생 시 스킵)
                    try:
                        self.session.mount('https://', CustomHTTPSAdapter())
                    except Exception as e:
                        print(f"커스텀 HTTPS 어댑터 설정 실패, 기본 설정 사용: {e}")

                def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30) -> str:
                    url = f"{self.base_url}/{endpoint}" if not endpoint.startswith('http') else endpoint

                    # 기본 파라미터에 서비스 키 추가
                    request_params = {"serviceKey": self.service_key}
                    if params:
                        request_params.update(params)

                    # 디버깅용 요청 URL 출력
                    print(f"요청 URL: {url}")
                    print(f"요청 파라미터: {request_params}")

                    # HTTPS 시도
                    try:
                        response = self.session.get(url, params=request_params, timeout=timeout)
                        response.raise_for_status()

                        # 인코딩 설정
                        response.encoding = response.apparent_encoding or "utf-8"

                        return response.text

                    except requests.exceptions.SSLError as ssl_error:
                        print(f"HTTPS 연결 실패, HTTP로 재시도... (오류: {ssl_error})")

                        # HTTP로 폴백
                        http_url = url.replace('https://', 'http://')
                        response = self.session.get(http_url, params=request_params, timeout=timeout)
                        response.raise_for_status()

                        # 인코딩 설정
                        response.encoding = response.apparent_encoding or "utf-8"

                        return response.text

                def fetch_welfare_list(self, page_no: int = 1, num_of_rows: int = 10, **filters) -> str:
                    """
                    복지 정보 목록을 조회

                    Args:
                        page_no: 페이지 번호
                        num_of_rows: 한 페이지당 항목 수
                        **filters: 추가 필터 옵션

                    Returns:
                        str: XML 응답 텍스트
                    """
                    params = {
                        "callTp": "L",
                        "pageNo": page_no,
                        "numOfRows": num_of_rows,
                        "srchKeyCode": "1"
                    }
                    params.update(filters)

                    return self.get("NationalWelfarelistV001", params)

                def close(self):
                    """세션 종료"""
                    self.session.close()

                def __enter__(self):
                    """컨텍스트 매니저 지원"""
                    return self

                def __exit__(self, exc_type, exc_val, exc_tb):
                    """컨텍스트 매니저 지원"""
                    self.close()

            class SimpleHTTPClient:
                """간단한 HTTP 클라이언트"""

                @staticmethod
                def get(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30) -> str:
                    """
                    간단한 GET 요청

                    Args:
                        url: 요청 URL
                        params: 요청 파라미터
                        timeout: 타임아웃 (초)

                    Returns:
                        str: 응답 텍스트
                    """
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(
                        url,
                        params=params,
                        timeout=timeout,
                        verify=False,  # SSL 검증 비활성화
                        headers=headers
                    )
                    response.raise_for_status()
                    response.encoding = response.apparent_encoding or "utf-8"
                    return response.text

            return response.text
            
        except requests.exceptions.SSLError as ssl_error:
            print(f"HTTPS 연결 실패, HTTP로 재시도... (오류: {ssl_error})")
            
            # HTTP로 폴백
            http_url = url.replace('https://', 'http://')
            response = self.session.get(http_url, params=request_params, timeout=timeout)
            response.raise_for_status()
            
            # 인코딩 설정
            response.encoding = response.apparent_encoding or "utf-8"
            
            return response.text
    
    def fetch_welfare_list(self, page_no: int = 1, num_of_rows: int = 10, **filters) -> str:
        """
        복지 정보 목록을 조회
        
        Args:
            page_no: 페이지 번호
            num_of_rows: 한 페이지당 항목 수
            **filters: 추가 필터 옵션
            
        Returns:
            str: XML 응답 텍스트
        """
        params = {
            "callTp": "L",
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "srchKeyCode": "1"
        }
        params.update(filters)
        
        return self.get("NationalWelfarelistV001", params)
    
    def close(self):
        """세션 종료"""
        self.session.close()
    
    def __enter__(self):
        """컨텍스트 매니저 지원"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 지원"""
        self.close()


class SimpleHTTPClient:
    """간단한 HTTP 클라이언트"""
    
    @staticmethod
    def get(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30) -> str:
        """
        간단한 GET 요청
        
        Args:
            url: 요청 URL
            params: 요청 파라미터
            timeout: 타임아웃 (초)
            
        Returns:
            str: 응답 텍스트
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(
            url, 
            params=params, 
            timeout=timeout, 
            verify=False,  # SSL 검증 비활성화
            headers=headers
        )
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        return response.text
