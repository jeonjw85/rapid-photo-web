# rapid-photo-web

[English](README.md)

[Rapid Photo Downloader](https://damonlynch.net/rapid/)를 브라우저에서 쓰기 위한 Ubuntu 기반 단일 앱 컨테이너

컨테이너당 GUI 세션 하나를 공유하며 설정과 사진은 호스트에 저장, 앱 종료 시 자동 재실행

## 실행

Docker와 Compose 필요

```sh
cp .env.example .env
mkdir -p data/config data/input data/uploads data/output
```

Linux/NAS에서는 `.env`의 `USER_ID`, `GROUP_ID`를 폴더 소유자에 맞춰 설정 (`id -u`, `id -g`로 현재 계정 ID 확인)

설정, 업로드, 출력 폴더는 해당 계정의 쓰기 권한 필요

```sh
docker compose up -d --build
```

접속 주소는 http://localhost:5800 또는 `http://서버주소:5800`

게시된 이미지 사용 시 `.env`에 `IMAGE=계정명/rapid-photo-web:0.1.0` 지정 후 `docker compose pull`, `docker compose up -d --no-build` 실행

## 사진 가져오기

| 컨테이너 경로 | 기본 호스트 경로 | 용도 |
| --- | --- | --- |
| `/config` | `./data/config` | 설정, 다운로드 기록, 캐시 |
| `/input` | `./data/input` | 읽기 전용 원본 |
| `/uploads` | `./data/uploads` | 브라우저 업로드 원본 |
| `/output` | `./data/output` | 가져온 사진과 영상 |

- 서버/NAS: `.env`의 `INPUT_DIR` 지정 후 앱의 **This Computer**에서 `/input` 선택
- SD/USB: 호스트에 장치를 마운트하고 `INPUT_DIR` 지정 후 `docker compose up -d --force-recreate` 실행
- 브라우저 업로드: 사이드바 파일 패널에서 `/uploads`를 연 뒤 파일 업로드, 전송 완료 후 앱에서 `/uploads` 선택

기본 저장 위치는 사진 `/output/photos`, 영상 `/output/videos`

파일 패널은 `/uploads`, `/output`의 업로드, 다운로드, 이름 변경, 삭제 지원

가져오기 후에도 업로드 원본 유지

SD/USB는 호스트에 마운트된 폴더로 연결하며 카메라 직접 연결과 자동 핫플러그는 미지원

Docker Desktop에서는 공유된 호스트 경로 사용, 카드 교체나 마운트 변경 후 컨테이너 재생성

## 설정

포트, 경로, 사용자 ID, 시간대, 화면 크기는 [.env.example](.env.example) 참고

한국어는 `LANG=ko_KR.UTF-8`, 한국 시간은 `TZ=Asia/Seoul`로 설정

호스트 폴더를 보관하면 컨테이너 재생성 후에도 설정과 사진 유지

시작 오류는 `docker compose logs --tail=100 rapid-photo-web`에서 경로와 UID/GID 확인

HTTPS와 웹 로그인은 [베이스 이미지 설정](https://github.com/jlesage/docker-baseimage-gui#security)을 참고해 `compose.yaml`에 환경변수 추가

## Docker Hub 게시

ARM64 사진 가져오기 검증 완료

AMD64는 빌드 가능하나 OrbStack 에뮬레이션에서 가져오기 중 멈춤 발생, 실제 x86_64 환경의 사진 가져오기는 추가 검증 대상

```sh
docker login
export DOCKERHUB_USERNAME=your-dockerhub-id
export VERSION=0.1.0

docker buildx build \
  --platform linux/arm64 \
  --build-arg IMAGE_VERSION="$VERSION" \
  -t "$DOCKERHUB_USERNAME/rapid-photo-web:$VERSION" \
  -t "$DOCKERHUB_USERNAME/rapid-photo-web:latest" \
  --push .
```

실제 AMD64 검증 후 [멀티플랫폼 빌더](https://docs.docker.com/build/building/multi-platform/)에서 `--platform linux/amd64,linux/arm64`로 두 아키텍처 게시 가능

`VERSION`은 앱 버전과 별개인 컨테이너 버전

## 테스트

Python 3.9 이상과 Docker 필요

```sh
docker build --platform linux/arm64 -t rapid-photo-web:test .
python3 tests/smoke.py --image rapid-photo-web:test --platform linux/arm64 --suite all
```

## 라이선스

이 저장소의 Dockerfile, 스크립트, 문서에 [MIT 라이선스](LICENSE) 적용

[jlesage/baseimage-gui 프로젝트](https://github.com/jlesage/docker-baseimage-gui/blob/v4.14.0/LICENSE)는 MIT, Damon Lynch의 [Rapid Photo Downloader](https://damonlynch.net/rapid/)는 GPL-3.0-or-later 적용

이미지에 포함된 소프트웨어는 각자의 기존 라이선스 유지

앱 소스와 배포판 패치는 [Ubuntu 소스 패키지](https://packages.ubuntu.com/source/noble/rapid-photo-downloader)에서 설치된 버전 기준 확인

이 저장소의 라이선스 사본은 이미지 내부 `/usr/share/doc/rapid-photo-web/LICENSE`, 설치된 패키지별 고지는 `/usr/share/doc`에 포함
