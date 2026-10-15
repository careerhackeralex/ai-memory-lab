import shutil
import socket
import subprocess

import httpx


def listen_addrs(port: int) -> list[str]:
    if shutil.which("lsof"):
        out = subprocess.run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-Fn"], capture_output=True, text=True).stdout
        return sorted({l[1:] for l in out.splitlines() if l.startswith("n")})
    out = subprocess.run(["ss", "-ltnH", f"sport = :{port}"], capture_output=True, text=True).stdout
    return sorted({l.split()[3] for l in out.splitlines() if l.strip()})


def lan_ip() -> str | None:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.0.2.1", 9))  # 패킷은 보내지 않는다. 기본 경로의 내 주소만 얻음
        ip = s.getsockname()[0]
        return None if ip.startswith("127.") else ip
    except OSError:
        return None
    finally:
        s.close()


def test_01_bind(base, port):
    r = httpx.get(base + "/health", timeout=10)
    assert r.status_code == 200 and r.json().get("status") == "healthy", f"/health 응답: {r.status_code}"
    addrs = listen_addrs(port)
    assert addrs, f"포트 {port}에서 듣는 프로세스가 없습니다"
    bad = [a for a in addrs if a.startswith(("*:", "0.0.0.0", "[::]", ":::"))]
    assert not bad, f"모든 주소로 열려 있습니다: {bad}"
    assert all(a.startswith(("127.0.0.1:", "[::1]:", "localhost:")) for a in addrs), addrs
    ip = lan_ip()
    if ip:  # 같은 네트워크 주소로는 접속이 안 돼야 한다
        s = socket.socket()
        s.settimeout(2)
        assert s.connect_ex((ip, port)) != 0, f"{ip}:{port}로 접속됩니다"
        s.close()
