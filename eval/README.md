# AI accuracy check

We want to know whether Claude judges news the way a person would. To find out, we're making a small answer key: about **30 real headlines**, each labeled by one of us.

## The file

`labeled_headlines.csv` has three columns:

| Column | What goes in it |
|---|---|
| `ticker` | The stock symbol, e.g. `AAPL` |
| `headline` | The exact headline text |
| `human_label` | Your judgment: `good`, `bad` or `neutral` for the stock |

There are 3 example rows to show the format.

## How to add headlines

1. Run the app and open **Stock Detail** for any stock.
2. Pick a headline and decide: is this news **good**, **bad** or **neutral** for the company's stock?
3. Add a row to the CSV. If the headline has a comma in it, wrap the whole headline in "double quotes".
4. Try to get a mix: roughly 10 good, 10 bad and 10 neutral, from several different companies.

Label based on the headline alone, and don't ask the AI first. That would defeat the point.

## How we'll use it

Once `services/ai_summary.py` works, we'll write a small script that asks Claude to label each headline and counts how often it agrees with us. For example, "Claude matched our label on 26 of 30 headlines (87%)." That gives us a real accuracy number for our presentation, and a way to tell whether a prompt change made things better or worse.
