"""
Запуск Cloudflare quick-tunnel для публичного доступа к локальному фронтенду.

Что делает:
- Запускает `cloudflared.exe tunnel --url http://localhost:5173`
  (порт можно переопределить переменной ROADMATE_TUNNEL_URL).
- Стримит вывод cloudflared в текущую консоль.
- Как только в выводе появляется `https://<...>.trycloudflare.com`,
  печатает её в крупной рамке, чтобы её было удобно скопировать и
  отправить друзьям.
- При падении cloudflared показывает понятное сообщение, не закрывая
  окно (если запущено из bat — пользователь увидит причину).

Используется из `run_with_tunnel.bat`, но можно запускать и руками:
    .venv\\Scripts\\python.exe scripts\\share_tunnel.py
"""

from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
from pathlib import Path

URL_RE = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
DEFAULT_TARGET = "http://localhost:5173"
BANNER_WIDTH = 70


def _find_cloudflared(repo_root: Path) -> Path | None:
    """Ищем cloudflared рядом с проектом или в PATH."""
    exe_name = "cloudflared.exe" if os.name == "nt" else "cloudflared"
    candidate = repo_root / exe_name
    if candidate.exists():
        return candidate

    # Фоллбек: вдруг cloudflared в PATH (например, установлен через winget).
    from shutil import which

    found = which(exe_name)
    if found:
        return Path(found)
    return None


def _print_banner(url: str) -> None:
    line = "=" * BANNER_WIDTH
    print("", flush=True)
    print(line, flush=True)
    print(" PUBLIC URL FOR YOUR FRIENDS:", flush=True)
    print(f"   {url}", flush=True)
    print("", flush=True)
    print(" Send this link to anyone — it works through the internet.", flush=True)
    print(" Tunnel stays alive while THIS window is open.", flush=True)
    print(" Press Ctrl+C here to stop the tunnel.", flush=True)
    print(line, flush=True)
    print(" NOTE: every restart of this script generates a NEW URL.", flush=True)
    print(" Any *.trycloudflare.com URL from a previous run is DEAD.", flush=True)
    print(line, flush=True)
    print("", flush=True)


def _print_dead_banner(last_url: str | None) -> None:
    line = "=" * BANNER_WIDTH
    print("", flush=True)
    print(line, flush=True)
    print(" TUNNEL STOPPED.", flush=True)
    if last_url:
        print(f"   {last_url}", flush=True)
        print(" ^ this URL is now DEAD and will NOT load anywhere.", flush=True)
    print(" Cloudflare quick-tunnels live only while cloudflared is running.", flush=True)
    print(" Re-run run_with_tunnel.bat to get a NEW public URL.", flush=True)
    print(line, flush=True)
    print("", flush=True)


def _save_url_file(url_file: Path, url: str) -> None:
    try:
        url_file.parent.mkdir(parents=True, exist_ok=True)
        url_file.write_text(url + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"[warn] could not write {url_file}: {exc}", flush=True)


def _clear_url_file(url_file: Path) -> None:
    try:
        if url_file.exists():
            url_file.unlink()
    except OSError:
        pass


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    cf = _find_cloudflared(repo_root)
    if cf is None:
        print(
            "[ERROR] cloudflared not found. Put cloudflared.exe at the project root "
            "or install it from https://github.com/cloudflare/cloudflared/releases/latest",
            file=sys.stderr,
            flush=True,
        )
        return 1

    target = os.environ.get("ROADMATE_TUNNEL_URL", DEFAULT_TARGET)

    url_file = repo_root / "logs" / "tunnel_url.txt"
    # wipe the URL from a previous session before we know the new one
    _clear_url_file(url_file)

    print(f"Starting Cloudflare quick tunnel for {target} ...", flush=True)
    print("This usually takes 5-30 seconds. Please wait.", flush=True)
    print("", flush=True)

    cmd = [str(cf), "tunnel", "--no-autoupdate", "--url", target]

    # На Windows запускаем в новой группе процессов, чтобы Ctrl+C ловить только
    # здесь, а не убивать родительское окно cmd.exe.
    popen_kwargs: dict[str, object] = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
        "bufsize": 1,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    try:
        proc = subprocess.Popen(cmd, **popen_kwargs)  # type: ignore[arg-type]
    except FileNotFoundError:
        print(f"[ERROR] cannot launch {cf}", file=sys.stderr, flush=True)
        return 1

    found_url: str | None = None
    assert proc.stdout is not None
    try:
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            if found_url is None:
                match = URL_RE.search(line)
                if match:
                    found_url = match.group(0)
                    _save_url_file(url_file, found_url)
                    _print_banner(found_url)
        proc.wait()
    except KeyboardInterrupt:
        print("", flush=True)
        print("Stopping tunnel ...", flush=True)
        try:
            if os.name == "nt":
                proc.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    # tunnel is gone — clear the URL file so a stale value doesn't mislead
    _clear_url_file(url_file)

    rc = proc.returncode or 0
    if found_url is None and rc != 0:
        print("", flush=True)
        print(
            "[ERROR] cloudflared exited before printing a public URL "
            f"(exit code {rc}).",
            file=sys.stderr,
            flush=True,
        )
        print(
            "Possible reasons: no internet, cloudflared blocked by antivirus, "
            "trycloudflare.com is unreachable from your network, or the local "
            f"target {target} is not responding.",
            file=sys.stderr,
            flush=True,
        )
    else:
        _print_dead_banner(found_url)
    return rc


if __name__ == "__main__":
    sys.exit(main())
