# rapid-photo-web

[Rapid Photo Downloader](https://damonlynch.net/rapid/)의 리눅스 GUI를 웹 브라우저에서 사용하는 Docker 이미지입니다.

- 접속하면 앱을 최대화해 표시하고, 종료된 앱은 자동 재실행합니다.
- 바탕화면 앱 메뉴와 웹 터미널 없이 사진 작업에 집중합니다.
- 서버/NAS 폴더, 호스트에 마운트한 SD카드·USB, 브라우저 업로드를 지원합니다.
- 설정과 사진을 호스트에 저장하며 `linux/amd64`, `linux/arm64`로 빌드할 수 있습니다.
- 컨테이너 하나가 하나의 앱 세션을 제공합니다. 동시에 접속한 브라우저는 같은 화면을 공유합니다.

## 빠른 시작

Docker와 Docker Compose 플러그인이 필요합니다. 프로젝트 폴더에서 실행합니다.

```sh
cp .env.example .env
mkdir -p data/config data/input data/uploads data/output
```

Linux/NAS에서는 `.env`의 `USER_ID`, `GROUP_ID`를 사진 저장 폴더 소유자의 ID에 맞춥니다. 현재 계정의 ID는 `id -u`, `id -g`로 확인할 수 있습니다. 설정·업로드·출력 폴더는 이 계정으로 파일을 생성할 수 있어야 합니다.

```sh
docker compose up -d --build
```

브라우저에서 **http://localhost:5800** 또는 `http://서버주소:5800`에 접속합니다. 서버 포트는 `.env`의 `WEB_PORT`로 바꿀 수 있습니다.

이미 게시된 이미지를 사용하려면 `.env`의 `IMAGE`를 `계정명/rapid-photo-web:버전`으로 지정합니다.

```sh
docker compose pull
docker compose up -d --no-build
```

## 사진 가져오기

| 컨테이너 경로 | 기본 호스트 경로 | 용도 |
| --- | --- | --- |
| `/config` | `./data/config` | 앱 설정, 다운로드 기록, 캐시 |
| `/input` | `./data/input` | 읽기 전용 원본 |
| `/uploads` | `./data/uploads` | 브라우저에서 업로드한 원본 |
| `/output` | `./data/output` | 가져온 사진과 영상 |

### 서버·NAS 폴더

`.env`의 `INPUT_DIR`을 원본 폴더로, `OUTPUT_DIR`을 저장할 폴더로 설정합니다. 앱의 **This Computer**에서 `/input` 또는 그 하위 폴더를 선택하고 사진을 가져옵니다.

최초 사진 대상은 `/output/photos`, 영상 대상은 `/output/videos`입니다. 앱에서 이름·하위 폴더 규칙과 대상 폴더를 바꿀 수 있습니다. 기존 설정은 컨테이너 재시작·재생성 시 덮어쓰지 않습니다.

### SD카드·USB 저장장치

1. Docker 호스트에서 저장장치를 마운트합니다.
2. `.env`의 `INPUT_DIR`을 마운트 경로로 지정합니다. 예: `/media/사용자/CAMERA`.
3. `docker compose up -d --force-recreate`로 연결을 반영합니다.
4. 앱의 **This Computer → /input**에서 가져옵니다.

Linux/NAS에서는 호스트의 마운트 경로를 사용합니다. Windows/macOS의 Docker Desktop 계열에서는 Docker에 공유된 폴더 경로를 사용합니다. 카드를 교체하거나 마운트 위치가 바뀌면 컨테이너를 재생성합니다.

장치는 앱에서 **폴더 소스**로 사용합니다. PTP 카메라 직접 연결, 브라우저 PC의 USB 직접 전달, 자동 핫플러그 처리는 이 이미지의 지원 범위에 포함되지 않습니다.

### 브라우저 PC의 파일

1. 웹 화면의 사이드바에서 **폴더 아이콘**을 눌러 파일 전송 패널을 엽니다.
2. **uploads** 폴더를 열고 경로가 `/uploads`로 바뀐 것을 확인합니다.
3. 업로드 버튼으로 파일을 선택하고 전송 완료를 기다립니다.
4. 앱의 **This Computer**에서 `/uploads`를 선택하거나 다시 읽어 사진을 가져옵니다.
5. 파일 전송 패널의 **output**에서 결과 파일을 다운로드할 수도 있습니다.

패널은 `/uploads`와 `/output`에만 접근합니다. 이름 변경·삭제 기능도 제공하므로 업로드 원본과 결과 파일을 관리할 수 있습니다. 업로드 원본을 자동 삭제하지 않습니다.

## 설정

`.env.example`을 복사해 필요한 값만 변경합니다.

| 설정 | 기본값 | 의미 |
| --- | --- | --- |
| `IMAGE` | `rapid-photo-web:local` | 실행할 이미지 이름 |
| `IMAGE_VERSION` | `0.1.0` | 로컬 빌드의 컨테이너 버전 표시 |
| `WEB_PORT` | `5800` | 호스트 웹 포트 |
| `USER_ID`, `GROUP_ID` | `1000`, `1000` | 앱 실행 사용자·그룹 |
| `UMASK` | `0022` | 새 파일의 권한 마스크 |
| `TZ` | `Etc/UTC` | 시간대, 예: `Asia/Seoul` |
| `LANG` | `en_US.UTF-8` | 준비된 로케일: `en_US.UTF-8`, `ko_KR.UTF-8` |
| `DISPLAY_WIDTH`, `DISPLAY_HEIGHT` | `1920`, `1080` | 가상 화면 크기 |
| `CONFIG_DIR`, `INPUT_DIR`, `UPLOADS_DIR`, `OUTPUT_DIR` | 위 표 참조 | 호스트 저장 경로 |

한글 파일명을 위한 CJK 글꼴을 포함합니다. 한국어 실행은 `LANG=ko_KR.UTF-8`, 한국 시간은 `TZ=Asia/Seoul`로 설정합니다. 앱 언어를 앱 설정에서 별도로 지정한 경우 그 설정이 우선할 수 있습니다.

웹 화면의 설정에서 **Local Scaling** 또는 **Remote Resizing**을 선택해 화면을 맞출 수 있습니다. 첫 실행의 Tip of the Day 창은 앱의 기본 안내 창입니다.

### 인증·HTTPS

베이스 이미지의 선택형 웹 인증·HTTPS 설정을 사용할 수 있습니다. 필요한 변수는 `compose.yaml`의 `environment`에 추가합니다.

- `SECURE_CONNECTION=1`: HTTPS 활성화. 기본 자체 서명 인증서 또는 `/config/certs`의 인증서를 사용합니다.
- `WEB_AUTHENTICATION=1`: 웹 로그인 활성화.
- `WEB_AUTHENTICATION_USERNAME`, `WEB_AUTHENTICATION_PASSWORD`: 로그인 정보. 실제 값은 로컬 환경/시크릿으로 전달합니다.

자세한 인증서·시크릿·리버스 프록시 설정은 [베이스 이미지 문서](https://github.com/jlesage/docker-baseimage-gui#security)를 참고하세요. HTTPS를 켜면 접속 주소도 `https://`로 바꿉니다.

## 상태 확인과 데이터 유지

```sh
docker compose ps
docker compose logs --tail=100 rapid-photo-web
docker compose restart
```

헬스체크는 웹 응답과 앱 프로세스를 함께 확인합니다. 쓰기 권한이 맞지 않으면 시작 로그에 해당 경로와 필요한 UID/GID가 표시됩니다. 호스트 폴더 권한 또는 `.env`의 사용자 ID를 수정한 뒤 재생성합니다. 사진 저장소 전체의 소유권을 자동으로 바꾸지 않습니다.

앱 설정과 다운로드 기록은 `/config` 아래에 저장됩니다. `docker compose down` 후 다시 실행해도 호스트의 데이터 폴더는 유지됩니다. 데이터 폴더를 보관하면 이미지 교체 후에도 같은 설정과 사진을 사용할 수 있습니다.

## Docker Hub에 게시

```sh
docker login
export DOCKERHUB_USERNAME=your-dockerhub-id
export VERSION=0.1.0

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg IMAGE_VERSION="$VERSION" \
  -t "$DOCKERHUB_USERNAME/rapid-photo-web:$VERSION" \
  -t "$DOCKERHUB_USERNAME/rapid-photo-web:latest" \
  --push .
```

멀티아키텍처 빌더가 없는 환경에서는 먼저 `docker buildx create --name rapid-photo-web-builder --driver docker-container --use --bootstrap`으로 빌더를 준비합니다. 교차 아키텍처 빌드는 해당 아키텍처를 실행할 수 있는 빌더/에뮬레이션 환경이 필요합니다.

태그 `0.1.0`은 **컨테이너 버전**입니다. Rapid Photo Downloader는 Ubuntu 24.04 배포판 패키지를 사용하며, 실제 앱 버전은 웹 사이드바와 시작 로그에 표시됩니다. GUI 베이스는 `ubuntu-24.04-v4.14.0`의 멀티아키텍처 digest로 고정되어 있습니다.

## 개발 검증

Python 3.9 이상과 Docker가 필요합니다. 검증은 별도의 임시 컨테이너·데이터를 사용하고 종료 시 정리합니다.

```sh
docker build --platform linux/arm64 -t rapid-photo-web:test .
python3 tests/smoke.py --image rapid-photo-web:test --platform linux/arm64 --suite all

docker buildx build --platform linux/amd64 --load -t rapid-photo-web:test-amd64 .
python3 tests/smoke.py --image rapid-photo-web:test-amd64 --platform linux/amd64 --suite all

docker compose config
sh -n rootfs/startapp.sh rootfs/etc/cont-init.d/90-rapid-photo-web.sh
```

스모크 검증은 실제 앱의 시작, 사용자 권한, 설정 유지, 원본 보존, 한글·공백 파일명 가져오기, 카드 폴더 마운트, 앱 재실행을 확인합니다. 웹 업로드·다운로드 및 실제 물리 장치 연결은 별도 통합 확인 대상입니다.

이 개발 환경의 AMD64 검증은 OrbStack의 x86_64 에뮬레이션에서 실행했습니다. 시작·권한·설정 검증은 통과했지만, 앱의 사진 스캔 프로세스 생성이 에뮬레이터에서 멈춥니다. 같은 이미지는 네이티브 ARM64에서 사진 가져오기까지 통과했습니다. 따라서 AMD64 사진 가져오기는 실제 x86_64 Linux에서 별도로 확인해야 하며, 현재 에뮬레이션 실패를 네이티브 AMD64 결함으로 단정하지 않습니다.

## 기반 프로젝트

- [Rapid Photo Downloader](https://damonlynch.net/rapid/) — Damon Lynch의 사진·영상 가져오기 앱, GPL-3.0-or-later.
- [jlesage/docker-baseimage-gui](https://github.com/jlesage/docker-baseimage-gui) — noVNC/TigerVNC/Openbox GUI 컨테이너 베이스.
- [Ubuntu 배포판 패키지·소스](https://packages.ubuntu.com/noble/rapid-photo-downloader).

이 프로젝트는 앱을 컨테이너로 패키징하는 독립 프로젝트입니다. 설치된 패키지의 라이선스·저작권 문서는 이미지의 `/usr/share/doc`에 포함됩니다.
