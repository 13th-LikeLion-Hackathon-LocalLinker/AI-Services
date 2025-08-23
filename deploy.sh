#!/bin/bash

# LocalLinker AI EC2 배포 스크립트 (Ubuntu/Debian용)
# Amazon Linux 사용자는 deploy_amazon_linux.sh 사용

set -e

echo "🚀 LocalLinker AI 배포 시작..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수 정의
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 환경변수 파일 확인
if [ ! -f ".env" ]; then
    log_error ".env 파일이 존재하지 않습니다."
    log_info "env.example을 참조하여 .env 파일을 생성해주세요."
    exit 1
fi

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    log_error "Docker가 설치되지 않았습니다."
    log_info "Docker 설치: https://docs.docker.com/engine/install/"
    exit 1
fi

# Docker Compose 설치 확인
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose가 설치되지 않았습니다."
    log_info "Docker Compose 설치: https://docs.docker.com/compose/install/"
    exit 1
fi

# SSL 설정이 필요하지 않으므로 제거

# 이전 컨테이너 정리
log_info "이전 컨테이너 정리 중..."
docker-compose down --remove-orphans || true

# 이미지 빌드 및 컨테이너 시작
log_info "Docker 이미지 빌드 중..."
docker-compose build --no-cache

log_info "컨테이너 시작 중..."
docker-compose up -d

# 헬스체크
log_info "서비스 상태 확인 중..."
sleep 10

for i in {1..30}; do
    if curl -f http://localhost:8100/api/health &> /dev/null; then
        log_info "✅ 서비스가 성공적으로 시작되었습니다!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        log_error "❌ 서비스 시작에 실패했습니다."
        docker-compose logs
        exit 1
    fi
    
    echo "대기 중... ($i/30)"
    sleep 2
done

# 배포 완료 메시지
echo ""
log_info "🎉 배포가 완료되었습니다!"
echo ""
echo "서비스 접속 정보:"
echo "- API 서버: http://$(curl -s ifconfig.me):8100"
echo "- API 문서: http://$(curl -s ifconfig.me):8100/docs"
echo "- 헬스체크: http://$(curl -s ifconfig.me):8100/api/health"
echo ""
echo "유용한 명령어:"
echo "- 로그 확인: docker-compose logs -f"
echo "- 서비스 재시작: docker-compose restart"
echo "- 서비스 중지: docker-compose down"
echo ""
