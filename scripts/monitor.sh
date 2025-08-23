#!/bin/bash

# 모니터링 스크립트 (Amazon Linux 호환)

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== LocalLinker AI 서비스 모니터링 ===${NC}"
echo ""

# 서비스 상태 확인
echo -e "${GREEN}📊 서비스 상태${NC}"
docker-compose ps
echo ""

# 시스템 리소스 확인
echo -e "${GREEN}💻 시스템 리소스${NC}"
echo "CPU 사용률:"
# Amazon Linux에서도 작동하는 CPU 사용률 확인
if command -v top &> /dev/null; then
    top -bn1 | grep -i "cpu(s)" | awk '{print $2 + $4"%"}' || echo "측정 불가"
else
    echo "top 명령어 없음"
fi

echo "메모리 사용률:"
if command -v free &> /dev/null; then
    free -h | awk 'NR==2{printf "사용: %s/%s (%.2f%%)\n", $3,$2,$3*100/$2 }' || echo "측정 불가"
else
    echo "free 명령어 없음"
fi

echo "디스크 사용률:"
df -h | grep -vE '^Filesystem|tmpfs|cdrom|devtmpfs' | awk '{print $5 " " $1 " " $4}'
echo ""

# Docker 컨테이너 리소스 사용량
echo -e "${GREEN}🐳 Docker 컨테이너 리소스${NC}"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
echo ""

# 서비스 헬스체크
echo -e "${GREEN}🏥 서비스 헬스체크${NC}"
if curl -s -f http://localhost:8100/api/health > /dev/null; then
    echo -e "${GREEN}✅ API 서비스: 정상 (포트 8100)${NC}"
else
    echo -e "${RED}❌ API 서비스: 비정상 (포트 8100)${NC}"
fi
echo ""

# 최근 로그 확인
echo -e "${GREEN}📋 최근 로그 (최근 10줄)${NC}"
if [ -f "logs/etl_pipeline.log" ]; then
    echo "ETL Pipeline 로그:"
    tail -5 logs/etl_pipeline.log
    echo ""
fi

echo "Docker 로그:"
docker-compose logs --tail=5 locallinker-ai
echo ""

# 디스크 공간 경고
echo -e "${GREEN}⚠️  디스크 공간 경고${NC}"
df -h | awk '$5 > 80 {print "경고: " $1 " 디스크 사용률이 " $5 " 입니다."}'
echo ""

# 네트워크 연결 확인
echo -e "${GREEN}🌐 네트워크 연결${NC}"
echo "활성 연결:"
# ss 또는 netstat 사용 (Amazon Linux에서 모두 사용 가능)
if command -v ss &> /dev/null; then
    ss -tuln | grep -E ':8100|:8000' || echo "8100, 8000 포트에서 활성 연결 없음"
elif command -v netstat &> /dev/null; then
    netstat -tuln | grep -E ':8100|:8000' || echo "8100, 8000 포트에서 활성 연결 없음"
else
    echo "네트워크 상태 확인 도구 없음"
fi
echo ""

echo -e "${BLUE}=== 모니터링 완료 ===${NC}"
