"""Minimal STK Connect TCP client.

Only used for the raw-command escape hatch and for reading the exact STK
version. The object-model COM API remains the primary control channel.
"""

from __future__ import annotations

import logging
import re
import socket
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_VERSION_RE = re.compile(r"STK\s+v?([0-9][0-9A-Za-z.\-]*)", re.IGNORECASE)


@dataclass
class ConnectResult:
    command: str
    ack: str | None
    data: list[str]
    raw: str
    transport: str = "tcp"

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "ack": self.ack,
            "data": self.data,
            "raw": self.raw,
            "transport": self.transport,
        }


class ConnectClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 5001) -> None:
        self.host = host
        self.port = port

    def is_available(self, timeout: float = 0.8) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((self.host, self.port))
            return True
        except OSError:
            return False
        finally:
            sock.close()

    def execute(self, command: str, timeout: float = 30.0) -> ConnectResult:
        command = command.strip()
        if not command:
            raise ValueError("Connect command must not be empty")
        payload = (command + "\n").encode("utf-8")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        chunks: list[bytes] = []
        last_data = 0.0
        try:
            sock.connect((self.host, self.port))
            sock.sendall(payload)
            started = time.monotonic()
            while True:
                now = time.monotonic()
                if now - started > timeout:
                    break
                try:
                    block = sock.recv(65536)
                except socket.timeout:
                    if chunks and (now - last_data) > 0.6:
                        break
                    if not chunks and (now - started) > 3.0:
                        break
                    continue
                if not block:
                    break
                chunks.append(block)
                last_data = time.monotonic()
        finally:
            sock.close()

        raw = b"".join(chunks).decode("utf-8", errors="replace")
        ack = None
        if raw.startswith("ACK"):
            ack = "ACK"
        elif raw.startswith("NACK") or raw.startswith("NAK"):
            ack = "NAK"
        lines = [line.strip() for line in raw.replace("\r", "").split("\n") if line.strip()]
        # Strip the ACK/NACK token and the "COMMAND <n>" header line.
        data = [
            line
            for line in lines
            if line not in {"ACK", "NACK", "NAK"} and not re.match(r"^[A-Z0-9_]+\s+\d+\s*$", line)
        ]
        return ConnectResult(command=command, ack=ack, data=data, raw=raw)

    def get_version(self, timeout: float = 5.0) -> str | None:
        try:
            result = self.execute("GetSTKVersion /", timeout=timeout)
        except OSError:
            return None
        match = _VERSION_RE.search(result.raw)
        if match:
            return f"STK {match.group(1)}"
        return None
