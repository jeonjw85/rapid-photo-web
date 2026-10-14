# rapid-photo-web

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-latest-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/r/jeonjw/rapid-photo-web)
[![Docker Pulls](https://img.shields.io/docker/pulls/jeonjw/rapid-photo-web)](https://hub.docker.com/r/jeonjw/rapid-photo-web)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[한국어](README.ko.md)

[Rapid Photo Downloader](https://damonlynch.net/rapid/) in your browser, packaged as a single-app Ubuntu container

One shared GUI session per container, with persistent settings, browser file transfers and automatic app restart

## Run

Requires Docker with Compose. Published image: `linux/arm64`

```sh
cp .env.example .env
mkdir -p data/config data/input data/uploads data/output
```

Set `IMAGE=jeonjw/rapid-photo-web:latest` in `.env`. On Linux/NAS, match `USER_ID` and `GROUP_ID` to the folder owner (`id -u`, `id -g`). Config, uploads and output must be writable by that user

```sh
docker compose up -d --pull always --no-build
```

Open http://localhost:5800, or use your server's address

Run the same command to update to the latest release

## Import photos

| Container path | Default host path | Contents |
| --- | --- | --- |
| `/config` | `./data/config` | Settings, download history and cache |
| `/input` | `./data/input` | Read-only source files |
| `/uploads` | `./data/uploads` | Browser uploads |
| `/output` | `./data/output` | Imported photos and videos |

- Server/NAS: set `INPUT_DIR` in `.env`, then select `/input` under **This Computer** in the app
- SD/USB: mount the device on the Docker host, set `INPUT_DIR` to that path and run `docker compose up -d --force-recreate`
- Browser upload: open the sidebar's file panel, enter `/uploads` and upload files, then select `/uploads` in the app after the transfer finishes

Default destinations: `/output/photos` and `/output/videos`

The file panel can upload, download, rename and delete files in `/uploads` and `/output` only. Uploaded originals stay in place after import

SD/USB support uses host-mounted folders, not direct camera access or automatic hotplug. On Docker Desktop, use a shared host path and recreate the container after changing cards or mounts

## Configuration

See [.env.example](.env.example) for ports, paths, user IDs, timezone and display size. For Korean, use `LANG=ko_KR.UTF-8` and `TZ=Asia/Seoul`

Settings and files survive container recreation when the host folders are kept. For startup errors, check `docker compose logs --tail=100 rapid-photo-web` for the path and required UID/GID

For HTTPS and web login, follow the [base image configuration](https://github.com/jlesage/docker-baseimage-gui#security) and add the variables to `compose.yaml`

## Development

Requires Python 3.9+ and Docker

```sh
docker build --platform linux/arm64 -t rapid-photo-web:test .
python3 tests/smoke.py --image rapid-photo-web:test --platform linux/arm64 --suite all
```

The [Docker workflow](.github/workflows/docker.yml) builds and tests PRs to `main` and pushes to `main`. Pushing a `vMAJOR.MINOR.PATCH` tag publishes the tested image under its version and `latest`

## License

The Dockerfile, scripts and documentation in this repository use the [MIT license](LICENSE)

The [jlesage/baseimage-gui project](https://github.com/jlesage/docker-baseimage-gui/blob/v4.14.0/LICENSE) uses MIT. [Rapid Photo Downloader](https://damonlynch.net/rapid/) by Damon Lynch uses GPL-3.0-or-later. Software bundled in the image retains its own licenses

App source and distribution patches: [Ubuntu source package](https://packages.ubuntu.com/source/noble/rapid-photo-downloader), matching the installed version

This repository's license is included at `/usr/share/doc/rapid-photo-web/LICENSE` in the image; installed package notices are under `/usr/share/doc`
