# STL Tags Converter

A simple tool to convert old framework STL tags to new framework format.

## Features

- Convert `<tagd:style>` tags to `<tag:theme_prop>` format
- Clean, simple interface
- File upload support
- Download converted HTML

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Streamlit App (Recommended)

Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

Then open your browser to the URL shown (usually http://localhost:8501)

### HTML Version

Alternatively, open `converter.html` in your web browser.

## How It Works

The converter automatically transforms:
- `<tagd:style name="..." value="..." type="..." />` 
- Into: `<tag:theme_prop:... default="..." />`

All conversions happen automatically as you type or paste HTML.
