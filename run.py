import os
import socket

from app import create_app

app = create_app()


def _default_host():
    """Return a loopback bind address that works regardless of how `localhost` resolves.

    An IPv4-only listener is unreachable at [::1]. Browsers on IPv6-preferring
    hosts resolve `localhost` to ::1 first, so the connection is refused before
    any CORS or auth logic runs and the browser reports only "Failed to fetch".
    Binding :: accepts IPv4-mapped connections as well, where the kernel supports
    it; otherwise fall back so the server still starts.
    """
    if not socket.has_ipv6:
        return '0.0.0.0'
    probe = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    try:
        probe.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    except OSError:
        return '0.0.0.0'
    finally:
        probe.close()
    return '::'


if __name__ == '__main__':
    host = os.environ.get('HOST') or _default_host()
    app.run(debug=True, host=host, port=int(os.environ.get('PORT', 5000)))