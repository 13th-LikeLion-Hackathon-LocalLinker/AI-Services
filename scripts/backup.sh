#!/bin/bash

# 백업 스크립트 (Amazon Linux 호환)

set -e

# 색상 정의
GREEN='\033[0;32m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# 백업 디렉토리 생성
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

log_info "백업 시작: $BACKUP_DIR"

# FAISS 인덱스 백업
if [ -d "faiss_index" ]; then
    log_info "FAISS 인덱스 백업 중..."
    tar -czf $BACKUP_DIR/faiss_index.tar.gz faiss_index/
fi

# 가이드북 PDF 백업
if [ -d "guidebook_pdfs" ]; then
    log_info "가이드북 PDF 백업 중..."
    tar -czf $BACKUP_DIR/guidebook_pdfs.tar.gz guidebook_pdfs/
fi

# 로그 백업
if [ -d "logs" ]; then
    log_info "로그 파일 백업 중..."
    tar -czf $BACKUP_DIR/logs.tar.gz logs/
fi

# 환경설정 파일 백업
if [ -f ".env" ]; then
    log_info "환경설정 파일 백업 중..."
    cp .env $BACKUP_DIR/
fi

# 전체 백업 아카이브 생성
log_info "전체 백업 아카이브 생성 중..."
tar -czf backups/backup_$(date +%Y%m%d_%H%M%S).tar.gz -C $BACKUP_DIR .

# 30일 이상된 백업 파일 삭제
find backups/ -name "backup_*.tar.gz" -mtime +30 -delete

log_info "✅ 백업 완료: $BACKUP_DIR"
log_info "전체 백업 파일: backups/backup_$(date +%Y%m%d_%H%M%S).tar.gz"
