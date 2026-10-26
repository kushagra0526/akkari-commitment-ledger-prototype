import datetime as dt

from commitledger import extract

D = dt.date(2026, 6, 3)   # a Wednesday


def msg(i, who, text, ts=D):
    return {"id": i, "ts": ts, "who": who, "text": text}


def test_due_dates_resolve_against_the_message_date():
    assert extract.parse_due("by Friday", D) == dt.date(2026, 6, 5)
    assert extract.parse_due("tomorrow", D) == dt.date(2026, 6, 4)
    assert extract.parse_due("next Tuesday", D) == dt.date(2026, 6, 9)
    assert extract.parse_due("in 2 days", D) == dt.date(2026, 6, 5)
    assert extract.parse_due("by the 15th", D) == dt.date(2026, 6, 15)


def test_hedged_negated_and_question_sentences_make_no_item():
    for t in ["We might send the SOC 2 report at some point.", "We can't ship the fix before launch.", "Should I send the pricing sheet?", "If you'd like, I could raise your API limit."]:
        assert extract.extract([msg(0, "vendor", t)]) == []


def test_commitment_request_and_blocker_are_found_and_closed():
    ms = [msg(0, "customer", "Can you raise your API limit by Friday?"), msg(1, "customer", "The security review is blocking us."),
          msg(2, "vendor", "Done: your API limit is raised.", D + dt.timedelta(days=1))]
    it = extract.extract(ms)
    kinds = {i["src"]: i["kind"] for i in it}
    assert kinds == {0: "REQUEST", 1: "BLOCKER"}
    assert it[0]["closed_by"] == 2 and it[1]["closed_by"] is None


def test_overdue_lists_only_open_items_past_due():
    it = extract.extract([msg(0, "vendor", "I'll send the pricing sheet tomorrow."), msg(1, "vendor", "I'll share the SOC 2 report by Friday.")])
    assert [i["src"] for i in extract.overdue(it, dt.date(2026, 6, 5))] == [0]
