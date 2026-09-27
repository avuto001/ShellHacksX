# Who owns what

Each person owns a set of files. **Only edit files you own.** That way, two people never change the same file at the same time, and GitHub never has to merge conflicting changes.

Replace "Teammate 1-4" with real names once you've decided who does what.

| Person | Role | Owns these files |
|---|---|---|
| **Teammate 1** | Stock data & home page | `my_stocks.py`<br>`pages/1_Stock_Detail.py`<br>`services/stock_data.py`<br>`utils/ui.py` |
| **Teammate 2** | AI summaries | `services/ai_summary.py` (except `answer_question`)<br>`pages/2_Daily_Summary.py` |
| **Teammate 3** | Risk math & charts | `services/risk.py`<br>`pages/3_Portfolio_Risk.py`<br>`tests/test_risk.py` |
| **Teammate 4** | AI safety, chat & accuracy | `services/security.py`<br>`pages/4_Ask_StockSense.py`<br>`answer_question()` in `services/ai_summary.py`<br>`eval/` |

## Shared files: ask in the group chat before changing

These files affect everyone. Post a quick message before you edit one, so nobody else edits it at the same time:

| File | Why it's shared |
|---|---|
| `utils/state.py` | Every page reads the portfolio from here |
| `requirements.txt` | After a change, everyone has to run `./setup.sh` again |
| `README.md`, `TEAM.md` | Team docs |
| `setup.sh`, `run.sh`, `.vscode/` | Everyone's setup |

## How the pieces connect

- **Teammate 1**'s Stock Detail page already shows the AI summary from `summarize_news()`. It will appear as soon as Teammate 2 builds that function, and nobody has to edit the page.
- **Teammate 2** and **Teammate 4** both use `clean_news_text()` from `services/security.py`. Teammate 4 builds it; Teammate 2 calls it on every headline before sending it to Claude.
- **Teammate 4** uses the headlines in `eval/` to check how accurate Teammate 2's summaries are.
- Need a new helper in a file you don't own? Ask its owner to add it, or agree in the chat first.
