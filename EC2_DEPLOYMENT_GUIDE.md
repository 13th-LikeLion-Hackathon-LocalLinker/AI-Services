# LocalLinker AI EC2 배포 가이드

## 📋 사전 준비사항

### 1. AWS EC2 인스턴스 설정

#### 인스턴스 사양 권장사항
- **최소 사양**: t3.medium (2 vCPU, 4GB RAM)
- **권장 사양**: t3.large (2 vCPU, 8GB RAM) 또는 그 이상
- **스토리지**: 최소 20GB (gp3 권장)
- **운영체제**: Amazon Linux 2023 (권장) 또는 Amazon Linux 2

#### 보안 그룹 설정
```
인바운드 규칙:
- SSH (22): 본인 IP만 허용
- Custom TCP (8100): 0.0.0.0/0 (API 서버 포트)
```

### 2. 탄력적 IP 설정 (권장)
- EC2 콘솔에서 탄력적 IP 할당
- 인스턴스에 탄력적 IP 연결 (재부팅 시에도 IP 유지)

## 🚀 배포 단계

### 1단계: EC2 인스턴스 접속 및 기본 설정

```bash
# EC2 인스턴스 접속
ssh -i your-key.pem ec2-user@your-ec2-ip

# 시스템 업데이트 (Amazon Linux 2023)
sudo dnf update -y

# 또는 Amazon Linux 2를 사용하는 경우
# sudo yum update -y

# 필수 패키지 설치 (Amazon Linux 2023)
sudo dnf install -y curl wget git unzip

# 또는 Amazon Linux 2를 사용하는 경우
# sudo yum install -y curl wget git unzip
```

### 2단계: Docker 설치

#### Amazon Linux 2023의 경우:
```bash
# Docker 설치
sudo dnf install -y docker

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker ec2-user

# Docker 서비스 시작 및 부팅시 자동 시작 설정
sudo systemctl start docker
sudo systemctl enable docker

# 새로운 그룹 권한 적용
newgrp docker
```

#### Amazon Linux 2의 경우:
```bash
# Docker 설치
sudo yum install -y docker

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker ec2-user

# Docker 서비스 시작 및 부팅시 자동 시작 설정
sudo systemctl start docker
sudo systemctl enable docker

# 새로운 그룹 권한 적용
newgrp docker
```

### 3단계: 프로젝트 코드 배포

```bash
# 프로젝트 디렉토리 생성
mkdir -p ~/locallinker-ai
cd ~/locallinker-ai

# GitHub에서 코드 클론 (또는 파일 업로드)
git clone <your-repository-url> .

# 또는 로컬에서 파일 업로드 (rsync 사용)
# rsync -avz -e "ssh -i your-key.pem" ./LocalLinker-ai/ ec2-user@your-ec2-ip:~/locallinker-ai/
```

### 4단계: 환경변수 설정

```bash
# .env 파일 생성
cp env.example .env

# .env 파일 편집
nano .env
```

**.env 파일 예시:**
```env
OPENAI_API_KEY=sk-your-actual-openai-api-key
OPENAI_CHAT_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
TOP_K_RESULTS=5
MAX_TOKENS=1000
TEMPERATURE=0.7
OPENAI_TIMEOUT=30
```

### 5단계: 배포 실행

```bash
# 배포 스크립트 실행 권한 부여
chmod +x deploy.sh

# 배포 실행
./deploy.sh
```

## 🔧 배포 후 관리

### 서비스 상태 확인
```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그 확인
docker-compose logs -f locallinker-ai
```

### 서비스 관리 명령어
```bash
# 서비스 재시작
docker-compose restart

# 서비스 중지
docker-compose down

# 서비스 시작
docker-compose up -d

# 이미지 재빌드 후 재시작
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 데이터 백업
```bash
# FAISS 인덱스 백업
tar -czf faiss_backup_$(date +%Y%m%d).tar.gz faiss_index/

# 로그 백업
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

## 🔒 보안 설정

### 1. 방화벽 설정

```bash
# firewalld 설정 (Amazon Linux 기본 방화벽)
sudo systemctl start firewalld
sudo systemctl enable firewalld

# SSH와 8100 포트 허용
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-port=8100/tcp

# 설정 적용
sudo firewall-cmd --reload

# 필요한 경우 특정 IP만 허용하고 싶다면
# sudo firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='YOUR_IP_ADDRESS' port protocol='tcp' port='8100' accept"

# 현재 설정 확인
sudo firewall-cmd --list-all
```

### 2. 자동 업데이트 설정

```bash
# Amazon Linux 2023의 경우
# 자동 보안 업데이트는 기본적으로 활성화되어 있음
sudo dnf config-manager --set-enabled amzn2023-kernel-livepatch

# Amazon Linux 2의 경우
# sudo yum update --security
# crontab을 이용한 자동 업데이트 설정
# echo "0 2 * * * /usr/bin/yum update -y --security" | sudo crontab -
```

## 📊 모니터링

### 1. 시스템 모니터링
```bash
# 시스템 리소스 확인
htop
df -h
free -h

# Docker 리소스 사용량
docker stats
```

### 2. 로그 모니터링
```bash
# 실시간 로그 모니터링
tail -f logs/etl_pipeline.log

# 에러 로그 검색
grep -i error logs/*.log
```

## 🚨 문제 해결

### 일반적인 문제들

1. **메모리 부족**
   ```bash
   # 스왑 파일 생성
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

2. **Docker 권한 문제**
   ```bash
   sudo usermod -aG docker ec2-user
   newgrp docker
   ```

3. **포트 충돌**
   ```bash
   # 포트 사용 확인
   sudo netstat -tulpn | grep :8100
   sudo netstat -tulpn | grep :8000
   
   # 또는 ss 명령어 사용
   sudo ss -tulpn | grep :8100
   ```

4. **서비스 연결 테스트**
   ```bash
   # API 서비스 테스트
   curl http://localhost:8100/api/health
   curl http://YOUR_EC2_IP:8100/api/health
   ```

## 📞 지원

문제가 발생하면 다음을 확인해주세요:
1. Docker 컨테이너 로그: `docker-compose logs`
2. 시스템 로그: `sudo journalctl -f`
3. 디스크 공간: `df -h`
4. 메모리 사용량: `free -h`
