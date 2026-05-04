# Kingdom Ink — KDP Cover Studio

A Streamlit app from **Kingdom Ink** that builds print-ready Amazon KDP paperback wraparound covers at 300 DPI from a separate front and back cover file. It calculates the spine width from your page count and paper type, composites the back / spine / front onto a single bleed-sized canvas, and exports a flattened PDF ready for upload.

## Branding assets

Drop the Kingdom Ink logo at `assets/logo.png` (transparent PNG recommended). The app falls back to a text wordmark if the file is missing. Theme colors live in `.streamlit/config.toml` — adjust there if you need to tweak the palette.

## Features

- Front and back cover uploads (PDF, PNG, or JPEG)
- Automatic spine width from page count + paper choice
  - White paper: `pages × 0.002252″`
  - Cream paper: `pages × 0.0025″`
- 0.125″ bleed handling, with edge-pixel replication when sources are trim-only
- Solid-color spine fill via color picker
- Live preview, spec summary, and one-click PDF download
- Spine-width warnings (too narrow for text / keep spine text minimal)

## Setup

### 1. System dependency: Poppler

`pdf2image` shells out to Poppler to rasterize PDF uploads. Install it for your OS before installing the Python packages.

**macOS (Homebrew):**

```bash
brew install poppler
```

**Ubuntu / Debian:**

```bash
sudo apt-get update && sudo apt-get install -y poppler-utils
```

**Windows:**

1. Download a Poppler build from <https://github.com/oschwartz10612/poppler-windows/releases/>.
2. Extract it (e.g. to `C:\Program Files\poppler`).
3. Add the extracted `bin\` folder to your `PATH`, or pass `poppler_path=` to `convert_from_bytes` in `app.py`.

Verify the install with `pdftoppm -v`.

### 2. Python environment

Python 3.10 or newer is recommended.

```bash
cd kdp-cover-generator
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

The app opens in your browser at <http://localhost:8501>.

## Using the app

1. **Upload covers.** Upload a front cover and a back cover in the sidebar.
2. **Enter book specs.** Trim width, trim height, page count, and paper type.
3. **Bleed setting.** Check *"Uploaded covers include bleed?"* if your source files already extend 0.125″ past the trim on the outside edges. Leave it unchecked if your files are sized to trim — the app will replicate the edge pixels outward to create the bleed.
4. **Pick a spine color.** Defaults to white. The spine panel is filled with this solid color.
5. **Generate cover.** Review the preview and the spec summary, then click *Download PDF*.

## Output specs

- 300 DPI flattened RGB PDF
- Canvas width: `trim_width × 2 + spine_width + 0.25″`
- Canvas height: `trim_height + 0.25″`
- JPEG-encoded internally at quality 95 with 4:4:4 chroma to keep small text crisp

## Project layout

```
kdp-cover-generator/
  app.py                      Streamlit UI + cover compositing
  requirements.txt            Python dependencies
  README.md                   This file
  assets/
    logo.png                  Kingdom Ink wordmark (you provide)
  .streamlit/
    config.toml               Theme + Streamlit settings
```

## Troubleshooting

- **"Unable to get page count" / PDFInfoNotInstalledError** — Poppler is not on `PATH`. Reinstall it (see step 1) and restart your shell.
- **PDF uploads look blurry** — they are rasterized at 300 DPI; if the source PDF is small, embed higher-resolution art before exporting.
- **Spine color appears different in the PDF viewer** — flat-color rendering can vary slightly across viewers; the actual file is RGB at the exact picked hex.
