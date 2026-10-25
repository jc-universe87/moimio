🌐 [English](beginner.md) · [Deutsch](beginner.de.md) · **한국어** · [Español](beginner.es.md) · [Português (Brasil)](beginner.pt-BR.md) · [Français](beginner.fr.md)

# 초보자 설치 가이드

터미널을 한 번도 열어 본 적 없지만 실제 행사를 위해 Moimio를 실행해야 하는 분을 위한 가이드입니다. 천천히 가겠습니다.

Docker와 Linux 서버에 이미 익숙하다면 [빠른 설치 가이드](quick-guide.ko.md)가 같은 내용을 30분 안에 다룹니다.

개발자가 아니어도 됩니다. 명령을 꼼꼼히 복사하고, 잘 안 될 때 도움을 청할 마음만 있으면 됩니다.

---

## 시작하기 전에 솔직한 이야기

Moimio 설치는 데스크톱 앱 설치보다 손이 더 갑니다. 아직 "버튼 누르고, 기다리면, 끝" 같은 방식은 없습니다. 가이드에 없는 문제를 만나면 기술에 밝은 친구에게 묻거나 오류 메시지를 AI 채팅 도우미에 붙여 넣어 보세요. 보통 몇 분이면 해결됩니다.

처음 하신다면 **2시간 정도** 잡아 두세요. 대부분은 다운로드를 기다리는 시간입니다. 두 번째부터는 훨씬 빠릅니다.

---

## 직접 호스팅해야 할까요? 현실 점검

설치는 쉬운 부분입니다. 더 어려운 질문은 그 뒤 몇 달 동안 실제 서버를 운영하는 일이 어떤 모습이냐는 것입니다. 특히 행사가 한창일 때 무언가 고장 나서 20분 안에 되살려야 하는 상황이라면요.

직접 호스팅하는 Moimio는 이제 여러분이 책임지는 작은 Linux 서버입니다. 구체적으로는 이렇습니다.

- **서버가 계속 켜져 있어야 합니다.** 사무실이 정전되거나, 행사장 와이파이가 끊기거나, VPS 업체에 장애가 나면 되살릴 때까지 등록이 멈춥니다.
- **업데이트를 적용해야 합니다.** 새 Moimio 버전(명령 하나, [Moimio 업데이트하기](#moimio-업데이트하기) 참고), Ubuntu 보안 패치, 가끔의 Docker 업데이트. 매주는 아니지만 없지도 않습니다.
- **곤란한 때에 문제가 생깁니다.** SSL 인증서 갱신이 실패하거나, 업데이트 후 데이터베이스 마이그레이션이 실행되지 않거나, 데이터베이스 컨테이너가 다시 시작되지 않을 수 있습니다. 해결은 보통 명령 한두 개입니다. *어떤 명령인지 안다면* 말이죠.
- **백업은 여러분 몫입니다.** Moimio에 백업 기능이 있지만, 큰 변경 전에 실제로 실행하고 결과를 안전한 곳에 보관하는 것은 여러분이 해야 합니다.
- **DNS, 인증서, 터널은 운영상 깨지기 쉽습니다.** 도메인이 만료되거나, IP가 바뀌거나, Cloudflare 토큰이 교체되면 등록 양식이 404가 됩니다.

**스스로 점검해 보세요.** 계속하기 전에 솔직하게 확인해 주세요.

- [ ] 터미널 명령을 실행하고 오류 출력을 읽는 데 익숙하다.
- [ ] 서비스가 시작되지 않을 때 로그를 찾아 읽는 방법을 안다.
- [ ] 서버 IP 주소가 바뀌면 DNS를 업데이트하는 방법을 안다.
- [ ] 행사 중 밤 11시에 무언가 고장 나면 고쳐 줄 사람(또는 실력)이 있다.
- [ ] 백업을 하려는 마음만이 아니라 실제 백업 계획이 있다.

**하나라도 *아니요*라면 같은 제품의 호스팅 버전인 [moimio.app](https://moimio.app)을 고려해 주세요.** 같은 코드, 같은 배정 엔진, 같은 등록 흐름으로 돌아갑니다. 호스팅, 백업, 업데이트, SSL을 대신 처리합니다. 현재 요금은 웹사이트에 있습니다.

그래도 직접 호스팅하고 싶다면 이 가이드가 계속 안내합니다. 직접 호스팅의 비용은 VPS 월 몇 유로가 아니라, 행사 중에 언제든 대응할 수 있어야 한다는 부담입니다. 잘 알고 결정하세요.

---

## 호스팅 방법 고르기

Moimio를 실행하는 합리적인 방법은 두 가지입니다. 상황에 맞는 쪽을 고르세요.

### → 경로 A: 작은 서버("VPS") 임대하기

VPS는 데이터 센터에 있는 작은 컴퓨터로, 월 단위로 빌려 원격으로 접속합니다. 월 €4~10 정도입니다. 항상 켜져 있고, 항상 접속할 수 있으며, 여러분 쪽에서 관리할 장비가 없습니다.

**이런 경우에 좋습니다:** 유지 관리를 적게 하고 싶을 때, 몇 달 전부터 등록을 받을 때, 집의 컴퓨터를 Moimio 실행에 묶어 두고 싶지 않을 때.

아래 [경로 A: VPS 임대하기](#경로-a-vps-임대하기)로 이어집니다.

### → 경로 B: 내 컴퓨터나 미니 PC에서 직접 호스팅하기

이미 가진 컴퓨터에서 Moimio를 실행하고, Cloudflare Tunnel이라는 무료 서비스로 인터넷에 공개합니다. 호스팅 비용이 없습니다.

**이런 경우에 좋습니다:** 데이터 주권이 꼭 지켜야 할 조건이고(참가자 데이터가 반드시 우리 소유의 하드웨어에 있어야 할 때), 행사 중에 Linux 기기의 문제를 해결할 사람이 있을 때.

집이나 사무실의 호스트는 VPS보다 확실히 덜 안정적입니다. 전원, 인터넷, cloudflared 연결 프로그램, 호스트 운영 체제 자체가 고장 날 수 있고, 누군가 기기에 가서 고칠 때까지 등록 양식이 멈춥니다. 데이터 주권이 꼭 필요한 조건이 아니라면 경로 A(VPS)나 [moimio.app](https://moimio.app)이 더 간단합니다.

아래 [경로 B: Cloudflare Tunnel로 직접 호스팅하기](#경로-b-cloudflare-tunnel로-직접-호스팅하기)로 이어집니다.

두 경로 모두 [**4단계: Moimio 설치하기**](#4단계-moimio-설치하기)에서 만납니다. Moimio를 어디서 실행하든 이 단계는 같습니다.

---

## 경로 A: VPS 임대하기

VPS 업체는 데이터 센터의 작은 컴퓨터를 제공합니다. Hetzner, OVH, Scaleway, DigitalOcean, Linode, Vultr, Contabo와 여러 지역 업체 등 많습니다. Moimio에 필요한 사양은 대부분 월 €4~10입니다.

유럽의 교회나 선교 단체라면 GDPR 때문에 유럽 데이터 센터가 있는 업체가 나은 경우가 많습니다(참가자 데이터가 EU 안에 머뭅니다). Hetzner Cloud(독일/핀란드)와 OVH(프랑스/독일)가 흔한 선택입니다. 한국, 일본, 미국 등 다른 곳의 주최자라면 보통 그 지역 클라우드 업체로 충분합니다. Moimio는 어느 업체든 상관없습니다.

> **특정 업체를 추천하는 것이 아닙니다.** 이 가이드는 문서가 잘 되어 있고 저렴하다는 이유로 Hetzner Cloud를 *예시*로 들 뿐, 추천하는 것은 아닙니다. 믿을 수 있는 곳을 고르세요. 설정은 어디서나 비슷합니다.

### 1단계: 가입하고 서버 만들기

VPS 업체마다 가입과 서버 생성 절차가 다릅니다. 업체가 관리 화면을 바꿀 때마다 낡아 버리는 단계별 설명을 여기 다시 쓰기보다, 업체의 시작 안내 문서를 따르세요.

Hetzner Cloud의 경우: <https://docs.hetzner.com/cloud/servers/getting-started/creating-a-server/>

서버를 만들 때 Moimio에 중요한 선택은 다음과 같습니다.

- **운영 체제:** **Ubuntu 24.04**(또는 22.04). 문제가 생겼을 때 도움을 받기가 가장 쉽습니다.
- **서버 크기:** 150명 규모 행사라면 대략 **2 vCPU + 2 GB RAM + 40 GB 디스크**로 충분합니다. 대부분의 업체에서 "소형" 등급이며 월 €4~5입니다.
- **SSH 키:** 서버를 만들 때 SSH 키를 추가하세요(비밀번호 없이 접속할 수 있습니다). 아직 키가 없다면 서버를 만들기 전에 [2단계: SSH 키 만들기](#2단계-ssh-키-만들기)로 갔다가 돌아오세요.
- **위치:** 참가자들이 있는 곳과 가까운 데이터 센터를 고르세요. 유럽 행사라면 보통 EU 데이터 센터가 낫고, 다른 지역 행사라면 지리적·법적으로 알맞은 곳을 고르세요.

서버가 만들어지면 업체가 **공인 IP 주소**(예: `203.0.113.42`)를 알려 줍니다. 접속할 때 필요하니 **이 IP 주소를 적어 두세요**.

### 2단계: SSH 키 만들기

SSH 키는 서로 짝이 맞는 파일 두 개입니다. VPS 업체에 주는 **공개 키**와, 디지털 집 열쇠처럼 노트북에만 두는 **개인 키**입니다. 둘이 함께 있으면 노트북에서 비밀번호 없이 서버에 로그인할 수 있습니다.

노트북에서 터미널을 여세요.

- **macOS:** Spotlight → "터미널".
- **Linux:** 아무 터미널 앱.
- **Windows:** Microsoft Store에서 [Windows Terminal](https://aka.ms/terminal)을 설치하거나 기본 PowerShell을 쓰세요.

그다음 입력하세요.

```bash
ssh-keygen -t ed25519 -C "you@your-email.com"
```

(이메일은 그냥 이름표일 뿐이며, 이메일이 발송되지 않습니다.) 질문이 나오면:

- Enter를 눌러 기본 파일 위치를 받아들이세요.
- 기억할 수 있는 암호 문구를 입력하세요(노트북을 도난당했을 때 키를 보호합니다). Enter를 누르세요.
- 암호 문구를 한 번 더 입력하세요. Enter를 누르세요.

공개 키를 확인하세요.

```bash
cat ~/.ssh/id_ed25519.pub
```

`ssh-ed25519 AAAA...`로 시작하는 긴 한 줄이 나옵니다. 줄 전체를 복사하세요. VPS 업체의 SSH 키 설정에 추가하세요(업체마다 관리 화면에 이를 위한 메뉴가 있습니다). 이제 서버(새로 만들거나 다시 설치한 서버)가 노트북의 로그인을 받아들입니다.

이 단계에서 막히면 "[VPS 업체 이름] SSH 키 추가"로 검색하세요. 모든 업체에 관련 문서가 있습니다.

### 3단계: 서버에 접속하기

노트북에서 터미널을 여세요.

```bash
ssh root@203.0.113.42
```

(`203.0.113.42`를 여러분 서버의 IP 주소로 바꾸세요.)

처음에는 이 호스트를 믿을지 묻습니다. `yes`를 입력하고 Enter를 누르세요. 묻는다면 SSH 키 암호 문구를 입력하세요. 다음과 비슷한 화면이 나와야 합니다.

```
Welcome to Ubuntu 24.04.x LTS ...
root@your-server:~#
```

이것이 **서버의** 터미널 프롬프트입니다. 이제 입력하는 모든 것은 노트북이 아니라 서버에서 실행됩니다. **접속 성공입니다.**

`Permission denied (publickey)`가 나오면 SSH 키가 서버에 연결되지 않은 것입니다. 업체의 SSH 키 설정을 다시 확인하세요.

이제 [4단계: Moimio 설치하기](#4단계-moimio-설치하기)로 가세요.

---

## 경로 B: Cloudflare Tunnel로 직접 호스팅하기

이 경로에는 계속 켜 둘 수 있는 컴퓨터가 필요합니다. 데스크톱, 미니 PC, 더 이상 쓰지 않는 오래된 노트북, 또는 Raspberry Pi 4(4 GB나 8 GB). 그 컴퓨터가 있는 곳의 안정적인 인터넷 연결도 필요합니다.

### 1단계: 컴퓨터 준비하기

아직 없다면 **Linux**를 설치하세요.

- **오래된 노트북이나 데스크톱:** Ubuntu Desktop 24.04 LTS가 가장 쉽습니다. <https://ubuntu.com/download/desktop>에서 내려받아 설치 안내를 따르세요.
- **Raspberry Pi:** Raspberry Pi OS나 ARM용 Ubuntu Server를 쓰세요. 각각의 문서에 설정 방법이 있습니다.
- **이 용도로 산 미니 PC:** 대부분 Windows가 깔려 나오지만 Ubuntu도 깔끔하게 설치됩니다. Raspberry Pi Imager와 Ubuntu 설치 프로그램 모두 문서가 잘 되어 있습니다.

꼭 Linux여야 하는 것은 *아닙니다*. Moimio는 Docker Desktop을 쓰는 macOS, Docker Desktop과 WSL2를 쓰는 Windows에서도 실행됩니다. 하지만 몇 달씩 켜 두는 서버라면 Linux가 가장 예측 가능한 선택입니다.

### 2단계: Docker 설치하기

그 컴퓨터에서 터미널을 여세요(다른 곳에서 SSH로 접속하는 것이 아니라 기기에서 직접, 또는 설정해 두었다면 같은 네트워크의 노트북에서 SSH로). 그다음:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

새 그룹 설정이 적용되도록 로그아웃했다가 다시 로그인하세요(또는 다시 시작하세요). 그다음 확인하세요.

```bash
docker --version
docker run --rm hello-world
```

"Hello from Docker!"가 나오면 Docker가 작동하는 것입니다.

### 3단계: Cloudflare Tunnel 설정하기

**Cloudflare Tunnel**은 공유기 포트를 열거나 집 IP를 몰라도 집이나 사무실 컴퓨터에 공개 URL을 주는 무료 서비스입니다. 접속은 Cloudflare 네트워크를 거치며, TLS도 Cloudflare가 처리합니다.

1. Cloudflare 계정이 없다면 <https://dash.cloudflare.com/sign-up>에서 가입하세요. 무료 요금제로 충분합니다.
2. 도메인을 Cloudflare에 추가하세요(도메인 이름이 필요합니다. 아직 없다면 아래 [도메인 섹션](#도메인-이름-마련하기)을 참고하세요).
3. Cloudflare 대시보드에서 **Zero Trust → Networks → Tunnels**로 가세요. **Create a tunnel**을 클릭하고 이름(예: "moimio-home")을 붙인 뒤, Cloudflare 안내에 따라 Linux 기기에 연결 프로그램을 설치하세요. Cloudflare 설정 마법사가 운영 체제에 맞는 정확한 `cloudflared` 설치 명령을 알려 줍니다.
4. 터널의 **Public hostnames** 섹션에서 `events.yourchurch.org` 같은 호스트 이름을 추가하고 **Service**를 `HTTP://localhost:6120`으로 설정하세요.
5. 저장하세요. Cloudflare가 TLS 인증서를 자동으로 발급하고 갱신합니다.

다음 단계에서 Moimio를 실행하면, 어느 브라우저에서든 `https://events.yourchurch.org`로 터널을 거쳐 HTTPS가 이미 설정된 상태로 접속할 수 있습니다.

최신 안내: <https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/>

### 직접 호스팅에서 문제가 생길 때

실제 행사 중 직접 호스팅에서 생기는 문제를 대략 자주 일어나는 순서로 보면:

- 행사장이나 사무실의 **정전**으로 서버가 꺼집니다. 컴퓨터와 공유기에 UPS(무정전 전원 장치, 약 €80)를 달아 대비하세요.
- 행사장이나 사무실의 **인터넷 장애**로 공개 URL이 끊깁니다. 바로 바꿔 연결할 수 있는 휴대폰 테더링을 준비하거나, 중단 위험을 감수하세요.
- **cloudflared 연결 프로그램이 멈춥니다.** 시스템 업데이트, 메모리 급증, 연결 프로그램 버전 차이로 터널이 예고 없이 끊길 수 있습니다. 보통 호스트에서 `sudo systemctl restart cloudflared`로 해결됩니다. 호스트에 접근할 수 있고 명령을 안다면 쉽습니다.
- **호스트 운영 체제 자체가 응답하지 않습니다.** 새로 설치한 Ubuntu에서는 드물지만, 다른 작업도 돌리는 Raspberry Pi나 몇 달 동안 재부팅하지 않은 호스트에서는 더 자주 일어납니다. 복구하려면 보통 기기 앞에 직접 가야 합니다.

이상한 문제가 아니라, 데이터 센터가 아닌 곳에서 서버를 운영할 때의 평범한 고장들입니다. 문제는 행사 때 이를 고칠 사람이 있느냐입니다. 있다면 데이터를 물리적으로 우리 공간에 두는 대가로 직접 호스팅은 합리적인 선택입니다. 없다면 [moimio.app](https://moimio.app)이 이 네 가지 고장을 모두 대신 감당합니다.

이제 [4단계: Moimio 설치하기](#4단계-moimio-설치하기)로 가세요.

---

## 4단계: Moimio 설치하기

VPS든 직접 호스팅이든 이 단계는 같습니다. 지금 쓰는 터미널은 SSH로 접속한 VPS(경로 A)이거나 내 기기(경로 B)입니다. 여기서부터 "**서버**"는 Moimio가 실행되는 컴퓨터를 뜻합니다.

### 4.1 코드 내려받기

```bash
git clone https://github.com/pistio/moimio.git
cd moimio
```

Ubuntu에는 `git`이 미리 설치되어 있습니다. 내려받기는 몇 초면 끝납니다.

이제 프롬프트에 `moimio` 폴더 안에 있다고 표시됩니다.

### 4.2 Moimio 설정하기

```bash
cp .env.example .env
nano .env
```

`nano`는 간단한 텍스트 편집기입니다. 화살표 키로 이동하세요. 다음 줄들을 찾아 수정하세요.

**`SECRET_KEY`**: 자리 표시자를 진짜 무작위 문자열로 바꾸세요. 만들려면 노트북에서 **두 번째 터미널**을 열고:

```bash
openssl rand -hex 64
```

출력을 복사해 `nano`에서 새 `SECRET_KEY` 값으로 붙여 넣으세요.

**`POSTGRES_PASSWORD`**: `moimio_dev`를 다른 무작위 문자열로 바꾸세요(더 짧은 문자열은 `openssl rand -hex 32`로 만드세요). 처음 시작하기 전인 지금 하세요. 데이터베이스는 처음 시작할 때의 비밀번호를 기억합니다.

**`DATABASE_URL`**: 이 줄은 그대로 두어도 됩니다. Moimio가 `POSTGRES_PASSWORD`로 실제 데이터베이스 주소를 만들어 줍니다. 깔끔하게 하고 싶다면 이 줄의 `moimio_dev`도 새 비밀번호로 바꾸세요.

**`LOG_LEVEL`**: `INFO`로 두세요. `DEBUG` 설정은 참가자 이름, 주소, 생년월일을 서버 로그 파일에 기록하므로, 가상의 데이터로 문제를 찾을 때만 쓰세요.

저장: **Ctrl-O**, 그다음 **Enter**. 끝내기: **Ctrl-X**.

지금은 이 파일의 다른 부분을 건드릴 필요가 없습니다. 이메일 설정은 선택 사항이며 아래 [이메일 보내기 (선택)](#이메일-보내기-선택)에서 다룹니다.

### 4.3 Moimio 시작하기

```bash
docker compose up -d --build
```

Docker가 기본 이미지를 내려받고, Moimio 이미지를 빌드하고, 컨테이너 세 개(데이터베이스, 백엔드, 프런트엔드)를 시작합니다. 처음에는 **5~10분** 걸립니다.

끝나면:

```bash
docker compose logs --tail=30 backend
```

다음을 찾으세요.

```
INFO  [alembic.runtime.migration] Running upgrade ... -> <latest migration>
INFO  Application startup complete.
```

이 줄들이 보이면 Moimio가 실행된 것입니다(첫 줄은 데이터베이스를 설정하거나 업데이트해야 할 때만 나오므로 둘째 줄만 보여도 괜찮습니다). **오류 줄이 보이면 진행하지 마세요.** 이 가이드 아래쪽의 문제 해결 섹션을 참고하세요.

### 4.4 초기 설정(관리자 계정 만들기)

<p align="center">
  <img src="../assets/first-time-setup.png" alt="첫 최고 관리자 계정을 만드는 초기 설정 마법사" width="420">
  <br>
  <em>첫 최고 관리자 계정을 만드는 초기 설정 마법사</em>
</p>

브라우저를 여세요.

- **경로 A(VPS):** `http://YOUR_SERVER_IP:6120`으로 가세요(예: `http://203.0.113.42:6120`).
- **경로 B(직접 호스팅):** 같은 기기라면 `http://localhost:6120`, Cloudflare Tunnel을 설정했다면 `https://events.yourchurch.org`로 가세요.

자동으로 **초기 설정** 화면이 나옵니다. Moimio는 계정이 하나도 없을 때만 이 화면을 보여 줍니다. 다음을 입력하세요.

- **성명**: Moimio에 표시될 이름.
- **이메일**: 로그인할 때 씁니다.
- **비밀번호**와 **비밀번호 확인**: 8자 이상. 비밀번호 관리자를 쓰면 좋습니다.

아래의 선택기로 화면 언어를 바꿀 수 있습니다. **최고 관리자 생성**을 클릭하세요. 그러면 로그인 페이지가 나옵니다. 방금 정한 이메일과 비밀번호로 로그인하세요. 이 첫 계정이 모든 것을 할 수 있는 **최고 관리자**입니다.

🎉 **Moimio 설치를 마쳤습니다.**

<p align="center">
  <img src="../assets/welcome-splash.png" alt="행사가 아직 없을 때 표시되는 Moimio에 오신 것을 환영합니다 화면" width="560">
  <br>
  <em>Moimio에 오신 것을 환영합니다 화면</em>
</p>

아직 행사가 없으므로 행사의 세 단계(준비, 등록, 행사)를 설명하는 **Moimio에 오신 것을 환영합니다** 화면이 보입니다. **첫 행사 만들기**를 클릭해 시작하세요.

지금 해 두면 좋은 일이 하나 더 있습니다. 왼쪽 메뉴의 **워크스페이스**를 클릭하고, 단체에 **개인정보 처리방침**이 있다면 그 웹 주소를 붙여 넣으세요. 그러면 등록 양식을 작성하는 사람들이 동의 체크박스 바로 옆에서 링크를 보게 됩니다.

---

## 5단계: 실제 도메인으로 접속하게 하기(선택, 권장)

`http://203.0.113.42:6120`으로 Moimio에 접속하는 것은 여러분에게는 되지만, 참가자에게 보낼 주소는 아닙니다. 실제 등록에는 `https://events.yourchurch.org` 같은 주소가 필요합니다. HTTPS를 쓰면 "새 버전이 있습니다" 안내나 오프라인 캐시처럼 브라우저가 보안 사이트에서만 허용하는 편의 기능도 켜집니다.

**경로 B**(Cloudflare Tunnel로 직접 호스팅)를 택했다면 이미 끝났습니다. 터널 URL이 공개 주소입니다. 이 섹션은 건너뛰세요.

**경로 A**(VPS)를 택했다면 계속하세요.

### 도메인 이름 마련하기

아직 없다면 아무 도메인 등록 업체(Namecheap, Porkbun, INWX, Cloudflare Registrar, OVH 모두 괜찮습니다)에서 사세요. `.org` 도메인은 연 €10~15 정도입니다.

도메인을 따로 살 필요는 없습니다. 이미 가진 도메인의 하위 도메인으로도 충분합니다. 교회 주소가 `yourchurch.org`라면 새 도메인보다 `events.yourchurch.org` 같은 하위 도메인이 더 깔끔합니다.

도메인 등록과 DNS가 막막하게 느껴진다면 기술에 밝은 친구에게 묻거나 상황을 AI 채팅 도우미에 설명해 보세요. 사용하는 등록 업체의 절차를 몇 분 안에 안내해 줄 수 있습니다.

### 도메인을 서버에 연결하기(VPS 경로)

등록 업체의 DNS 설정에서 **A 레코드**를 추가하세요.

| 이름 | 유형 | 값 |
|---|---|---|
| `events`(또는 원하는 하위 도메인) | A | `203.0.113.42`(서버 IP) |

저장하세요. DNS는 몇 분(때로는 최대 1시간) 안에 퍼집니다. 확인해 보세요.

```bash
ping events.yourchurch.org
```

서버 IP에서 응답이 오면 DNS가 작동하는 것입니다.

### HTTPS(TLS) 추가하기

깔끔한 방법이 두 가지 있습니다. 둘 다 잘 작동하니 편한 쪽을 고르세요.

#### 방법 1: Cloudflare를 앞에 두기

TLS가 처음이라면 가장 간단합니다. Cloudflare를 리버스 프록시로 쓰세요.

1. 도메인을 (무료) Cloudflare 계정에 추가하세요.
2. [경로 B, 3단계](#3단계-cloudflare-tunnel-설정하기)와 똑같이 VPS에 Cloudflare Tunnel을 설정하고 `HTTP://localhost:6120`을 가리키게 하세요(터널을 쓰면 위의 A 레코드가 필요 없습니다. Cloudflare가 DNS 항목을 만들어 줍니다).
3. Cloudflare가 HTTPS를 자동으로 처리합니다. `https://events.yourchurch.org`로 접속하면 터널이 Moimio까지 연결해 줍니다.

일반적인 "proxied" A 레코드만으로는 부족합니다. Cloudflare는 방문자를 표준 웹 포트(80/443)로 넘기는데 Moimio는 6120에서 기다리기 때문입니다. 터널은 이 문제를 피하고, 포트를 하나도 열 필요가 없습니다.

사실상 "한 번 설정하면 잊어도 되는" 방법이라 많은 직접 호스팅 사용자가 결국 이 방법을 씁니다.

#### 방법 2: 호스트에 Caddy 설치하기

같은 서버에 Moimio와 함께 Caddy를 설치하세요. Caddy가 Let's Encrypt 인증서를 자동으로 받아 옵니다.

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

`/etc/caddy/Caddyfile`을 수정하세요.

```bash
sudo nano /etc/caddy/Caddyfile
```

내용을 다음으로 바꾸세요.

```
events.yourchurch.org {
    reverse_proxy localhost:6120
}
```

(실제 도메인으로 바꾸세요.) 저장(Ctrl-O, Enter)하고 끝내세요(Ctrl-X). Caddy를 다시 불러오세요.

```bash
sudo systemctl reload caddy
```

Caddy가 Let's Encrypt에서 TLS 인증서를 자동으로 받아 옵니다(처음에는 30~60초). `https://events.yourchurch.org`로 접속해 보세요.

이제 포트 6120을 인터넷에서 닫을 수 있고, 닫아야 합니다. 같은 서버의 Caddy만 이 포트와 통신하면 되기 때문입니다. 확실한 방법은 Docker가 서버 자신에서만 듣도록 하는 것입니다. `.env`를 다시 열고(`nano .env`) 다음과 같이 설정하세요.

```
FRONTEND_PORT=127.0.0.1:6120
BACKEND_PORT=127.0.0.1:6121
DB_PORT=127.0.0.1:6122
```

저장한 뒤 `docker compose up -d`로 적용하세요(`ufw` 규칙만으로는 이 일을 할 수 없습니다. Docker는 포트를 직접 열어 `ufw`를 우회합니다). 업체 웹 관리 화면의 방화벽을 두 번째 방어선으로 쓰면 좋습니다. 22, 80, 443 포트만 허용하세요.

---

## 이메일 보내기 (선택)

Moimio는 이메일 없이도 작동합니다. 이메일을 설정하면 사람들이 등록할 때 확인 이메일을 받고, 잊어버린 비밀번호를 재설정할 수 있습니다. 켜려면 "SMTP" 발송을 허용하는 이메일 계정 정보가 필요합니다(이메일 업체 도움말에서 그렇게 부릅니다). `.env`를 열고 `SMTP_`로 시작하는 부분을 채우세요.

```
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=events@yourchurch.org
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=events@yourchurch.org
SMTP_FROM_NAME=Your Church Events
```

저장한 뒤 `docker compose up -d`로 적용하세요. 작동하는지 확인하려면 행사의 등록 양식 설정을 열고 **이메일 확인** 아래의 **테스트 이메일 보내기**를 클릭하세요. 테스트 메시지가 내 받은편지함으로 옵니다. 흔히 쓰는 업체의 설정은 [빠른 설치 가이드](quick-guide.ko.md#smtp-참고선택)에 있습니다.

---

## Moimio 업데이트하기

새 버전이 나오면 서버에서:

```bash
cd ~/moimio
./upgrade.sh
```

스크립트가 바뀔 내용을 보여 주고 **Proceed with upgrade? [y/N]** 하고 묻습니다. `y`를 입력하세요. 그러면 스크립트가:

- `.env` 설정 파일의 사본을 저장하고,
- `moimio` 폴더 옆에 데이터베이스 백업(`pgdata-pre-upgrade-<date-and-time>.sql.gz`라는 파일)을 저장하고,
- 새 버전을 내려받아 Moimio를 다시 빌드하고 다시 시작하고,
- 필요할 때 예전 버전으로 돌아가는 정확한 명령을 출력합니다.

`sudo`를 쓰기 때문에 비밀번호를 물을 수 있습니다. 최신 버전 대신 특정 버전으로 옮기려면 버전 이름을 붙이세요. 예: `./upgrade.sh v1.0.6`(버전 이름은 변경 이력에 있습니다). 아무것도 바꾸지 않고 무엇을 할지만 보려면 `./upgrade.sh --dry-run`을 실행하세요.

마지막에 스크립트는 Moimio가 정상이라고 보고할 때까지 최대 90초 기다립니다. "backend did not become healthy"가 출력되면 롤백 안내를 따르기 전에 브라우저에서 Moimio를 열어 보세요. 열리고 로그인할 수 있다면 업데이트가 시작하는 데 시간이 조금 더 필요했을 가능성이 큽니다.

업데이트는 보통 3~5분 걸립니다. Moimio를 다시 빌드하고 시작하는 동안 사이트를 잠시 쓸 수 없습니다. 진행 중인 행사가 있다면 행사 시간이 아닐 때 하세요.

참가자 데이터는 업데이트해도 유지되며, 새 버전에 필요한 데이터베이스 변경은 시작할 때 자동으로 적용됩니다. 새 버전에 만족할 때까지 백업 파일을 보관했다가 그다음에 지우세요.

---

## 백업

가장 간단한 백업은 데이터베이스 덤프입니다. 서버에서:

```bash
cd ~/moimio
docker compose exec -T db pg_dump -U moimio moimio | gzip > ~/moimio-backup-$(date +%F).sql.gz
```

홈 디렉터리에 날짜가 붙은 백업 파일이 만들어집니다. 정기적으로 노트북이나 클라우드 저장소에 복사하세요.

복원하면 데이터베이스의 모든 내용이 백업 내용으로 바뀌므로, 정말 필요할 때만 하세요. 먼저 데이터베이스를 비워야 하며, `dropdb`와 `createdb` 줄이 그 일을 합니다.

```bash
cd ~/moimio
docker compose stop backend
docker compose exec -T db dropdb -U moimio moimio
docker compose exec -T db createdb -U moimio moimio
gunzip -c ~/moimio-backup-2026-04-28.sql.gz | docker compose exec -T db psql -U moimio moimio
docker compose start backend
```

(여러분의 백업 파일 이름을 쓰세요.)

실제 운영 환경이라면 `cron`으로 백업을 자동화하고 파일을 서버 밖으로 보내세요. 그게 어렵다면 기술에 밝은 친구에게 묻거나, GitHub에 "정기 백업" 가이드를 요청하는 이슈를 등록하세요.

**Moimio 안의 백업.** 관리자에게는 왼쪽 메뉴에 **백업** 페이지도 있습니다. 행사마다 ZIP 파일 하나를 다운로드하고, **백업에서 복원** 버튼으로 행사를 새 초안으로 되살립니다. 한 행사를 크게 바꾸기 전이나 다른 Moimio로 행사를 복사할 때 편리합니다. 팀원 계정은 포함되지 않으므로 새 서버에서는 다시 초대해야 합니다.

**모든 것을 새 서버로 옮기거나**, 호스팅 서비스에서 행사를 가져오려면 [직접 운영하는 Moimio로 워크스페이스 옮기기(영문)](../moving-a-workspace.md)를 참고하세요.

---

## 문제 해결

**`docker compose up`이 "permission denied"로 실패해요.**
`docker` 그룹에 속해 있지 않습니다. 로그아웃했다가 다시 로그인하거나(설치 과정에서 사용자를 그룹에 추가하지만 다시 로그인해야 적용됩니다), `sudo docker compose up -d --build`를 쓰세요.

**브라우저에 "사이트에 연결할 수 없음"이 나와요.**
순서대로 세 가지를 확인하세요.
1. 서버가 실제로 켜져 있나요? VPS라면 업체 관리 화면을 확인하세요. 직접 호스팅이라면 컴퓨터가 켜져 있고 연결되어 있어야 합니다.
2. Moimio가 실제로 실행 중인가요? 서버에서 `docker compose ps`. 세 줄(db, backend, frontend) 모두 `Up`이어야 합니다. 아니라면 `docker compose logs <service>`가 이유를 보여 줍니다.
3. 방화벽이 막고 있나요? VPS 업체에는 별도의 방화벽이 있는 경우가 많습니다. 필요한 포트가 열려 있는지 확인하세요.

**페이지는 열리는데 로그인이 안 돼요(초기 설정 화면도 없어요).**
이미 계정이 있습니다. 설정 화면은 계정이 하나도 없을 때만 나옵니다. 로그인 양식을 쓰세요. 비밀번호를 잊었는데 이메일이 설정되어 있지 않다면, 서버에서 두 번째 최고 관리자 계정을 만들고(다른 이메일 주소를 쓰세요) 그 계정으로 로그인해 계속하면 됩니다.

```bash
docker compose exec backend python -m app.cli.create_admin
```

**페이지에 "Cannot reach the server"만 나와요.**
Moimio의 웹사이트 부분은 실행 중이지만 그 뒤의 부분이 응답하지 않습니다. `docker compose ps`를 실행해 `backend` 줄이 `Up`인지 확인하세요. 아니라면 보통 `docker compose logs --tail=50 backend`가 이유를 알려 줍니다.

**백엔드 로그에 `password authentication failed`가 나와요.**
Moimio를 처음 시작한 뒤에 `.env`의 데이터베이스 비밀번호를 바꿨습니다. 데이터베이스는 여전히 원래 비밀번호를 기대합니다. `.env`에 원래 비밀번호를 다시 넣고 `docker compose up -d`를 실행하세요.

**Cloudflare Tunnel이 Moimio에 연결되지 않아요.**
서버에서 `sudo systemctl status cloudflared`로 연결 프로그램이 실행 중인지 확인하고, `sudo journalctl -u cloudflared -f`로 실시간 로그를 보세요(그만 보려면 Ctrl-C). 흔한 원인은 터널이 `localhost:80`을 가리키는데 Moimio는 `localhost:6120`에 있는 경우입니다. 터널의 공개 호스트 이름 설정을 고치세요.

**도메인을 설정한 뒤 HTTPS 오류가 나요(Caddy 경로).**
DNS가 아직 퍼지지 않았을 수 있습니다. 5분 기다렸다가 다시 시도하세요. 또는 Caddy가 아직 인증서를 받지 못했을 수 있습니다. `sudo systemctl status caddy`로 진행 상황을 보세요. 로그는 `journalctl -u caddy`에 있습니다.

**그보다 이상한 문제.**
[버그를 신고하세요](https://github.com/pistio/moimio/issues/new?template=bug_report.md). 다음을 포함해 주세요.
- 하려던 일.
- 실제로 본 것(정확한 오류 메시지).
- `docker compose logs --tail=50 backend`의 출력.
- 붙여 넣기 전에 참가자 데이터는 가려 주세요.

---

## 다음 단계

Moimio 설치를 마쳤습니다. 실제로 행사를 운영하려면 [사용 설명서](../manual/README.ko.md)가 행사 만들기, 등록 설정, 배정 엔진 실행, 체크인, 명단 내보내기를 안내합니다.

개발자의 도움 없이 여기까지 오셨다면, 대부분의 사람들이 "나한테는 너무 어려워"라고 말할 일을 해내신 겁니다. 직접 호스팅하는 소프트웨어의 세계에 오신 것을 환영합니다.
