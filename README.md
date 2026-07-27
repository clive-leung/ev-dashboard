# EV Ramp Dashboard

Interactive dashboard comparing production ramp trajectories for Tesla, Rivian, and Lucid Motors — aligned to each company's start of production (SOP).

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Dash](https://img.shields.io/badge/Dash-2.17-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## What it shows

- **Production & Delivery Volume** (bar charts) — quarterly vehicle output
- **Gross & Net Margin** (line charts) — profitability trajectory with dynamic y-axis
- **Key Insights** — auto-generated summary callouts per company
- **Add New Quarter** — upload an earnings PDF and AI extracts the numbers (requires API key)

Data sourced from public SEC 10-Q/10-K filings and earnings press releases.

## Quick Start

```bash
# Clone
git clone https://github.com/clive-leung/ev-dashboard.git
cd ev-dashboard

# Install
pip install -r requirements.txt

# Run
python app.py
```

Open http://localhost:8000 in your browser.

## PDF Upload (optional)

To enable AI-powered data extraction from earnings PDFs, set an OpenAI-compatible API key:

```bash
export OPENAI_API_KEY="sk-..."
export LLM_MODEL="gpt-4o-mini"          # optional, defaults to gpt-4o-mini
export OPENAI_BASE_URL="https://api.openai.com/v1"  # optional, any compatible endpoint
```

Without the API key, the dashboard works fine — you just can't auto-extract new quarters from PDFs.

## Deploy

**Render / Railway / Fly.io:**
```bash
gunicorn app:server --bind 0.0.0.0:8000 --workers 2
```

**Docker:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "app:server", "--bind", "0.0.0.0:8000", "--workers", "2"]
```

## Project Structure

```
app.py            # Main application (Dash + Plotly)
app.yaml          # Databricks Apps config (optional, for Databricks hosting)
requirements.txt  # Python dependencies
data.json         # Auto-generated at runtime (persists added quarters)
```

## Data

All margin values stored as ratios (e.g., 0.25 = 25%). Periods 0-2 excluded as early-production outliers. Each company's timeline is aligned to their SOP:

| Company | SOP | Period 3 starts |
| --- | --- | --- |
| Tesla | Jun 2012 (Model S) | Q1 2013 |
| Rivian | Sep 2021 (R1T) | Q2 2022 |
| Lucid | Oct 2021 (Air) | Q3 2022 |

## License

MIT
