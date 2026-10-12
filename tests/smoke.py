#!/usr/bin/env python3
"""Exercise a built image using real Docker containers and temporary data."""

import argparse
import configparser
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
import urllib.request
import uuid


SETTINGS = Path("xdg/config/Rapid Photo Downloader/Rapid Photo Downloader.conf")
HEALTHCHECK = "/usr/local/bin/rapid-photo-web-healthcheck.py"


def docker(*args, check=True):
    return subprocess.run(
        ["docker", *map(str, args)], text=True, capture_output=True, check=check,
        timeout=180,
    )


class Container:
    def __init__(self, image, platform, *, readonly_output=False, uid=1000, bind_config=True):
        self.image = image
        self.platform = platform
        self.uid = uid
        self.readonly_output = readonly_output
        self.bind_config = bind_config
        self.temp = tempfile.TemporaryDirectory(prefix="rapid-photo-web-test-")
        self.root = Path(self.temp.name)
        self.name = "rapid-photo-web-test-" + uuid.uuid4().hex[:12]
        self.extra_mounts = []
        for name in ("config", "input", "uploads", "output"):
            (self.root / name).mkdir(mode=0o777)
            (self.root / name).chmod(0o777)

    def start(self):
        args = [
            "run", "-d", "--pull=never", "--name", self.name,
            "--platform", self.platform, "--shm-size=512m",
            "-p", "127.0.0.1::5800", "-e", f"USER_ID={self.uid}",
            "-e", f"GROUP_ID={self.uid}",
        ]
        for name in ("config", "input", "uploads", "output"):
            if name == "config" and not self.bind_config:
                continue
            mode = ":ro" if name == "input" or (
                name == "output" and self.readonly_output
            ) else ""
            args.extend(["-v", f"{self.root / name}:/{name}{mode}"])
        for source, destination in self.extra_mounts:
            args.extend(["-v", f"{source}:{destination}:ro"])
        result = docker(*args, self.image, check=False)
        if result.returncode:
            raise AssertionError(f"Container could not start: {result.stderr}")

    def state(self):
        return json.loads(docker("inspect", self.name).stdout)[0]["State"]

    def wait_healthy(self):
        deadline = time.monotonic() + 150
        while time.monotonic() < deadline:
            state = self.state()
            if not state["Running"]:
                break
            if state.get("Health", {}).get("Status") == "healthy":
                return
            time.sleep(1)
        raise AssertionError("Container did not become healthy:\n" + self.logs())

    def logs(self):
        result = docker("logs", self.name, check=False)
        return result.stdout + result.stderr

    def exec(self, *args, check=True):
        return docker("exec", self.name, *args, check=check)

    def settings(self):
        prefs = configparser.ConfigParser(interpolation=None, strict=False)
        prefs.read(self.root / "config" / SETTINGS)
        return prefs

    def seed_settings(self, text):
        path = self.root / "config" / SETTINGS
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def recreate(self):
        docker("stop", "-t", "15", self.name)
        docker("rm", "-v", self.name)
        self.start()
        self.wait_healthy()

    def close(self):
        docker("rm", "-fv", self.name, check=False)
        # The image creates app-owned files; remove only this test's directory.
        docker(
            "run", "--rm", "--pull=never", "--platform", self.platform,
            "--entrypoint", "/bin/sh", "-v", f"{self.root}:/test-data",
            self.image, "-c", "chmod -R a+rwX /test-data", check=False,
        )
        self.temp.cleanup()


class ImageTests(unittest.TestCase):
    image = ""
    platform = ""

    def container(self, **kwargs):
        instance = Container(self.image, self.platform, **kwargs)
        self.addCleanup(instance.close)
        return instance


class RuntimeTests(ImageTests):
    def test_fresh_start(self):
        """A missing runtime dependency or incorrect default breaks first launch."""
        c = self.container(uid=1234)
        (c.root / "config").chmod(0o755)
        c.start()
        c.wait_healthy()
        pid = c.exec("cat", "/tmp/rapid-photo-web.pid").stdout.strip()
        status = c.exec("cat", f"/proc/{pid}/status").stdout
        self.assertIn("Uid:\t1234\t1234\t1234\t1234", status)
        prefs = c.settings()
        self.assertEqual(prefs["Device"]["this_computer_path"], "/input")
        self.assertEqual(prefs["Rename"]["photo_download_folder"], "/output/photos")
        self.assertEqual(prefs["Rename"]["video_download_folder"], "/output/videos")
        port = docker("port", c.name, "5800").stdout.strip().rsplit(":", 1)[1]
        with urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=10) as response:
            self.assertEqual(response.status, 200)

    def test_saved_settings_survive_recreate(self):
        """Starting the image must not reset an existing user's destination."""
        c = self.container()
        (c.root / "output" / "custom photos").mkdir(mode=0o777)
        c.seed_settings(
            "[Device]\ndevice_autodetection=false\nthis_computer_source=true\n"
            "this_computer_path=/input\n[Rename]\n"
            "photo_download_folder=/output/custom photos\n"
            "video_download_folder=/output\n"
        )
        c.start()
        c.wait_healthy()
        c.recreate()
        self.assertEqual(
            c.settings()["Rename"]["photo_download_folder"], "/output/custom photos"
        )

    def test_default_config_volume(self):
        """The base must prepare a fresh config volume before access is checked."""
        c = self.container(bind_config=False)
        c.start()
        c.wait_healthy()

    def test_custom_settings_ignore_unused_defaults(self):
        """Unused default names must not block a saved custom destination."""
        c = self.container()
        for kind in ("photos", "videos"):
            (c.root / "output" / kind).write_text("Existing unrelated file")
            (c.root / "output" / ("custom " + kind)).mkdir(mode=0o777)
        c.seed_settings(
            "[Device]\ndevice_autodetection=false\nthis_computer_source=true\n"
            "this_computer_path=/input\n[Rename]\n"
            "photo_download_folder=/output/custom photos\n"
            "video_download_folder=/output/custom videos\n"
        )
        c.start()
        c.wait_healthy()
        self.assertEqual(
            c.settings()["Rename"]["photo_download_folder"], "/output/custom photos"
        )
        for kind in ("photos", "videos"):
            self.assertEqual(
                (c.root / "output" / kind).read_text(), "Existing unrelated file"
            )

    def test_saved_default_destinations_are_created(self):
        """Saved default destinations must exist before the app validates them."""
        c = self.container()
        c.seed_settings(
            "[Device]\ndevice_autodetection=false\nthis_computer_source=true\n"
            "this_computer_path=/input\n[Rename]\n"
            "photo_download_folder=/output/photos\n"
            "video_download_folder=/output/videos\n"
        )
        c.start()
        c.wait_healthy()
        self.assertEqual(
            c.exec(
                "su", "app", "-s", "/bin/sh", "-c",
                "touch /output/photos/.probe /output/videos/.probe",
            ).returncode,
            0,
        )

    def test_unwritable_output(self):
        """Do not report a usable app when the destination cannot accept files."""
        c = self.container(readonly_output=True)
        c.start()
        deadline = time.monotonic() + 60
        while c.state()["Running"] and time.monotonic() < deadline:
            time.sleep(1)
        self.assertFalse(c.state()["Running"], c.logs())
        self.assertNotEqual(c.state()["ExitCode"], 0, c.logs())
        self.assertIn("/output", c.logs())
        self.assertIn("1000", c.logs())

    def test_existing_ownership_preserved(self):
        """Booting must not recursively take ownership of the photo library."""
        c = self.container()
        sentinel = c.root / "output" / "existing.txt"
        sentinel.write_text("Existing photo library ownership")
        before = (sentinel.stat().st_uid, sentinel.stat().st_gid)
        c.start()
        c.wait_healthy()
        self.assertEqual((sentinel.stat().st_uid, sentinel.stat().st_gid), before)

    def test_app_restart(self):
        """A closed GUI must be relaunched by the container supervisor."""
        c = self.container()
        c.start()
        c.wait_healthy()
        old_pid = c.exec("cat", "/tmp/rapid-photo-web.pid").stdout.strip()
        c.exec("kill", "-STOP", old_pid)
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline and c.exec(HEALTHCHECK, check=False).returncode == 0:
            time.sleep(1)
        self.assertNotEqual(c.exec(HEALTHCHECK, check=False).returncode, 0, c.logs())
        port = docker("port", c.name, "5800").stdout.strip().rsplit(":", 1)[1]
        with urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=10) as response:
            self.assertEqual(response.status, 200)
        c.exec("kill", "-CONT", old_pid)
        c.exec("kill", "-TERM", old_pid)
        deadline = time.monotonic() + 60
        new_pid = old_pid
        while time.monotonic() < deadline:
            new_pid = c.exec("cat", "/tmp/rapid-photo-web.pid", check=False).stdout.strip()
            if new_pid and new_pid != old_pid and c.exec(HEALTHCHECK, check=False).returncode == 0:
                break
            time.sleep(1)
        self.assertNotEqual(new_pid, old_pid, c.logs())
        self.assertEqual(c.exec(HEALTHCHECK, check=False).returncode, 0, c.logs())


class PhotoTests(ImageTests):
    def import_photo(self, source_kind):
        c = self.container()
        if source_kind == "card":
            source = c.root / "card storage"
            source.mkdir()
            (c.root / "input" / "card").mkdir()
            app_source = "/input/card"
            c.extra_mounts.append((source, app_source))
        else:
            source = c.root / source_kind
            app_source = "/" + source_kind
        filename = "테스트 photo.jpg"
        docker(
            "run", "--rm", "--pull=never", "--platform", self.platform,
            "--entrypoint", "/usr/bin/python3", "-v", f"{source}:/fixtures",
            self.image, "-c",
            "from PyQt5.QtGui import QImage; import subprocess; "
            "image=QImage(64,64,QImage.Format_RGB32); image.fill(0xff2288aa); "
            f"assert image.save('/fixtures/{filename}'); "
            "subprocess.run(['exiftool','-overwrite_original',"
            "'-DateTimeOriginal=2024:01:02 03:04:05',"
            f"'/fixtures/{filename}'],check=True)",
        )
        original = source / filename
        expected = hashlib.sha256(original.read_bytes()).digest()
        c.seed_settings(
            "[Device]\ndevice_autodetection=false\nthis_computer_source=true\n"
            f"this_computer_path={app_source}\n"
            "[Rename]\nphoto_download_folder=/output/photos\n"
            "video_download_folder=/output/videos\n"
            "[Automation]\nauto_download_at_startup=true\nmove=false\n"
            "[Display]\ndid_you_know_on_startup=false\n"
        )
        c.start()
        c.wait_healthy()
        deadline = time.monotonic() + 60
        matches = []
        while time.monotonic() < deadline:
            matches = list((c.root / "output").rglob("*.jpg"))
            if len(matches) == 1 and hashlib.sha256(matches[0].read_bytes()).digest() == expected:
                break
            time.sleep(1)
        self.assertEqual(len(matches), 1, c.logs())
        self.assertEqual(hashlib.sha256(matches[0].read_bytes()).digest(), expected)
        self.assertTrue(original.exists())
        self.assertEqual(hashlib.sha256(original.read_bytes()).digest(), expected)
        if source_kind == "input":
            c.recreate()
            self.assertEqual(hashlib.sha256(matches[0].read_bytes()).digest(), expected)

    def test_folder_import(self):
        """The actual app copies a read-only source with Unicode/spaces intact."""
        self.import_photo("input")

    def test_card_folder_import(self):
        """A separately mounted card folder is a usable source."""
        self.import_photo("card")

    def test_uploaded_folder_import(self):
        """Files in the writable upload inbox can be imported like local folders."""
        self.import_photo("uploads")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--platform", required=True, choices=("linux/arm64", "linux/amd64"))
    parser.add_argument("--suite", choices=("runtime", "photos", "all"), default="all")
    args = parser.parse_args()
    if docker("info", check=False).returncode:
        parser.exit(2, "Docker Engine must be running.\n")
    if docker("image", "inspect", args.image, check=False).returncode:
        parser.exit(1, f"FAIL: required image {args.image!r} has not been built.\n")
    ImageTests.image, ImageTests.platform = args.image, args.platform
    suite = unittest.TestSuite()
    for name, case in (("runtime", RuntimeTests), ("photos", PhotoTests)):
        if args.suite in (name, "all"):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
