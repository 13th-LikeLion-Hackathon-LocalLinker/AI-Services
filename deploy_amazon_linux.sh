#!/bin/bash

# LocalLinker AI Amazon Linux EC2 배포 스크립트

set -e

echo "🚀 LocalLinker AI Amazon Linux 배포 시작..."

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

# Amazon Linux 버전 확인
check_amazon_linux_version() {
    if [ -f /etc/os-release ]; then
        source /etc/os-release
        if [[ "$ID" == "amzn" ]]; then
            if [[ "$VERSION_ID" == "2023"* ]]; then
                AMAZON_LINUX_VERSION="2023"
                PACKAGE_MANAGER="dnf"
            elif [[ "$VERSION_ID" == "2"* ]]; then
                AMAZON_LINUX_VERSION="2"
                PACKAGE_MANAGER="yum"
            else
                AMAZON_LINUX_VERSION="1"
                PACKAGE_MANAGER="yum"
            fi
        else
            log_error "이 스크립트는 Amazon Linux에서만 실행됩니다."
            exit 1
        fi
    else
        log_error "운영체제를 확인할 수 없습니다."
        exit 1
    fi
    
    log_info "Amazon Linux $AMAZON_LINUX_VERSION 감지됨 (패키지 매니저: $PACKAGE_MANAGER)"
}

# 환경변수 파일 확인
if [ ! -f ".env" ]; then
    log_error ".env 파일이 존재하지 않습니다."
    log_info "env.example을 참조하여 .env 파일을 생성해주세요."
    exit 1
fi

# Amazon Linux 버전 확인
check_amazon_linux_version

# Docker 설치 확인 및 설치
if ! command -v docker &> /dev/null; then
    log_warn "Docker가 설치되지 않았습니다. 자동으로 설치합니다..."
    
    # 시스템 업데이트
    log_info "시스템 업데이트 중..."
    sudo $PACKAGE_MANAGER update -y
    
    # Docker 설치
    log_info "Docker 설치 중..."
    sudo $PACKAGE_MANAGER install -y docker
    
    # Docker 서비스 시작
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # 현재 사용자를 docker 그룹에 추가
    sudo usermod -aG docker $USER
    
    log_info "Docker 설치 완료. 새로운 셸 세션에서 실행하거나 'newgrp docker' 명령을 실행해주세요."
fi

# Docker Compose 설치 확인 및 설치
if ! command -v docker-compose &> /dev/null; then
    log_warn "Docker Compose가 설치되지 않았습니다. 자동으로 설치합니다..."
    
    # Docker Compose 설치
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_info "Docker Compose 설치 완료."
fi

# Docker 서비스 상태 확인
if ! sudo systemctl is-active --quiet docker; then
    log_info "Docker 서비스 시작 중..."
    sudo systemctl start docker
fi

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
log_info "🎉 Amazon Linux EC2 배포가 완료되었습니다!"
echo ""
echo "서비스 접속 정보:"
echo "- API 서버: http://$(curl -s ifconfig.me):8100"
echo "- API 문서: http://$(curl -s ifconfig.me):8100/docs"
echo "- 헬스체크: http://$(curl -s ifconfig.me):8100/api/health"
echo ""
echo "Amazon Linux 관련 유용한 명령어:"
echo "- 시스템 업데이트: sudo $PACKAGE_MANAGER update -y"
echo "- 로그 확인: docker-compose logs -f"
echo "- 서비스 재시작: docker-compose restart"
echo "- 서비스 중지: docker-compose down"
echo "- 방화벽 상태: sudo firewall-cmd --list-all"
echo ""
