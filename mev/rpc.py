"""Minimal JSON-RPC client with retries, batching and a fallback endpoint."""
import json
import sys
import time
import urllib.request

ENDPOINTS = ["https://rpc.mevblocker.io", "https://eth.drpc.org"]


def _post(url, payload, timeout=120):
    req = urllib.request.Request(url, json.dumps(payload).encode(),
                                 {"Content-Type": "application/json", "User-Agent": "mev-study"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def call(method, params, tries=8, endpoints=None):
    endpoints = endpoints or ENDPOINTS
    last = None
    for i in range(tries):
        url = endpoints[i % len(endpoints)] if i >= 3 else endpoints[0]
        try:
            d = _post(url, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
            if "result" in d:
                return d["result"]
            last = d.get("error")
        except Exception as e:  # network errors, 429, 5xx
            last = e
        print(f"rpc retry {i} {method}: {last}", file=sys.stderr)
        time.sleep(min(30, 2 * (i + 1)))
    raise RuntimeError(f"{method} failed: {last}")


def batch(calls, size=50, tries=8):
    """calls: list of (method, params). Returns results in order. Falls back to single calls."""
    out = []
    for k in range(0, len(calls), size):
        chunk = calls[k:k + size]
        payload = [{"jsonrpc": "2.0", "id": j, "method": m, "params": p} for j, (m, p) in enumerate(chunk)]
        res = None
        for i in range(tries):
            try:
                d = _post(ENDPOINTS[0], payload)
                if isinstance(d, list) and len(d) == len(chunk) and all("result" in x for x in d):
                    res = [x["result"] for x in sorted(d, key=lambda x: x["id"])]
                    break
                print(f"batch partial/err {str(d)[:200]}", file=sys.stderr)
            except Exception as e:
                print(f"batch retry {i}: {e}", file=sys.stderr)
            time.sleep(min(30, 2 * (i + 1)))
        if res is None:
            res = [call(m, p) for m, p in chunk]
        out += res
    return out


def block_ts(n):
    return int(call("eth_getBlockByNumber", [hex(n), False])["timestamp"], 16)


def block_at_or_after(ts, lo, hi):
    """First block with timestamp >= ts (binary search)."""
    while lo < hi:
        mid = (lo + hi) // 2
        if block_ts(mid) < ts:
            lo = mid + 1
        else:
            hi = mid
    return lo
