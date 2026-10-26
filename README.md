# commitledger: who owes what by when, from a customer channel

Akkari "listens to every conversation and reads every thread to surface commitments, requests, blockers, issues, risks and next steps, explicit or implied", then drives each loop until it is closed (https://akkari.io/). The first step is the unglamorous one: telling a real commitment ("I'll send the SOC 2 report by Friday") from a look-alike ("We might add that at some point", "Should I send it?"), resolving "by Friday" against the message date, and noticing when a later message closes it. This prototype does that on synthetic customer threads with known answers.

## What it does
`commitledger/extract.py`: for each message, split into sentences; vendor sentences with a commitment cue (`I'll`, `we'll`, `let me`, `I can`, `I'm going to`, `happy to`) become COMMITMENT unless hedged, conditional, negated, in the past, or a question; customer sentences starting `Can you / Please / We need you to` become REQUEST; `... is blocking us / waiting on ...` becomes BLOCKER. Due dates (`by Friday`, `tomorrow`, `by EOD`, `next Tuesday`, `in 2 days`, `this week`, `by the 15th`) are resolved from the message date. A later message with a completion cue and two shared action words closes the item. `overdue()` lists open items past their due date.

## Results (synthetic threads of 3-6 items, 600 each; gold written by the generator)
Dev: seeds 0-599 (1,997 items). Held-out: seeds 10000-10599 (1,986 items) with new phrasing (`Happy to ...`, `I'm going to ...`, `ETA ...: we'll ...`, `I'm on it, I'll ...`) and new look-alikes (`We'd love to ... eventually`, `Not sure we can ...`, `I'll think about whether to ...`); fixed in git before the first run.

| | dev | held-out run 1 | held-out run 2 (after two small fixes) |
|---|---|---|---|
| items found (gold) | 1,988 / 1,997 | 1,882 / 1,986 | **1,979 / 1,986** |
| items that are not real | 0 | 78 | **0** |
| keyword rule ("will / please / can you / blocking") finds | 1,519 | 1,374 | 1,374 (75 false items) |
| due date right (dated items) | 1,402 / 1,402 | 1,342 / 1,342 | 1,423 / 1,423 |
| closure right | 1,988 / 1,988 | 1,882 / 1,882 | 1,979 / 1,979 |
| overdue items found / false | 572 of 574 / 0 | 551 of 586 / 0 | **584 of 586 / 0** |

Run 1 missed `Happy to ...` (not in my cue list) and accepted `Not sure we can ...` and `I'll think about whether to ...` as commitments; I added `happy to` and the two hedges and re-ran. Run 1 is in `out/first_run.txt`. During dev a closing phrase (`All set, ...`) was missing from the completion cues and one generator flaw (the same action twice in a thread merged two items) was fixed.

## Read this before believing the table
Near-circular: I wrote the phrase families on both sides, the dates come from 7 patterns, and every closure shares the action's words. Real threads have implied commitments ("sure, Friday works"), pronouns, several asks in one sentence, time zones, edits and sarcasm, and an implied commitment is exactly what the Akkari page says it wants. Nothing here uses Akkari data or systems.

## Run it (3 commands)
```
pip install pytest
python -m pytest -q tests
python -m commitledger.run
```
Standard library only. 4 tests.

Unofficial prototype by Kushagra Pratap Singh. Not affiliated with Akkari.
