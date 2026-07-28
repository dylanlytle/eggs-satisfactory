# Efficiency Group for Guaranteed Satisfaction

**E.G.G.S.** - Cooperation is voluntary. Satisfaction is guaranteed.

A collaborative campaign handbook for a 4-8 player Satisfactory run.

The group edits one source file:

[`content/handbook.md`](content/handbook.md)

The PDF generator turns that Markdown into a printable handbook. GitHub Actions
also builds a fresh PDF whenever changes are pushed to `main` or proposed in a
pull request.

## Quick start

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/generate_pdf.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/generate_pdf.py
```

The generated file is:

```text
dist/EGGS_Operations_Handbook.pdf
```

To generate from a different source or choose another output path:

```bash
python scripts/generate_pdf.py \
  --source content/handbook.md \
  --output dist/my-campaign-handbook.pdf
```

## How the group should collaborate

1. Create a branch named after the change, such as `role/power-manager` or
   `rules/train-standard`.
2. Edit `content/handbook.md`.
3. Run the PDF generator locally if possible.
4. Commit the change and open a pull request.
5. Let at least one other player review changes to shared standards.
6. Merge the pull request after the automatic PDF build succeeds.

For a very casual workflow, GitHub's pencil-shaped **Edit this file** button is
enough. GitHub will offer to create a branch and pull request in the browser.

## Downloading an automatically generated PDF

1. Open the repository's **Actions** tab.
2. Select the latest successful **Build handbook PDF** run.
3. Download the `satisfactory-handbook` artifact.

The workflow also updates the PDF attached to tagged GitHub releases.

## Repository layout

```text
content/handbook.md       Editable campaign plan
scripts/generate_pdf.py   Markdown-to-PDF generator
dist/                     Locally generated handbook
.github/workflows/        Automatic PDF build
CONTRIBUTING.md           Suggested group-editing rules
requirements.txt          Python dependency
```

## Supported Markdown

The generator supports:

- Headings
- Paragraphs
- Bulleted and numbered lists
- Block quotes
- Simple Markdown tables
- Inline bold text, inline code, and links

Keep tables reasonably narrow so they remain readable on letter-sized pages.

## Game-data references

The handbook links to the
[Official Satisfactory Wiki](https://satisfactory.wiki.gg/) for current
milestones, Space Elevator requirements, foundations, the world grid, the map,
and the Dimensional Depot.
