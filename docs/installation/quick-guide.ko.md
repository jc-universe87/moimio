# 빠른 설치 가이드

터미널, Docker, 간단한 서버 관리에 익숙한 분을 위한 가이드입니다. 그렇지 않다면 [초보자 가이드](beginner.ko.md)가 같은 내용을 더 천천히, 더 자세히 안내합니다.

걸리는 시간: 새 서버에서 관리자로 로그인하기까지 **30~60분**. 대부분은 첫 `docker compose up --build` 시간이며, 이때 여러분의 기기에서 소스 코드로 Moimio 이미지 두 개를 빌드합니다.

---

## 준비 사항

- Linux 호스트(최신 배포판이면 무엇이든. Ubuntu 22.04+, Debian 12+, Fedora, systemd를 쓰는 모든 배포판).
- **Docker Engine 24+**와 **Docker Compose v2**(예전의 독립 실행형 `docker-compose`가 아니라 `docker compose` 하위 명령).
- **Git**(저장소 내려받기용). 또는 소스 tarball을 내려받아 풀어도 됩니다.
- **포트:** `6120`(프런트엔드. `/api`와 `/health`도 백엔드로 프록시하므로 브라우저에는 이 포트 하나만 필요합니다). Compose는 `6121`(백엔드, 디버깅 중 API에 직접 접근용)과 `6122`(PostgreSQL)도 엽니다. 둘 다 외부에 공개할 필요가 없습니다. localhost에만 묶는 방법은 아래 "포트 바꾸기"를 참고하세요.
- `sudo docker compose`를 호출하는 `upgrade.sh`를 위한 `sudo` 권한.
- 작은 교회 규모 설치라면 대략 **RAM 2 GB**와 **디스크 5 GB**.

Docker가 준비되었는지 확인하세요.

```bash
docker --version          # → Docker version 24.0+ ...
docker compose version    # → Docker Compose version v2.x.x
```

`docker compose version`이 실패하면 예전 독립 실행형 Compose가 설치된 것입니다. v2 플러그인을 설치하세요: `apt install docker-compose-plugin`(Ubuntu/Debian), 또는 [Docker 공식 안내](https://docs.docker.com/compose/install/)를 따르세요.

---

## 1. 내려받기와 설정

```bash
git clone https://github.com/jc-universe87/moimio.git
cd moimio
cp .env.example .env
```

`.env`를 열고 최소한 아래 중 처음 두 개는 수정하세요.

| 변수 | 설정할 값 |
|---|---|
| `SECRET_KEY` | **64자 이상**의 무작위 문자열. `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` 또는 `openssl rand -hex 64`로 만드세요. **운영 환경에서 `change-me-...` 자리 표시자를 그대로 두지 마세요.** |
| `POSTGRES_PASSWORD` | 데이터베이스 사용자의 무작위 비밀번호. 같은 방법으로 만드세요. |
| `DATABASE_URL` | 선택 사항. `docker-compose.yml`이 `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`로 백엔드의 `DATABASE_URL`을 만들기 때문에 `.env`의 이 줄은 컨테이너가 쓰지 않습니다. 파일을 일관되게 유지하고 싶다면 비밀번호 부분을 함께 바꿔 두세요. |

`POSTGRES_PASSWORD`는 **처음 시작하기 전에** 설정하세요. Postgres는 `pgdata` 볼륨이 처음 만들어질 때만 이 값을 적용합니다. 나중에 바꾸면 데이터베이스 안에서도 바꿀 때까지 `password authentication failed`가 납니다.

`LOG_LEVEL=INFO`(기본값)는 그대로 두세요. 이유는 "운영 환경 보안 강화"를 참고하세요.

처음부터 이메일을 쓰려면 SMTP 설정도 하세요. 이 가이드 아래쪽의 SMTP 표를 참고하세요. SMTP를 건너뛰어도 괜찮습니다. 앱은 SMTP 없이도 작동합니다(등록 확인 이메일이 발송되지 않을 뿐이며, 관리자가 등록을 직접 확정할 수 있습니다).

### 포트 바꾸기

기본값은 6120(프런트엔드), 6121(백엔드), 6122(Postgres)입니다. 호스트에서 이미 쓰고 있는 포트가 있다면 `.env`에서 바꾸세요.

```
FRONTEND_PORT=7120
BACKEND_PORT=7121
DB_PORT=7122
```

`docker-compose.yml`이 `${FRONTEND_PORT:-6120}` 등으로 이 값을 읽으므로 다른 곳을 고칠 필요가 없습니다. 그러면 `http://localhost:7120`을 열면 됩니다.

이 값은 Compose의 `ports:` 매핑에 그대로 들어가므로 주소를 함께 지정할 수도 있습니다. 다음은 포트를 호스트의 루프백 인터페이스에만 묶습니다.

```
BACKEND_PORT=127.0.0.1:6121
DB_PORT=127.0.0.1:6122
# Only when your reverse proxy or tunnel runs on this same host:
FRONTEND_PORT=127.0.0.1:6120
```

브라우저는 프런트엔드의 `/api` 프록시를 통해 백엔드와 통신하므로 `BACKEND_PORT`를 바꿔도 다른 작업은 필요 없습니다(예전 `.env` 파일에는 `VITE_API_URL`이 남아 있을 수 있는데, 아무 곳에서도 읽지 않으니 지워도 됩니다).

---

## 2. 스택 시작하기

![docker compose up build 실행 중의 터미널 출력](../assets/install-docker-build.png)

```bash
docker compose up -d --build
```

처음 실행하면 이미지를 내려받고 빌드합니다. 인터넷이 괜찮다면 3~5분 정도 걸립니다. 이후 다시 빌드할 때는 더 빠릅니다.

백엔드가 올라오는 것을 지켜보세요.

```bash
docker compose logs -f backend
```

다음 두 줄이 순서대로 나와야 합니다.

```
INFO  [alembic.runtime.migration] Running upgrade ... -> <latest migration>
INFO  Application startup complete.
```

첫 줄은 데이터베이스 스키마가 성공적으로 생성/마이그레이션되었다는 뜻입니다. 둘째 줄은 uvicorn이 API를 제공하고 있다는 뜻입니다. 첫 줄 없이 둘째 줄만 보인다면 마이그레이션이 이미 최신 상태라는 뜻이므로 역시 괜찮습니다. **Ctrl-C를 누르면 로그 보기만 멈추고 컨테이너는 계속 실행됩니다.**

API를 간단히 확인하세요(같은 엔드포인트를 프런트엔드를 통해 `http://localhost:6120/health`로도 열 수 있습니다).

```bash
curl http://localhost:6121/health
# → {"status":"ok","database":"healthy","version":"1.0.6"}
```

### Alembic 마이그레이션에 대하여

Alembic은 SQLAlchemy와 함께 쓰는 데이터베이스 마이그레이션 도구입니다. 스키마 변화를 관리하며, 마이그레이션 파일 하나하나가 데이터베이스를 앞으로(가능하면 뒤로도) 옮기는 방법을 아는 버전별 변경 묶음입니다.

알아 두면 좋은 점 두 가지:

- **마이그레이션은 백엔드 컨테이너가 시작할 때마다 자동으로 실행됩니다.** Dockerfile의 CMD는 `alembic upgrade head && uvicorn ...`입니다. Alembic이 데이터베이스의 현재 리비전을 확인해 더 새로운 마이그레이션을 적용한 뒤 uvicorn에 넘깁니다.
- **마이그레이션은 데이터를 지우지 않습니다.** 각 마이그레이션은 "이 열 추가", "이 테이블 생성", "이 인덱스 이름 변경"처럼 점진적입니다. 데이터베이스를 처음부터 다시 만들지 않습니다. `docker compose down -v`(`-v` 옵션은 `moimio_pgdata`를 포함한 명명된 볼륨을 삭제합니다)만 실행하지 않으면 참가자 데이터, 행사, 배정은 업그레이드해도 보존됩니다.

데이터베이스를 정말 초기화해야 한다면 `docker compose down -v`를 쓰세요(`<project>_pgdata`, 예를 들어 `moimio_pgdata`라는 이름의 `pgdata` 볼륨을 삭제합니다). 실제 데이터가 없는 설치에서만 하세요.

---

## 3. 첫 관리자 만들기

![첫 최고 관리자 계정을 만드는 초기 설정 마법사](../assets/first-time-setup.png)

Moimio에는 기본 관리자 계정이 없습니다. 브라우저에서 `http://localhost:6120`(또는 설정한 포트)을 여세요. 자동으로 **초기 설정 화면**이 나옵니다. Moimio가 사용자가 없음을 감지하고 마법사를 보여 줍니다.

다음을 입력하세요.

- **성명**: 관리 화면에 표시되는 이름.
- **이메일**: 로그인에 사용합니다.
- **비밀번호**와 **비밀번호 확인**: 8자 이상. 비밀번호 관리자를 꼭 사용하세요.

화면에는 언어 선택기와 밝은/어두운 모드 전환 버튼도 있습니다. **최고 관리자 생성**을 클릭하세요. **최고 관리자** 역할로 계정이 만들어지고, 그 계정으로 로그인하는 로그인 페이지로 이동합니다. 사용자가 한 명이라도 생기면 설정 화면은 다시 나타나지 않습니다.

**다른 방법: CLI로 만들기.** 화면 없는 설치나 스크립트로 프로비저닝할 때는 같은 작업을 명령줄에서 할 수 있습니다.

```bash
docker compose exec backend python -m app.cli.create_admin
```

이메일, 성명, 비밀번호를 묻고 최고 관리자를 만듭니다. 직접 설치하는 분께는 화면에서 하는 방법을 기본으로 권장합니다. 하나뿐인 최고 관리자의 비밀번호를 잃어버렸는데 재설정용 SMTP가 없을 때도 CLI로 다시 들어갈 수 있습니다. 다른 이메일로 두 번째 최고 관리자를 만드세요.

---

## 4. 로그인(설정 이후)

방금 만든 계정으로 `http://localhost:6120/login`에서 로그인하세요.

아직 행사가 없으면 **Moimio에 오신 것을 환영합니다** 화면이 나옵니다. **첫 행사 만들기**를 클릭하세요. 행사가 생기면 행사 목록에 **+ 새 행사** 버튼이 있습니다.

최고 관리자라면 사이드바의 **워크스페이스**를 열고 **개인정보 처리방침 URL**도 설정하세요. 공개 등록 양식의 동의 문장 바로 뒤에 링크가 걸립니다. 비워 두면 링크가 나오지 않습니다.

---

## 5. 운영 환경 보안 강화

Moimio를 인터넷에 공개하기 전에:

- 포트 6120 앞에 TLS를 처리하는 리버스 프록시를 두세요. 호스트의 Caddy, Traefik, Cloudflare Tunnel 모두 잘 작동합니다. Nginx + Let's Encrypt는 전통적인 방법입니다.
- 앱 기능이 제대로 작동하는 것도 HTTPS 덕분입니다. 브라우저는 HTTPS나 `localhost`에서만 서비스 워커를 등록하므로, `http://192.168.1.20:6120` 같은 일반 HTTP 내부망 주소로 연 설치본에서는 오프라인 캐시도, "새 버전이 있습니다" 안내도 없고, "캐시 지우고 새로 고침" 버튼이 지울 것도 없으며, 그 이유를 알려 주는 오류도 어디에도 나오지 않습니다.
- 백엔드 포트(6121)와 데이터베이스 포트(6122)는 인터넷에 노출하지 마세요. `.env`에서 localhost에 묶으세요("포트 바꾸기" 참고). 호스트 방화벽 규칙만으로는 부족합니다. Docker가 공개하는 포트는 Docker가 직접 iptables에 열기 때문에 `ufw`/`firewalld` 규칙을 우회합니다.
- [`SECURITY.md`](../../SECURITY.md)(영문)를 읽으세요. "Hardening recommendations for self-hosters" 섹션에서 나머지(강력한 SECRET_KEY, DB 비밀번호 교체, Docker 호스트 패치, SMTP 자격 증명 관리)를 다룹니다.
- 실제 참가자가 있는 설치에서는 `LOG_LEVEL=INFO`를 유지하세요. `LOG_LEVEL=DEBUG`는 요청마다 참가자 이름, 주소, 생년월일을 컨테이너 로그에 기록합니다. 디버깅은 가상의 데이터를 넣은 사본에서 하세요.

---

## 6. 업데이트

git으로 내려받은 저장소의 최상위 폴더에서:

```bash
./upgrade.sh                # latest commit on your current branch
./upgrade.sh v1.0.6         # a specific release tag (see CHANGELOG.md)
./upgrade.sh v1.0.6 --yes   # skip the confirmation prompt
./upgrade.sh --dry-run      # show what would happen, change nothing
```

스크립트는 먼저 점검하고(`.env` 존재, 깨끗한 작업 트리, `db` 컨테이너 실행 중), 적용할 커밋을 보여 주고, `.env`를 `.env.pre-upgrade-<timestamp>.bak`에, 데이터베이스를 `../pgdata-pre-upgrade-<timestamp>.sql.gz`에 백업합니다. 그다음 대상 버전으로 체크아웃하고 `docker compose down`, `build --no-cache`, `up -d`를 실행합니다. 마지막에 정확한 롤백 명령을 출력합니다. 새 버전에 만족할 때까지 백업을 보관하세요. 태그를 체크아웃하면 저장소가 detached HEAD 상태가 되므로, 버전을 한 번 고정했다면 다음 버전도 그냥 실행하지 말고 명시하세요(`./upgrade.sh v1.0.7`).

다시 시작한 뒤 스크립트는 백엔드 컨테이너가 "healthy"를 보고할 때까지 최대 90초 기다립니다. `docker-compose.yml`의 백엔드 헬스체크는 30초의 시작 대기 후 10초마다 `/health`를 호출합니다. 기다림이 "did not become healthy" 경고로 끝나면(예: 오래 걸리는 마이그레이션), 롤백하기 전에 `curl http://localhost:6121/health`와 백엔드 로그를 확인하세요.

직접 하고 싶다면 이렇게 하면 됩니다.

```bash
git pull            # or: git fetch --tags && git checkout v1.0.6
docker compose build --no-cache
docker compose up -d --force-recreate
```

Dockerfile이 바뀌었을 때(새 의존성, 글꼴 설치 등)는 `--no-cache`가 중요합니다. 빼먹으면 새 코드가 옛 이미지 레이어 위에서 실행되어 이해하기 어려운 오류가 날 수 있습니다.

마이그레이션은 백엔드가 시작할 때 자동으로 실행되므로 `alembic upgrade head`를 직접 할 필요가 없습니다. 데이터는 업그레이드해도 보존됩니다(`pgdata` 볼륨은 건드리지 않습니다). 그래도 여느 업그레이드처럼 먼저 백업하세요.

저장소 최상위의 `deploy.sh`는 다른 도구입니다. 패키지로 받은 `../moimio-ce-<tag>.zip`으로 설치본을 교체하며, `git clone`으로 설치하지 않은 경우를 위한 것입니다. 저장소를 clone했다면 `upgrade.sh`를 쓰세요.

### 컨테이너 이미지

이 가이드는 소스 코드로 이미지를 빌드합니다. 각 릴리스는 `ghcr.io/jc-universe87/moimio-backend:<tag>`와 `ghcr.io/jc-universe87/moimio-frontend:<tag>`(예: `v1.0.6`)로도 게시됩니다. 이 이미지를 쓴다면 항상 버전 태그를 고정하세요. `:latest`는 v1.0.6에 멈춰 있어 더 이상 갱신되지 않으며 지원되지 않습니다. `backend/deploy/production.yml`은 호스팅 서비스용 템플릿이지 직접 설치용 compose 파일이 아닙니다. 최상위의 `docker-compose.yml`을 쓰세요.

---

## 7. 백업

가장 간단한 백업은 Postgres `pg_dump`입니다.

```bash
docker compose exec -T db pg_dump -U moimio moimio | gzip > moimio-backup-$(date +%F).sql.gz
```

cron으로 정기 실행하세요. 덤프는 호스트가 아닌 다른 곳에 보관하세요.

복원하려면 빈 데이터베이스에 덤프를 불러오세요(일반 덤프를 데이터가 있는 데이터베이스에 넣으면 기존 테이블과 행 때문에 실패합니다).

```bash
docker compose stop backend
docker compose exec -T db dropdb -U moimio moimio
docker compose exec -T db createdb -U moimio moimio
gunzip -c moimio-backup-2026-10-01.sql.gz | docker compose exec -T db psql -U moimio moimio
docker compose start backend
```

(`POSTGRES_USER` / `POSTGRES_DB`를 바꿨다면 그 값으로 바꾸세요.)

앱에는 행사 단위 백업 기능도 있습니다. 사이드바의 **백업** 페이지에서 행사마다 ZIP 하나(전체, 또는 개인정보 없이 구조만)를 다운로드하고, **백업에서 복원**으로 이 서버나 다른 서버에 새 초안 행사로 되살릴 수 있습니다. 팀원과 그 역할은 백업에 담기지 않으므로 받는 서버에서 팀을 다시 초대하세요. 사용 설명서의 [9장: 데이터 내보내기와 개인정보보호(GDPR)](../manual/09-data-export-gdpr.ko.md)를 참고하세요.

명령줄에서 워크스페이스 전체를 보관하려면: `docker compose exec backend python -m app.cli.export_all --out /tmp/moimio-export.zip`.

워크스페이스 전체, 곧 모든 행사를 한꺼번에 이 서버로 가져오려면 [직접 운영하는 Moimio로 워크스페이스 옮기기(영문)](../moving-a-workspace.md)를 참고하세요.

---

## SMTP 참고(선택)

등록 확인 이메일과 비밀번호 재설정을 쓰려면 `.env`의 SMTP 부분을 채우세요.

```
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=events@yourchurch.org
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=events@yourchurch.org
SMTP_FROM_NAME=Your Church Events
SMTP_TLS=true
SMTP_SSL=false
```

`SMTP_TLS=true`는 STARTTLS(포트 587)입니다. 포트 465의 암시적 TLS를 쓰려면 `SMTP_PORT=465`, `SMTP_SSL=true`, `SMTP_TLS=false`로 설정하세요. 이메일은 `SMTP_HOST`와 `SMTP_USER`가 모두 설정되었을 때만 켜집니다. 이 값들을 바꾼 뒤에는 백엔드를 다시 시작하세요(`docker compose up -d backend`).

흔히 쓰는 업체와 일반적인 설정(업체의 최신 문서로 꼭 확인하세요. 가끔 바뀝니다):

| 업체 | 일반적인 호스트 | 일반적인 포트 | 참고 |
|---|---|---|---|
| Zoho Mail | `smtp.zoho.eu` / `smtp.zoho.com` | 587 | Account → Security에서 앱 비밀번호를 만드세요 |
| Gmail / Google Workspace | `smtp.gmail.com` | 587 | 2단계 인증 + 앱 비밀번호 필요 |
| Brevo(옛 Sendinblue) | `smtp-relay.brevo.com` | 587 | 무료 요금제로 대부분의 작은 교회 발송량을 감당합니다 |
| SMTP2GO | `mail.smtp2go.com` | 587 | 무료 요금제가 있는 종량제 |
| Mailgun | `smtp.mailgun.org` | 587 | 도메인 인증 필요 |

설정하기 전에 **반드시 업체의 최신 SMTP 문서를 확인하세요**. 설정, 포트 번호, 인증 요구 사항은 바뀝니다. 기준은 이 표가 아니라 업체의 안내 페이지입니다.

행사를 만든 뒤 화면에서 테스트하세요. 행사의 등록 양식 설정(준비 단계에서는 **설정 ▸ 등록**, 등록을 연 뒤에는 **더보기 ▸ 등록 설정**)을 열고 **이메일 확인 ▸ 테스트 이메일 보내기**를 누르세요. 테스트 이메일은 로그인 주소로 발송되며, 어떤 `From` 이름, `Reply-To`, SMTP 서버를 썼는지 알려 줍니다. "이메일이 안 왔어요" 문제를 진단할 때 가장 유용합니다.

SMTP를 비워 두면 앱은 발송을 건너뛰고 발송할 때마다 `email_skipped`를 로그에 남깁니다. 개발할 때 유용합니다.

---

## 선택 설정 참고

모두 `.env`에서 읽어 `docker-compose.yml`이 넘겨줍니다. 바꾼 뒤에는 `docker compose up -d`로 다시 시작하세요.

| 변수 | 기본값 | 하는 일 |
|---|---|---|
| `LOG_LEVEL` | `INFO` | `DEBUG`는 모든 데이터베이스 쿼리를 값과 함께, 곧 참가자 데이터까지 기록합니다. |
| `RATE_LIMIT_REGISTRATION` | `60` | 한 주소에서 분당 신청 수. 양식에 추가한 가족 구성원도 하나씩 셉니다. 교인 전체가 한 와이파이로 동시에 등록한다면 올리세요. `0`이면 꺼집니다. 직접 둔 리버스 프록시나 Cloudflare Tunnel 뒤에서는, 그 프록시가 사설 또는 루프백 주소에서 Moimio에 접속하고 `X-Forwarded-For`를 보내는 한 실제 방문자 주소가 쓰입니다. |
| `FEATURE_ALLOCATION` | `true` | `false`면 등록 전용 설치를 위해 배정 엔진을 끕니다. |
| `FEATURE_OUTBOUND_WEBHOOKS` | `true` | `false`면 웹훅 페이지를 숨기고 발송을 끕니다. [웹훅(영문)](../webhooks.md)을 참고하세요. |
| `WEBHOOK_ALLOW_PRIVATE_TARGETS` | `false` | 사설, 루프백, 링크 로컬 주소(`10.x`, `192.168.x`, `localhost`…)의 웹훅 URL은 이 값이 `true`가 아니면 거부됩니다. 수신 측이 내부망에 있을 때만 설정하세요. `.env.example`에는 없으니 직접 줄을 추가하세요. |
| `WEBHOOK_DELIVERY_RETENTION_DAYS` | `30` | 웹훅 발송 기록을 보관하는 기간. |

`.env.example`과 `docker-compose.yml`의 나머지 변수(`FEATURE_CREATE_EVENT_CONFIRMATION`, `EVENT_CHARGE_*`, `BILLING_CARD_LAST4`, `FEATURE_ACCOUNT_PORTAL`, `ACCOUNT_URL`, `FEATURE_DEMO_NOTICE`, `MOIMIO_DEMO_MAIL_URL`, `MOIMIO_TENANT_ID`, `MOIMIO_WEBHOOK_URL`, `MOIMIO_WEBHOOK_SECRET`)는 호스팅 서비스와 데모 워크스페이스용입니다. 일반적인 직접 설치에서는 기본값 그대로 두세요. `APP_URL`은 더 이상 쓰이지 않습니다. 이메일 링크는 요청에서 주소를 가져옵니다.

---

## 문제 해결

**`docker compose up`이 로그 없이 바로 종료돼요.**
실제 오류를 확인하세요: `docker compose ps`, 그다음 `docker compose logs <service>`. 가장 흔한 원인은 포트 충돌입니다. 호스트의 다른 프로그램이 이미 6120, 6121, 6122를 쓰고 있는 경우입니다. 충돌하는 서비스를 멈추거나 포트를 바꾸세요(위의 "포트 바꾸기" 참고).

**백엔드 로그에 `db:5432`로의 `connection refused`가 나와요.**
Postgres가 준비되기 전에 백엔드가 시작되었습니다. 보통은 `depends_on: condition: service_healthy` 설정이 이를 막아 주는데, 이 오류가 보인다면 Docker 버전이 너무 오래되었을 수 있습니다. Docker를 업데이트하거나, 그냥 `docker compose restart backend`를 실행하세요.

**백엔드 로그에 `relation "users" does not exist`가 나와요.**
Alembic 마이그레이션이 실행되지 않았습니다. `docker compose logs backend`에서 그 앞쪽의 Alembic 오류를 확인하세요. 보통 `docker compose down && docker compose up -d --force-recreate`로 해결됩니다.

**페이지에 "Cannot reach the server"가 나오거나 로그인이 네트워크 오류로 실패해요.**
프런트엔드 컨테이너가 페이지를 제공하고 `/api/*`를 백엔드 컨테이너로 프록시합니다. 백엔드가 실행 중인지(`docker compose ps`, 그다음 `docker compose logs backend`), `curl http://localhost:6120/health`가 응답하는지 확인하세요. 직접 리버스 프록시를 앞에 두었다면 `/`만이 아니라 모든 경로를 포트 6120으로 전달하는지 확인하세요.

**백엔드 로그에 `password authentication failed for user "moimio"`가 나와요.**
데이터베이스 볼륨이 처음 만들어진 뒤에 `POSTGRES_PASSWORD`를 바꿨습니다. Postgres는 원래 비밀번호를 유지합니다. `.env`에 예전 비밀번호를 다시 넣거나, 데이터베이스 안에서 비밀번호를 바꾸고(`docker compose exec db psql -U moimio -c "ALTER USER moimio PASSWORD '<new>'"`) 다시 시작하세요.

**그 밖의 문제.**
관련 로그를 붙여 [버그를 신고하세요](https://github.com/jc-universe87/moimio/issues/new?template=bug_report.md)(참가자 데이터는 먼저 가려 주세요).

---

Moimio를 쓸 준비가 되셨나요? 행사 운영 흐름은 [사용 설명서](../manual/README.ko.md)부터 시작하세요.
