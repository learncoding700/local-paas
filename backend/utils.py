import re
import socket
from typing import List

IMAGE_REGEX = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._\-/:@]*$")
DANGEROUS_SUBSTRINGS = ("..", "//", ";", "&", "|", "$", "`", "\n", "\r", "\x00")


def validate_image_name(image: str) -> bool:
    if not image or not image.strip():
        return False
    s = image.strip()
    if len(s) > 255:
        return False
    for bad in DANGEROUS_SUBSTRINGS:
        if bad in s:
            return False
    if not IMAGE_REGEX.match(s):
        return False
    return True


def get_next_port(used_ports: List[int]) -> int:
    used = set(used_ports)
    for port in range(5000, 6001):
        if port not in used:
            return port
    raise RuntimeError("No free host port in range 5000-6000")


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"
