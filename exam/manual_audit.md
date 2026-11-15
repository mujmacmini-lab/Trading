**Extra audit, because the session logs the spec asks for are not on this machine.** The Fable strategies were
built in a separate cloud session ("BTCUSDT 4h trading strategies", 14 Nov 2026, 21:03-21:24 UTC), so its log
files live in that session's own container, not here. As a substitute, every tool call of that session was read
through the session API (84 assistant records, 38 tool calls: 33 shell commands, 4 file writes, 1 connector
call). Only what the AI *asked for* was checked, not what the commands printed back.

| What was looked for | Found |
|---|---|
| Opening `hidden/` or `BTCUSDT_4h_full` | **None.** No command or path touches the hidden file. |
| `../` paths | **None** literally - but see the next row. |
| Working outside `fable/` | **Yes.** The session started in the project root, not inside `fable/`, so the folder lock in `fable/.claude/settings.json` never applied. It listed every file name in the repository (so it saw that `hidden/` exists), read the root settings file and ran `diff -r fable opus` (opus/ was still empty). |
| WebFetch / WebSearch | **None.** |
| `mcp__` tools | **One**: `list_computer_folders`, a check for a connected computer. It returns folder names only; nothing was attached. |
| bybit / binance / coingecko / yfinance / ccxt | **None.** No downloads, no pip installs, no URLs. |
| Dates in November 2025 or later | **None** as data. The only hits are `range(2020, 2026)`, a loop over the years 2020-2025. |
| Price files read | Only `data/BTCUSDT_4h_insample.csv`. |

Two more things a viewer should know:

1. **The AI already knows roughly what bitcoin did in the hidden year.** Fable's own FINAL.md says: "My training
   data runs past October 2025, so I have a rough idea of how BTC moved afterwards. I did not use it." The hidden
   candles were never shown to it, but the hidden year is not truly unknown to a model trained into 2026. Nothing
   in the logs can prove or disprove whether that knowledge shaped the picks.
2. **This exam session also set up the exam room.** It downloaded the hidden file, and before the exam it began
   (and was interrupted on) a Fable build of its own. None of that work was used: it was never committed, and the
   100 scored strategies come byte-for-byte from the separate session's commit. Two leftover files from it
   (`fable/research/build.py`, `fable/research/lab.py`) are still in `fable/` here because the exam is not allowed
   to edit that folder.
