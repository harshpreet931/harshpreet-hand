"""Measure what building the font cost, from this Claude Code session's transcript.

Every assistant turn in ~/.claude/projects/<project>/<session>.jsonl carries the
API `usage` block; we dedupe by message id and price it at Claude Opus 5.5 list
prices (per million tokens): input $4, output $20, cache read $0.20,
cache write 2x input for the 1-hour TTL ($8) / 1.25x for 5-minute ($5).
"""
import collections
import datetime
import glob
import json
import os
import sys

PRICE = dict(input=4.00, output=20.00, cache_read=0.20, cache_write_1h=8.00, cache_write_5m=5.00)


def load(path):
    return [json.loads(l) for l in open(path)]


def user_text(r):
    c = r.get("message", {}).get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(b.get("text", "") for b in c if b.get("type") == "text")
    return ""


def measure(rows, lo, hi):
    msgs, tools, reads_img = {}, collections.Counter(), 0
    first = last = None
    for r in rows[lo:hi]:
        if r.get("type") != "assistant":
            continue
        m = r["message"]
        u = m.get("usage") or {}
        prev = msgs.get(m.get("id"))
        if prev is None or u.get("output_tokens", 0) >= prev.get("output_tokens", 0):
            msgs[m.get("id")] = u
        for b in m.get("content", []):
            if b.get("type") == "tool_use":
                tools[b["name"]] += 1
                fp = (b.get("input") or {}).get("file_path", "")
                if b["name"] == "Read" and fp.lower().endswith((".png", ".jpg", ".jpeg")):
                    reads_img += 1
        last = r["timestamp"]
    t = collections.Counter()
    for u in msgs.values():
        t["input"] += u.get("input_tokens", 0) or 0
        t["cache_read"] += u.get("cache_read_input_tokens", 0) or 0
        cc = u.get("cache_creation") or {}
        t["cache_write_1h"] += cc.get("ephemeral_1h_input_tokens", 0) or 0
        t["cache_write_5m"] += cc.get("ephemeral_5m_input_tokens", 0) or 0
        t["output"] += u.get("output_tokens", 0) or 0
        t["thinking"] += (u.get("output_tokens_details") or {}).get("thinking_tokens", 0) or 0
    cost = {k: t[k] * PRICE[k] / 1e6 for k in ("input", "output", "cache_read", "cache_write_1h", "cache_write_5m")}
    all_in = t["input"] + t["cache_read"] + t["cache_write_1h"] + t["cache_write_5m"]
    no_cache = all_in * PRICE["input"] / 1e6 + cost["output"]
    return dict(api_calls=len(msgs), tool_calls=sum(tools.values()), tools=dict(tools), images_viewed=reads_img,
                tokens=dict(t), total_tokens=all_in + t["output"], cost=cost, cost_total=sum(cost.values()),
                cost_without_caching=no_cache, last=last)


if __name__ == "__main__":
    proj = os.path.expanduser("~/.claude/projects/-Users-harshpreet-singh-Desktop-Projects-myHandwriting")
    path = sys.argv[1] if len(sys.argv) > 1 else max(glob.glob(f"{proj}/*.jsonl"), key=os.path.getmtime)
    rows = load(path)
    start = next(i for i, r in enumerate(rows) if r.get("type") == "user" and "<command-name>/goal" in user_text(r))
    end = next(i for i, r in enumerate(rows) if i > start and r.get("type") == "user" and "x post" in user_text(r).lower())
    s = measure(rows, start, end)
    t0 = datetime.datetime.fromisoformat(rows[start]["timestamp"].replace("Z", "+00:00"))
    t1 = datetime.datetime.fromisoformat(s["last"].replace("Z", "+00:00"))
    s["duration_seconds"] = int((t1 - t0).total_seconds())
    s["started"], s["model"] = rows[start]["timestamp"], "claude-opus-5-5"
    s["prices_per_mtok"] = PRICE
    json.dump(s, open(sys.argv[2] if len(sys.argv) > 2 else "session_stats.json", "w"), indent=2)
    print(json.dumps({k: v for k, v in s.items() if k != "tools"}, indent=2))
