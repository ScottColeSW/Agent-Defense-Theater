# Site

The static pages for Agent Defense Theater. No framework, no build step, no CDN. The page loads in one request plus two small JSON files.

## Start tests and read reports

Start the runner, which serves these pages and a small JSON API from your own machine:

```bash
python adt.py serve --open        # then open http://localhost:8765/start.html
```

| Page | What it does |
| --- | --- |
| [`start.html`](start.html) | The runner. Choose scripted, live preregistered, or live exploratory. Run every test or one. Watch progress, a live per-condition scoreboard, and the GPU cooldown panel. Cancel at any point. |
| [`report.html?run=<run_id>`](report.html) | The detailed report for one run: integrity of the decision log, summary by condition, prediction against result with the pass bar, where the time goes, the GPU timeline, where it held and where it did not, every reviewer decision with its request card, and every record. |

For live runs the start page shows a models table: size, what each model needs in memory, whether it fits the GPU, spills into system RAM, or will not fit, what is loaded now (with an Unload button), and a plan that updates as you tick models, with how many model swaps to expect. See [`../common/README.md`](../common/README.md).

A live run that would count as a result needs its prediction committed first, and the runner refuses without one and says why. Scripted runs are labeled and never results, and exploratory runs are labeled and kept outside the repository. A run that is cancelled or fails leaves no partial result behind. The runner is desktop only and binds to localhost.

On a static host there is no runner, so `start.html` says so and still lists the committed results, and their reports open from `data/reports/`. `python adt.py build` regenerates those files.

## Run it (static pages only)

The page reads its data with `fetch`, so serve the folder over HTTP. Opening `index.html` as a file will show a "could not load the data files" notice.

```bash
python -m http.server -d site 8765
```

Then open <http://localhost:8765/>.

## Files

| Path | Purpose |
| --- | --- |
| `index.html` | Home page: status, the range diagram, coverage matrix, ASI06 plots, how to read a result |
| `about.html`, `books.html` | About the author and Books. Linked from the top nav and the footer |
| `data/coverage.json` | The coverage matrix. Generated from [`../crosswalk/coverage.csv`](../crosswalk/coverage.csv) |
| `data/asi06-defenses.json` | Plot data for ASI06. Recomputed from the saved per-answer records |
| `start.html`, `report.html`, `assets/app.css`, `assets/app.js` | The runner and report pages, and their shared styles and scripts (no dependencies) |
| `data/reports/`, `data/tests.json` | Static copies of the committed results and the test list for hosts with no runner. Generated |
| `data/asi03-escalation.json` | Summary data for the ASI03 escalation experiment. Generated |
| `data/asi03.json` | Plot data for ASI03, from the preregistered runs, with the committed predictions beside the results |

The JSON files are generated. Do not edit them by hand.

## Rebuild the data

[`../tools/build_data.py`](../tools/build_data.py) is the only writer.

```bash
# coverage matrix only
python tools/build_data.py

# coverage plus the ASI06 plots, from a local Aegis Vector checkout
python tools/build_data.py --pav ../Project-Aegis-Vector
```

With `--pav` it also rewrites `items/asi06-memory-context-poisoning/results/pav-defenses.jsonl`. It recomputes adoption and utility from the per-answer records and exits with an error if the totals disagree with the figures Aegis Vector published for `none`, `gate_hold` and `layered`.

To change the matrix, edit `crosswalk/coverage.csv` and rebuild. The CSV is the source of truth.

## Rules for anything plotted here

- Plot only saved live runs. A scripted illustration may animate, and it carries a visible "scripted illustration" label.
- Show the denominator. Every bar says how many answers sit behind it, and percentages keep a decimal when the value is not whole.
- Show cost and retained utility next to attack success, never attack success alone.
- Name the source run and commit under the plot, and say who wrote the attacks.
- A result with no committed prediction is exploratory and says so. The ASI06 data predates this repository, which is why its `prereg` field points to Aegis Vector.

## Design

Dark slate palette and monospace type, matching Aegis Vector. Charts are hand-built SVG and CSS, so there is no charting library to download. Motion respects `prefers-reduced-motion`. The layout works down to phone width, and the heatmap scrolls sideways inside its card.

## Deploying

Everything in this folder is static. Publish the `site/` folder as-is (for example with GitHub Pages) after running the data build, and commit the generated `data/` files so the host needs no Python.
