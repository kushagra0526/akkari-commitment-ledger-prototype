"""Open-item ledger from a customer channel: who owes what by when, and what has been closed.

Vendor messages create COMMITMENTS ("I'll send the report by Friday"); customer messages create REQUESTS ("Can you ...?") and
BLOCKERS ("... is blocking us"). Hedged, conditional, negated, past-tense and question sentences create nothing. Due dates are resolved
against the message date. A later message with a completion cue that shares the action's words closes the item.
"""
import datetime as dt
import re

WD = {"monday": 0, "mon": 0, "tuesday": 1, "tue": 1, "tues": 1, "wednesday": 2, "wed": 2, "thursday": 3, "thu": 3, "thur": 3, "thurs": 3, "friday": 4, "fri": 4, "saturday": 5, "sat": 5, "sunday": 6, "sun": 6}
NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
COMMIT = re.compile(r"\b(i'll|i will|we'll|we will|let me|i can|we can|i'm going to|we're going to)\b", re.I)
BLOCK_VERB = r"(blocking us|blocked on|can't proceed until|waiting on)"
HEDGE = re.compile(r"\b(might|maybe|perhaps|could|someday|at some point|eventually|if you|if we|can't|cannot|won't|unable|roadmap|would love)\b", re.I)
REQUEST = re.compile(r"^(?:\w+[, ]+)?(can you|could you|please|we need you to|need you to)\b", re.I)
DONE = re.compile(r"\b(done|all set|sent|shipped|fixed|raised|scheduled|received|got it|resolved|deployed|shared)\b", re.I)
STOP = set("the a an to of for and your our you we i it that this is are be will by on in at with about".split())


def next_weekday(d, wd, strict=True):
    delta = (wd - d.weekday()) % 7
    if delta == 0 and strict:
        delta = 7
    return d + dt.timedelta(days=delta)


def parse_due(text, today):
    t = text.lower()
    if re.search(r"\b(today|eod|end of (the )?day|cob)\b", t) and not re.search(r"\bcob (mon|tue|wed|thu|fri)", t):
        return today
    if "tomorrow" in t:
        return today + dt.timedelta(days=1)
    m = re.search(r"\bin (\d+|one|two|three|four|five) days?\b", t)
    if m:
        n = int(m.group(1)) if m.group(1).isdigit() else NUM[m.group(1)]
        return today + dt.timedelta(days=n)
    m = re.search(r"\bnext (monday|tuesday|wednesday|thursday|friday|mon|tue|wed|thu|fri)\b", t)
    if m:
        return next_weekday(today + dt.timedelta(days=6 - today.weekday()), WD[m.group(1)], strict=False)   # the named day of next week
    m = re.search(r"\b(?:by |on |this )?(monday|tuesday|wednesday|thursday|friday|mon|tue|tues|wed|thu|thur|thurs|fri)\b", t)
    if m:
        return next_weekday(today, WD[m.group(1)], strict=False)
    m = re.search(r"\bby the (\d{1,2})(?:st|nd|rd|th)\b", t)
    if m:
        day = int(m.group(1))
        d = today.replace(day=min(day, 28)) if day <= 28 else today.replace(day=28)
        return d if d >= today else (d.replace(month=d.month % 12 + 1, year=d.year + (d.month == 12)))
    if re.search(r"\b(this week|end of (the )?week|eow)\b", t):
        return next_weekday(today, 4, strict=False)
    return None


def tokens(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 2}


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", text) if s.strip()]


def extract(messages):
    """messages: [{id, ts(date), who('vendor'|'customer'), text}] -> items [{src, kind, owner, text, due, closed_by}]"""
    items = []
    for m in messages:
        for s in sentences(m["text"]):
            low = s.lower()
            if s.endswith("?") and m["who"] == "vendor":
                continue
            if m["who"] == "vendor" and COMMIT.search(s) and not HEDGE.search(s) and not re.match(r"^(if|should|did)\b", low):
                body = COMMIT.split(s, maxsplit=1)[-1]
                if len(tokens(body)) >= 2:
                    items.append({"src": m["id"], "kind": "COMMITMENT", "owner": "vendor", "text": s, "due": parse_due(s, m["ts"]), "closed_by": None, "ts": m["ts"]})
            elif m["who"] == "customer" and REQUEST.match(s) and not HEDGE.search(re.sub(r"^(?:\w+[, ]+)?could you", "", s, flags=re.I)):
                items.append({"src": m["id"], "kind": "REQUEST", "owner": "vendor", "text": s, "due": parse_due(s, m["ts"]), "closed_by": None, "ts": m["ts"]})
            elif m["who"] == "customer" and re.search(BLOCK_VERB, low):
                items.append({"src": m["id"], "kind": "BLOCKER", "owner": "vendor", "text": s, "due": None, "closed_by": None, "ts": m["ts"]})
    # merge a request with the commitment that answers it (same action words, same thread day or later): keep the earlier, due date from either
    out = []
    for it in items:
        dup = next((o for o in out if o["kind"] != "BLOCKER" and it["kind"] != "BLOCKER" and len(tokens(o["text"]) & tokens(it["text"])) >= 3 and it["src"] != o["src"]), None)
        if dup:
            dup["due"] = dup["due"] or it["due"]
            continue
        out.append(it)
    for it in out:
        for m in messages:
            if m["id"] > it["src"] and DONE.search(m["text"]) and len(tokens(m["text"]) & tokens(it["text"])) >= 2 and not (m["who"] == "customer" and "?" in m["text"]):
                it["closed_by"] = m["id"]
                break
    return out


def overdue(items, today):
    return [i for i in items if i["closed_by"] is None and i["due"] is not None and i["due"] < today]
