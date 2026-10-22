from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "backup-to-cos.sh"


class BackupToCosTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.backups = self.root / "backups"
        self.remote = self.root / "remote"
        self.remote.mkdir()
        self.media = self.root / "media"
        self.project = self.root / "project"
        self.project.mkdir()
        self.media.mkdir()
        (self.media / "image.jpg").write_bytes(b"fake-image")
        (self.root / "rclone.conf").write_text("test config\n", encoding="utf-8")
        self.events = self.root / "events.log"
        self.failures = self.root / "failures"
        self.failures.mkdir()
        self._write_executable(
            "flock",
            """#!/usr/bin/env bash
exit 0
""",
        )
        self._write_executable(
            "docker",
            """#!/usr/bin/env bash
set -Eeuo pipefail
joined="$*"
if [[ "$joined" == *" stop --timeout "* ]]; then
  printf 'STOP\\n' >> "$MOCK_EVENTS"
  exit 0
fi
if [[ "$joined" == *" exec -T db "* ]]; then
  printf 'DUMP\\n' >> "$MOCK_EVENTS"
  printf 'fake-postgres-dump'
  exit 0
fi
if [[ "$joined" == *" run --rm "* ]]; then
  printf 'MEDIA\\n' >> "$MOCK_EVENTS"
  if [[ -f "$MOCK_FAILURES/media" ]]; then exit 1; fi
  tar -czf - -C "$MOCK_MEDIA" .
  exit 0
fi
if [[ "$joined" == *" up -d "* ]]; then
  printf 'START\\n' >> "$MOCK_EVENTS"
  if [[ -f "$MOCK_FAILURES/start" ]]; then
    rm -f "$MOCK_FAILURES/start"
    exit 1
  fi
  exit 0
fi
printf 'unexpected docker call: %s\\n' "$joined" >&2
exit 99
""",
        )
        self._write_executable(
            "rclone",
            """#!/usr/bin/env bash
set -Eeuo pipefail
while [[ "${1:-}" == --config ]]; do shift 2; done
command_name="${1:?missing rclone command}"
shift
case "$command_name" in
  copyto)
    source="$1"; target="$2"
    printf 'UPLOAD\\n' >> "$MOCK_EVENTS"
    if [[ -f "$MOCK_FAILURES/upload" ]]; then exit 1; fi
    cp "$source" "$MOCK_REMOTE/${target##*/}"
    ;;
  check)
    shift
    [[ "${1:-}" == --download ]] && shift
    source="$1"; target="$2"
    printf 'CHECK\\n' >> "$MOCK_EVENTS"
    if [[ -f "$MOCK_FAILURES/check" ]]; then exit 1; fi
    cmp "$source" "$MOCK_REMOTE/${target##*/}"
    ;;
  lsf)
    for file in "$MOCK_REMOTE"/*; do
      [[ -f "$file" ]] || continue
      [[ "$(basename "$file")" =~ ^eiheizone-[0-9]{8}_[0-9]{6}\\.tar\\.gz$ ]] || continue
      modified="$(date -u -d "@$(stat -c %Y "$file")" '+%Y-%m-%d %H:%M:%S')"
      printf '%s|%s\\n' "$modified" "$(basename "$file")"
    done
    ;;
  deletefile)
    printf 'DELETE:%s\\n' "${1##*/}" >> "$MOCK_EVENTS"
    rm -f "$MOCK_REMOTE/${1##*/}"
    ;;
  *) printf 'unexpected rclone call: %s\\n' "$command_name" >&2; exit 98 ;;
esac
""",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_executable(self, name: str, content: str) -> None:
        path = self.bin / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    @staticmethod
    def _bash_path(path: Path) -> str:
        if os.name != "nt":
            return str(path)
        drive = path.drive[0].lower()
        return f"/{drive}/{path.as_posix().split('/', 1)[1]}"

    def _run_backup(self, **extra_env: str) -> subprocess.CompletedProcess[str]:
        self.remote.mkdir(exist_ok=True)
        env = os.environ.copy()
        env.update(
            {
                "PATH": f"{self.bin}{os.pathsep}{env['PATH']}",
                "PROJECT_DIR": self._bash_path(self.project),
                "BACKUP_ROOT": self._bash_path(self.backups),
                "RCLONE_CONFIG": self._bash_path(self.root / "rclone.conf"),
                "BACKUP_REMOTE": "cos-crypt:eiheizone-backups",
                "MOCK_REMOTE": self._bash_path(self.remote),
                "MOCK_MEDIA": self._bash_path(self.media),
                "MOCK_EVENTS": self._bash_path(self.events),
                "MOCK_FAILURES": self._bash_path(self.failures),
                **extra_env,
            }
        )
        return subprocess.run(
            ["bash", str(SCRIPT)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def _create_old_backup(self, days_old: int) -> str:
        name = f"eiheizone-202610{22 - days_old:02d}_010101.tar.gz"
        path = self.remote / name
        path.write_bytes(b"old-backup")
        timestamp = (datetime.now(timezone.utc) - timedelta(days=days_old)).timestamp()
        os.utime(path, (timestamp, timestamp))
        return name

    def test_success_restores_backend_before_upload_and_keeps_seven(self) -> None:
        old_names = {self._create_old_backup(days) for days in range(1, 9)}

        result = self._run_backup()

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        events = self.events.read_text(encoding="utf-8").splitlines()
        self.assertLess(events.index("STOP"), events.index("DUMP"))
        self.assertLess(events.index("MEDIA"), events.index("START"))
        self.assertLess(events.index("START"), events.index("UPLOAD"))
        self.assertLess(events.index("UPLOAD"), events.index("CHECK"))
        self.assertEqual(len(list(self.remote.iterdir())), 7)
        self.assertTrue(old_names.intersection(path.name for path in self.remote.iterdir()))
        self.assertFalse(list(self.backups.glob(".work.*")))

    def test_upload_failure_preserves_local_material_and_old_backups(self) -> None:
        old_names = {self._create_old_backup(days) for days in range(1, 8)}
        (self.failures / "upload").touch()

        result = self._run_backup()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("START", self.events.read_text(encoding="utf-8"))
        self.assertEqual(old_names, {path.name for path in self.remote.iterdir()})
        work_dirs = list(self.backups.glob(".work.*"))
        self.assertEqual(len(work_dirs), 1)
        self.assertTrue((work_dirs[0] / "payload/database.dump").exists())
        self.assertTrue((work_dirs[0] / "payload/media.tar.gz").exists())

    def test_failed_remote_verification_does_not_prune_old_backups(self) -> None:
        old_names = {self._create_old_backup(days) for days in range(1, 8)}
        (self.failures / "check").touch()

        result = self._run_backup()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(old_names, old_names.intersection(path.name for path in self.remote.iterdir()))
        self.assertTrue(list(self.backups.glob(".work.*")))
        self.assertNotIn("DELETE:", self.events.read_text(encoding="utf-8"))

    def test_failed_backend_restart_is_retried_by_exit_trap(self) -> None:
        (self.failures / "start").touch()

        result = self._run_backup()

        events = self.events.read_text(encoding="utf-8").splitlines()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(events.count("START"), 2)
        self.assertTrue(list(self.backups.glob(".work.*")))
        self.assertFalse(list(self.remote.iterdir()))

    def test_media_snapshot_failure_restarts_backend(self) -> None:
        (self.failures / "media").touch()

        result = self._run_backup()

        self.assertNotEqual(result.returncode, 0)
        events = self.events.read_text(encoding="utf-8").splitlines()
        self.assertIn("MEDIA", events)
        self.assertEqual(events.count("START"), 1)
        self.assertNotIn("UPLOAD", events)
        self.assertFalse(list(self.remote.iterdir()))


if __name__ == "__main__":
    unittest.main()
