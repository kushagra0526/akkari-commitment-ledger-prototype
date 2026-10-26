"""Customer-channel conversations with gold items: each planted commitment/request/blocker has a due date and maybe a closing message."""
import datetime as dt
import random

ACTIONS = [("send the SOC 2 report", "SOC 2 report"), ("ship the fix for the export bug", "export bug fix"), ("raise your API limit", "API limit"),
           ("schedule the security review", "security review"), ("share the pricing sheet", "pricing sheet"), ("fix the SSO login issue", "SSO login issue"),
           ("add the webhook retry setting", "webhook retry setting")]
DATES = [("by Friday", "fri"), ("tomorrow", "tom"), ("by EOD", "eod"), ("next Tuesday", "nt"), ("in 2 days", "2d"), ("this week", "tw"), ("", None)]
COMMIT_FRAMES = ["I'll {a} {d}.", "We'll {a} {d}.", "I will {a} {d}.", "Let me {a} {d}.", "I can {a} {d}."]
HELD_COMMIT = ["Happy to {a} {d}.", "I'm going to {a} {d}.", "We're going to {a} {d}.", "I'm on it, I'll {a} {d}.", "ETA {d}: we'll {a}."]
REQ_FRAMES = ["Can you {a} {d}?", "Please {a} {d}.", "We need you to {a} {d}."]
NONCOMMIT = ["We might {a} at some point.", "If you'd like, I could {a}.", "We can't {a} before launch.", "Should I {a}?", "{A} is on the roadmap.", "I wish we could {a}."]
HELD_NON = ["We'd love to {a} eventually.", "I would love to {a} someday.", "Not sure we can {a}.", "I'll think about whether to {a}."]
BLOCK = ["The {n} is blocking us.", "We are blocked on the {n}.", "Still waiting on the {n}."]
CLOSE = ["Done: {past}.", "Just shipped it, {past}.", "All set, {past}.", "Got it, thanks, {past}."]
PAST = {"SOC 2 report": "the SOC 2 report is in your inbox", "export bug fix": "the export bug fix is live", "API limit": "your API limit is raised",
        "security review": "the security review is scheduled", "pricing sheet": "the pricing sheet is shared", "SSO login issue": "the SSO login issue is fixed",
        "webhook retry setting": "the webhook retry setting is added"}


def make_thread(seed, held_out=False):
    rng = random.Random(seed)
    start = dt.date(2026, 6, 1) + dt.timedelta(days=rng.randrange(0, 60))
    msgs, gold, day, mid = [], [], start, 0
    commit_frames = COMMIT_FRAMES + (HELD_COMMIT if held_out else [])
    non = NONCOMMIT + (HELD_NON if held_out else [])
    pool = rng.sample(ACTIONS, len(ACTIONS))   # one thread never repeats an action
    for _ in range(rng.randint(3, 6)):
        day += dt.timedelta(days=rng.choice([0, 1, 1, 2, 3]))
        while day.weekday() > 4:
            day += dt.timedelta(days=1)
        a, noun = pool.pop()
        d, key = rng.choice(DATES)
        kind = rng.choices(["commit", "request", "blocker", "non"], [4, 3, 1.5, 3])[0]
        if kind == "commit":
            frame = rng.choice(commit_frames)
            text = frame.format(a=a, d=d).replace(" .", ".").replace("  ", " ")
            msgs.append({"id": mid, "ts": day, "who": "vendor", "text": text})
            gold.append({"src": mid, "kind": "COMMITMENT", "noun": noun, "key": key, "ts": day})
        elif kind == "request":
            text = rng.choice(REQ_FRAMES).format(a=a, d=d).replace(" ?", "?").replace(" .", ".").replace("  ", " ")
            msgs.append({"id": mid, "ts": day, "who": "customer", "text": text})
            gold.append({"src": mid, "kind": "REQUEST", "noun": noun, "key": key, "ts": day})
        elif kind == "blocker":
            msgs.append({"id": mid, "ts": day, "who": "customer", "text": rng.choice(BLOCK).format(n=noun)})
            gold.append({"src": mid, "kind": "BLOCKER", "noun": noun, "key": None, "ts": day})
        else:
            text = rng.choice(non).format(a=a, A=a[0].upper() + a[1:])
            msgs.append({"id": mid, "ts": day, "who": rng.choice(["vendor", "customer"]), "text": text})
        mid += 1
        # sometimes the vendor answers a request, sometimes the item gets closed later
        if gold and gold[-1]["src"] == mid - 1 and rng.random() < 0.55:
            day += dt.timedelta(days=rng.choice([0, 1, 2, 4]))
            msgs.append({"id": mid, "ts": day, "who": "vendor", "text": rng.choice(CLOSE).format(past=PAST[gold[-1]["noun"]])})
            gold[-1]["closed_by"] = mid
            mid += 1
    for g in gold:
        g.setdefault("closed_by", None)
    return msgs, gold, day + dt.timedelta(days=rng.randrange(1, 10))
