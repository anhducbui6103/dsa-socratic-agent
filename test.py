from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

try:
    req = Request(
        "https://openrouter.ai/api/v1/chat/completions",
        method="GET",
        headers={"User-Agent": "test"},
    )
    with urlopen(req, timeout=20) as res:
        print(res.status)
        print(res.read().decode("utf-8", errors="replace"))
except HTTPError as e:
    print("HTTPError:", e.code)
    print(e.read().decode("utf-8", errors="replace"))
except URLError as e:
    print("URLError:", repr(e.reason))