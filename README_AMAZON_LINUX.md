# LocalLinker AI - Amazon Linux EC2 배포 가이드

## 🚀 빠른 시작 (Amazon Linux)

### 1. EC2 인스턴스 준비
- **AMI**: Amazon Linux 2023 또는 Amazon Linux 2
- **인스턴스 타입**: t3.medium 이상 권장
- **보안 그룹**: SSH (22), Custom TCP (8100) 포트 오픈

### 2. 코드 배포 및 실행

```bash
# EC2 접속
ssh -i your-key.pem ec2-user@your-ec2-ip

# 프로젝트 클론
git clone <your-repository-url> ~/locallinker-ai
cd ~/locallinker-ai

# 환경변수 설정
cp env.example .env
nano .env  # OpenAI API 키 등 설정

# Amazon Linux용 배포 스크립트 실행
chmod +x deploy_amazon_linux.sh
./deploy_amazon_linux.sh
```

### 3. 서비스 확인
```bash
# 서비스 상태 확인
curl http://localhost:8100/api/health

# API 문서 접속
curl http://YOUR_EC2_IP:8100/docs
```

## 📊 관리 명령어

```bash
# 서비스 모니터링
./scripts/monitor.sh

# 백업 생성
./scripts/backup.sh

# 애플리케이션 업데이트
./scripts/update.sh

# 로그 확인
docker-compose logs -f

# 서비스 재시작
docker-compose restart

# 서비스 중지
docker-compose down
```

## 🔧 Amazon Linux 특화 명령어

### 시스템 관리
```bash
# Amazon Linux 2023
sudo dnf update -y
sudo dnf install -y htop

# Amazon Linux 2
sudo yum update -y
sudo yum install -y htop

# 방화벽 관리
sudo firewall-cmd --list-all
sudo systemctl status firewalld
```

### Docker 관리
```bash
# Docker 서비스 상태
sudo systemctl status docker

# Docker 자동 시작 설정
sudo systemctl enable docker

# Docker 권한 추가 (필요시)
sudo usermod -aG docker ec2-user
newgrp docker
```

## 🔥 문제 해결

### Docker 권한 문제
```bash
sudo usermod -aG docker ec2-user
newgrp docker
# 또는 로그아웃 후 재접속
```

### 포트 접근 문제
```bash
# 방화벽 설정 확인
sudo firewall-cmd --list-all

# 포트 8100 추가
sudo firewall-cmd --permanent --add-port=8100/tcp
sudo firewall-cmd --reload
```

### 메모리 부족
```bash
# 스왑 파일 생성
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 📞 지원

자세한 내용은 `EC2_DEPLOYMENT_GUIDE.md`를 참조하세요.

---

**참고**: Ubuntu/Debian 환경에서는 `deploy.sh` 스크립트를 사용하세요.
