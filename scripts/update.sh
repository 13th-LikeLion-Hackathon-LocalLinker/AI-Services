#!/bin/bash

# 애플리케이션 업데이트 스크립트 (Amazon Linux 호환)

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 백업 생성
log_info "업데이트 전 백업 생성 중..."
./scripts/backup.sh

# Git에서 최신 코드 가져오기
log_info "최신 코드 가져오는 중..."
git fetch origin
git pull origin main

# Docker 이미지 재빌드
log_info "Docker 이미지 재빌드 중..."
docker-compose build --no-cache

# 서비스 재시작
log_info "서비스 재시작 중..."
docker-compose down
docker-compose up -d

# 헬스체크
log_info "서비스 상태 확인 중..."
sleep 15

for i in {1..30}; do
    if curl -f http://localhost:8100/api/health &> /dev/null; then
        log_info "✅ 업데이트가 성공적으로 완료되었습니다!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        log_error "❌ 업데이트 후 서비스 시작에 실패했습니다."
        log_warn "백업에서 복원을 고려해주세요."
        docker-compose logs
        exit 1
    fi
    
    echo "대기 중... ($i/30)"
    sleep 2
done

# 불필요한 Docker 이미지 정리
log_info "불필요한 Docker 이미지 정리 중..."
docker image prune -f

log_info "🎉 업데이트 완료!"
