#!/bin/sh
# Run after the base's 85-take-config-ownership.sh.
set -eu

as_app() {
    /usr/bin/setpriv --reuid=app --regid=app --init-groups "$@"
}

for path in /config /uploads /output; do
    if [ ! -d "${path}" ]; then
        mkdir -p "${path}"
        chown "${USER_ID}:${GROUP_ID}" "${path}"
    fi
    if ! as_app /bin/sh -c 'probe=$(mktemp "$1/.rapid-photo-web-write.XXXXXX") && rm "$probe"' sh "${path}"; then
        printf 'rapid-photo-web: %s must be writable by UID %s / GID %s.\n' \
            "${path}" "${USER_ID}" "${GROUP_ID}" >&2
        exit 1
    fi
done

# First-run settings use these destinations. Saved settings may also still
# point at them, so prepare missing directories. Never replace an existing
# file that happens to use one of these names.
for path in /output/photos /output/videos; do
    if [ ! -e "${path}" ]; then
        as_app mkdir -p "${path}"
    fi
done
mkdir -p /run/dbus
/usr/bin/dbus-uuidgen --ensure=/etc/machine-id
