# Pro Data Analysis Pipeline

This pipeline turns a finished Pro Data Analysis PDF into the CMS handoff files your team usually makes by hand.

## What it generates

- Canonical PDF copy named `YYYYMMDD-slug-lastname.pdf`
- Main JPEG named `YYYYMMDD-slug-lastname.jpg`
- Email JPEG named `EMAIL-YYYYMMDD-slug-lastname.jpg`
- PowerPoint deck named `YYYYMMDD-slug-lastname.pptx`

## Run it

Install JavaScript dependencies once:

```bash
npm install
```

Run the pipeline on one PDF:

```bash
uv run pro-data-analysis test_cases/where-the-dhs-shutdown-hit-hardest.pdf
```

## Install the Finder Quick Action

Run:

```bash
./scripts/install_quick_action.sh
```

That writes a Quick Action into `~/Library/Services` so you can right-click a PDF in Finder.
