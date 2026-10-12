#!/bin/sh
set -eu

settings_dir="${XDG_CONFIG_HOME}/Rapid Photo Downloader"
settings_file="${settings_dir}/Rapid Photo Downloader.conf"
mkdir -p "${settings_dir}"
if [ ! -e "${settings_file}" ]; then
    cp /defaults/rapid-photo-downloader.conf "${settings_file}"
fi

printf '%s\n' "$$" > /tmp/rapid-photo-web.pid
exec /usr/bin/rapid-photo-downloader "$@"
