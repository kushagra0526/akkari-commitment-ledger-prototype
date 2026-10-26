import datetime as dt
import json
import re
from collections import Counter

from . import extract, gen


def gold_due(g):
    d, k = g["ts"], g["key"]
    if k is None:
        return None
    return {"fri": d + dt.timedelta(days=(4 - d.weekday()) % 7), "tom": d + dt.timedelta(days=1), "eod": d, "2d": d + dt.timedelta(days=2),
            "tw": d + dt.timedelta(days=(4 - d.weekday()) % 7), "nt": d + dt.timedelta(days=7 - d.weekday()) + dt.timedelta(days=1)}[k]


KEYWORD = re.compile(r"\b(will|i'll|we'll|can you|could you|please|need you to|blocking|blocked)\b", re.I)


def keyword_items(msgs):
    return [{"src": m["id"], "kind": "ANY"} for m in msgs for s in extract.sentences(m["text"]) if KEYWORD.search(s)]


def score(seeds, held):
    t = Counter()
    for s in seeds:
        msgs, gold, report = gen.make_thread(s, held)
        items = extract.extract(msgs)
        g_by, i_by = {g["src"]: g for g in gold}, {i["src"]: i for i in items}
        k_srcs = {i["src"] for i in keyword_items(msgs)}
        t["gold_items"] += len(gold)
        t["found"] += len(g_by.keys() & i_by.keys())
        t["extra_items"] += len(i_by.keys() - g_by.keys())
        t["kw_found"] += len(g_by.keys() & k_srcs)
        t["kw_extra"] += len(k_srcs - g_by.keys())
        for src in g_by.keys() & i_by.keys():
            g, i = g_by[src], i_by[src]
            t["kind_right"] += g["kind"] == i["kind"]
            if g["key"]:
                t["dated"] += 1
                t["due_right"] += gold_due(g) == i["due"]
            t["closure_right"] += g["closed_by"] == i["closed_by"]
        gold_over = {g["src"] for g in gold if g["closed_by"] is None and gold_due(g) and gold_due(g) < report}
        mine_over = {i["src"] for i in extract.overdue(items, report)}
        t["overdue_gold"] += len(gold_over)
        t["overdue_found"] += len(gold_over & mine_over)
        t["overdue_false"] += len(mine_over - gold_over)
    return dict(t)


def main():
    res = {"dev": score(range(0, 600), False), "held_out": score(range(10000, 10600), True)}
    json.dump(res, open("out/result.json", "w"), indent=1)
    for k, v in res.items():
        print(k, v)


if __name__ == "__main__":
    main()
