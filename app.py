"""EV Ramp Dashboard"""
import os, json, base64, tempfile, logging
import pandas as pd
import plotly.graph_objects as go
import pdfplumber
from dash import Dash, html, dcc, callback, Input, Output, State, no_update

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

# LLM config - set these environment variables:
#   OPENAI_API_KEY  = your API key
#   OPENAI_BASE_URL = endpoint URL (defaults to https://api.openai.com/v1)
#   LLM_MODEL       = model name (defaults to gpt-4o-mini)
LLM_API_KEY = os.environ.get("OPENAI_API_KEY", "")
LLM_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

# ---------------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------------
SEED_DATA = [
    {"company":"Tesla","period":3,"quarter":"Q1 2013","production":5000,"deliveries":4900,"gross_margin":0.171,"net_margin":0.020},
    {"company":"Tesla","period":4,"quarter":"Q2 2013","production":6370,"deliveries":5150,"gross_margin":0.248,"net_margin":-0.075},
    {"company":"Tesla","period":5,"quarter":"Q3 2013","production":7150,"deliveries":5500,"gross_margin":0.238,"net_margin":-0.089},
    {"company":"Tesla","period":6,"quarter":"Q4 2013","production":6587,"deliveries":6892,"gross_margin":0.255,"net_margin":-0.026},
    {"company":"Tesla","period":7,"quarter":"Q1 2014","production":7535,"deliveries":6457,"gross_margin":0.250,"net_margin":-0.080},
    {"company":"Tesla","period":8,"quarter":"Q2 2014","production":8763,"deliveries":7579,"gross_margin":0.277,"net_margin":-0.080},
    {"company":"Tesla","period":9,"quarter":"Q3 2014","production":7075,"deliveries":7785,"gross_margin":0.296,"net_margin":-0.088},
    {"company":"Tesla","period":10,"quarter":"Q4 2014","production":11627,"deliveries":9834,"gross_margin":0.274,"net_margin":-0.113},
    {"company":"Tesla","period":11,"quarter":"Q1 2015","production":11160,"deliveries":10045,"gross_margin":0.277,"net_margin":-0.164},
    {"company":"Tesla","period":12,"quarter":"Q2 2015","production":12807,"deliveries":11532,"gross_margin":0.223,"net_margin":-0.193},
    {"company":"Tesla","period":13,"quarter":"Q3 2015","production":13091,"deliveries":11603,"gross_margin":0.247,"net_margin":-0.243},
    {"company":"Tesla","period":14,"quarter":"Q4 2015","production":14037,"deliveries":17478,"gross_margin":0.180,"net_margin":-0.264},
    {"company":"Tesla","period":15,"quarter":"Q1 2016","production":15510,"deliveries":14810,"gross_margin":0.220,"net_margin":-0.246},
    {"company":"Tesla","period":16,"quarter":"Q2 2016","production":18345,"deliveries":14402,"gross_margin":0.216,"net_margin":-0.231},
    {"company":"Tesla","period":17,"quarter":"Q3 2016","production":25185,"deliveries":24821,"gross_margin":0.277,"net_margin":0.010},
    {"company":"Tesla","period":18,"quarter":"Q4 2016","production":24882,"deliveries":22252,"gross_margin":0.191,"net_margin":-0.096},
    {"company":"Rivian","period":3,"quarter":"Q2 2022","production":4401,"deliveries":4467,"gross_margin":-1.934,"net_margin":-4.703},
    {"company":"Rivian","period":4,"quarter":"Q3 2022","production":7363,"deliveries":6584,"gross_margin":-1.711,"net_margin":-3.216},
    {"company":"Rivian","period":5,"quarter":"Q4 2022","production":10020,"deliveries":8054,"gross_margin":-1.508,"net_margin":-2.599},
    {"company":"Rivian","period":6,"quarter":"Q1 2023","production":9395,"deliveries":7946,"gross_margin":-0.809,"net_margin":-2.041},
    {"company":"Rivian","period":7,"quarter":"Q2 2023","production":13992,"deliveries":12640,"gross_margin":-0.368,"net_margin":-1.066},
    {"company":"Rivian","period":8,"quarter":"Q3 2023","production":16304,"deliveries":15564,"gross_margin":-0.357,"net_margin":-1.022},
    {"company":"Rivian","period":9,"quarter":"Q4 2023","production":17541,"deliveries":13972,"gross_margin":-0.461,"net_margin":-1.157},
    {"company":"Rivian","period":10,"quarter":"Q1 2024","production":13980,"deliveries":13588,"gross_margin":-0.438,"net_margin":-1.201},
    {"company":"Rivian","period":11,"quarter":"Q2 2024","production":9612,"deliveries":13790,"gross_margin":-0.389,"net_margin":-1.258},
    {"company":"Rivian","period":12,"quarter":"Q3 2024","production":13157,"deliveries":10018,"gross_margin":-0.449,"net_margin":-1.338},
    {"company":"Rivian","period":13,"quarter":"Q4 2024","production":12727,"deliveries":14183,"gross_margin":0.098,"net_margin":-0.428},
    {"company":"Rivian","period":14,"quarter":"Q1 2025","production":14611,"deliveries":8640,"gross_margin":0.166,"net_margin":-0.440},
    {"company":"Rivian","period":15,"quarter":"Q2 2025","production":5979,"deliveries":10661,"gross_margin":-0.158,"net_margin":-0.856},
    {"company":"Rivian","period":16,"quarter":"Q3 2025","production":10720,"deliveries":13201,"gross_margin":0.015,"net_margin":-0.748},
    {"company":"Rivian","period":17,"quarter":"Q4 2025","production":10974,"deliveries":9745,"gross_margin":0.093,"net_margin":-0.625},
    {"company":"Lucid","period":3,"quarter":"Q3 2022","production":2282,"deliveries":1398,"gross_margin":-1.520,"net_margin":-2.712},
    {"company":"Lucid","period":4,"quarter":"Q4 2022","production":3493,"deliveries":1932,"gross_margin":-1.388,"net_margin":-1.834},
    {"company":"Lucid","period":5,"quarter":"Q1 2023","production":2314,"deliveries":1406,"gross_margin":-2.350,"net_margin":-5.217},
    {"company":"Lucid","period":6,"quarter":"Q2 2023","production":2173,"deliveries":1404,"gross_margin":-2.684,"net_margin":-5.065},
    {"company":"Lucid","period":7,"quarter":"Q3 2023","production":1550,"deliveries":1457,"gross_margin":-2.408,"net_margin":-4.578},
    {"company":"Lucid","period":8,"quarter":"Q4 2023","production":2391,"deliveries":1734,"gross_margin":-1.609,"net_margin":-4.160},
    {"company":"Lucid","period":9,"quarter":"Q1 2024","production":1727,"deliveries":1967,"gross_margin":-1.343,"net_margin":-3.964},
    {"company":"Lucid","period":10,"quarter":"Q2 2024","production":2110,"deliveries":2394,"gross_margin":-1.345,"net_margin":-3.208},
    {"company":"Lucid","period":11,"quarter":"Q3 2024","production":1805,"deliveries":2781,"gross_margin":-1.062,"net_margin":-3.852},
    {"company":"Lucid","period":12,"quarter":"Q4 2024","production":3386,"deliveries":3099,"gross_margin":-0.890,"net_margin":-2.716},
    {"company":"Lucid","period":13,"quarter":"Q1 2025","production":2212,"deliveries":3109,"gross_margin":-0.972,"net_margin":-3.110},
    {"company":"Lucid","period":14,"quarter":"Q2 2025","production":3863,"deliveries":3309,"gross_margin":-1.050,"net_margin":-2.079},
    {"company":"Lucid","period":15,"quarter":"Q3 2025","production":3891,"deliveries":4078,"gross_margin":-0.991,"net_margin":-2.907},
    {"company":"Lucid","period":16,"quarter":"Q4 2025","production":7874,"deliveries":5345,"gross_margin":-0.807,"net_margin":-1.557},
]

# ---------------------------------------------------------------------------
# PERSISTENCE
# ---------------------------------------------------------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    save_data(SEED_DATA)
    return SEED_DATA

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_quarter(data, new_entry):
    data = [d for d in data if not (d["company"] == new_entry["company"] and d["quarter"] == new_entry["quarter"])]
    data.append(new_entry)
    data.sort(key=lambda x: (x["company"], x["period"]))
    save_data(data)
    return data

# ---------------------------------------------------------------------------
# PDF + LLM EXTRACTION
# ---------------------------------------------------------------------------
def extract_text_from_pdf(pdf_bytes):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name
    try:
        text = ""
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        return text
    finally:
        os.unlink(tmp_path)


def extract_data_with_llm(pdf_text, company_hint=None):
    """Call OpenAI-compatible API. Set OPENAI_API_KEY env var."""
    import requests

    if not LLM_API_KEY:
        return None, "No API key configured. Set OPENAI_API_KEY environment variable."

    prompt = f"""Extract quarterly financial data from this EV company earnings document.
Return ONLY valid JSON (no markdown, no explanation):
{{
  "company": "Tesla" or "Rivian" or "Lucid",
  "quarter": "Q1 2026" (format: Q# YYYY),
  "production": <integer, total vehicles produced>,
  "deliveries": <integer, total vehicles delivered>,
  "gross_margin": <decimal ratio, e.g. 0.25 for 25%>,
  "net_margin": <decimal ratio, e.g. -0.08 for -8%>
}}

Rules:
- gross_margin = (Revenue - Cost of Revenue) / Revenue
- net_margin = Net Income / Revenue
- Express as decimal ratios NOT percentages
- Company hint: {company_hint or "detect from content"}

Text:
{pdf_text[:8000]}"""

    try:
        resp = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
            json={"model": LLM_MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 300, "temperature": 0.0},
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        if "```" in content:
            content = content.split("```")[1].lstrip("json")
        return json.loads(content.strip()), None
    except requests.exceptions.HTTPError as e:
        return None, f"LLM API error {e.response.status_code}: {e.response.text[:200]}"
    except Exception as e:
        return None, f"LLM error: {str(e)[:200]}"

# ---------------------------------------------------------------------------
# DESIGN
# ---------------------------------------------------------------------------
COLORS = {"Tesla": "#E8272C", "Rivian": "#E5A000", "Lucid": "#444444"}
PAGE_BG = "#f7f8fa"; CARD_BG = "#ffffff"; TEXT_DARK = "#1f2937"
TEXT_MED = "#4b5563"; TEXT_LIGHT = "#6b7280"; BORDER = "#e5e7eb"

# ---------------------------------------------------------------------------
# SUMMARIES
# ---------------------------------------------------------------------------
def compute_summaries(data):
    df = pd.DataFrame(data)
    t = df[df["company"] == "Tesla"].sort_values("period")
    t_peak = t["production"].max()
    t_peak_q = t.loc[t["production"].idxmax(), "quarter"]
    r = df[df["company"] == "Rivian"].sort_values("period")
    r_gm_pos = r[r["gross_margin"] > 0]
    r_first_pos = r_gm_pos.iloc[0]["quarter"] if not r_gm_pos.empty else None
    r_peak = r["production"].max()
    l = df[df["company"] == "Lucid"].sort_values("period")
    l_del = int(l.iloc[-1]["deliveries"]); l_q = l.iloc[-1]["quarter"]
    l_gm = l.iloc[-1]["gross_margin"] * 100
    return {
        "tesla": f"Tesla ramped to {t_peak:,} vehicles/qtr by {t_peak_q}, sustaining 20\u201328% gross margins throughout.",
        "rivian": f"Rivian turned gross-margin positive in {r_first_pos}, peaking at {r_peak:,} vehicles produced in a single quarter." if r_first_pos else f"Rivian peaked at {r_peak:,}/qtr but hasn\u2019t hit positive gross margin.",
        "lucid": f"Lucid delivered {l_del:,} in {l_q} with gross margin at {l_gm:.0f}% \u2014 still burning cash per vehicle.",
    }

# ---------------------------------------------------------------------------
# CHARTS
# ---------------------------------------------------------------------------
def chart_layout(title, yaxis_title, yrange=None):
    d = dict(
        title=dict(text=title, x=0.01, xanchor="left", font=dict(size=15, color=TEXT_DARK, family=FONT)),
        xaxis=dict(title=None, showgrid=False, zeroline=False, dtick=3, tickfont=dict(size=11, color=TEXT_LIGHT, family=FONT), showline=True, linecolor=BORDER),
        yaxis=dict(title=dict(text=yaxis_title, font=dict(size=11, color=TEXT_LIGHT, family=FONT)), showgrid=False, zeroline=True, zerolinecolor="#d1d5db", zerolinewidth=1.5, tickfont=dict(size=11, color=TEXT_LIGHT, family=FONT)),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
        margin=dict(l=50, r=10, t=35, b=25), hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_size=12, font_family=FONT, bordercolor=BORDER),
    )
    if yrange:
        d["yaxis"]["range"] = yrange
    return d


def build_figures(data):
    df = pd.DataFrame(data)
    df["gm_pct"] = df["gross_margin"] * 100
    df["nm_pct"] = df["net_margin"] * 100
    gm_min, gm_max = df["gm_pct"].min(), df["gm_pct"].max()
    nm_min, nm_max = df["nm_pct"].min(), df["nm_pct"].max()
    gm_range = [gm_min - abs(gm_min) * 0.1 - 5, gm_max + abs(gm_max) * 0.1 + 5]
    nm_range = [nm_min - abs(nm_min) * 0.1 - 5, nm_max + abs(nm_max) * 0.1 + 5]
    figs = {}
    for cid, metric, title, yax, is_bar, yr in [
        ("prod", "production", "Production Volume", "vehicles", True, None),
        ("del", "deliveries", "Delivery Volume", "vehicles", True, None),
        ("gm", "gm_pct", "Gross Margin", "%", False, gm_range),
        ("nm", "nm_pct", "Net Margin", "%", False, nm_range),
    ]:
        fig = go.Figure()
        for co in ["Tesla", "Rivian", "Lucid"]:
            cdf = df[df["company"] == co].sort_values("period")
            if cdf.empty:
                continue
            if is_bar:
                fig.add_trace(go.Bar(x=cdf["period"], y=cdf[metric], name=co, marker_color=COLORS[co], marker_line_width=0, hovertemplate=f"<b>{co}</b> (%{{customdata}})<br>%{{y:,.0f}}<extra></extra>", customdata=cdf["quarter"]))
            else:
                fig.add_trace(go.Scatter(x=cdf["period"], y=cdf[metric], mode="lines+markers", name=co, line=dict(color=COLORS[co], width=2.5), marker=dict(size=4), hovertemplate=f"<b>{co}</b> (%{{customdata}})<br>%{{y:.1f}}%<extra></extra>", customdata=cdf["quarter"]))
            last = cdf.iloc[-1]
            fv = f"{last[metric]:,.0f}" if is_bar else f"{last[metric]:.0f}%"
            fig.add_annotation(x=last["period"], y=last[metric], text=f"<b>{fv}</b>", showarrow=False, font=dict(size=11, color=COLORS[co], family=FONT), yshift=14)
        fig.update_layout(**chart_layout(title, yax, yr))
        if is_bar:
            fig.update_layout(barmode="group", bargap=0.15, bargroupgap=0.05)
        figs[cid] = fig
    return figs

# ---------------------------------------------------------------------------
# APP
# ---------------------------------------------------------------------------
app = Dash(__name__)
server = app.server
app.title = "EV Ramp Dashboard"

app.index_string = '''<!DOCTYPE html>
<html>
<head>
{%metas%}<title>{%title%}</title>{%favicon%}{%css%}
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; }
body { margin: 0; background: ''' + PAGE_BG + '''; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
.processing { animation: pulse 1.5s ease-in-out infinite; }
</style>
</head>
<body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body>
</html>'''

card = {"backgroundColor": CARD_BG, "borderRadius": "8px", "padding": "14px 16px 6px 16px", "border": f"1px solid {BORDER}"}
pill = {"display": "inline-flex", "alignItems": "center", "gap": "6px", "padding": "4px 12px", "borderRadius": "20px", "backgroundColor": "#f3f4f6", "border": f"1px solid {BORDER}"}

init_data = load_data()
init_figs = build_figures(init_data)
summaries = compute_summaries(init_data)

app.layout = html.Div(style={"fontFamily": FONT, "maxWidth": "1500px", "margin": "0 auto", "padding": "20px 24px"}, children=[
    dcc.Store(id="data-store", data=init_data),
    # HEADER
    html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "12px", "flexWrap": "wrap", "gap": "10px"}, children=[
        html.Div([
            html.H1("EV Ramp Dashboard", style={"fontSize": "26px", "fontWeight": "800", "color": TEXT_DARK, "margin": "0", "letterSpacing": "-0.5px"}),
            html.P("Production ramp comparison aligned to start of production", style={"fontSize": "14px", "color": TEXT_LIGHT, "margin": "2px 0 0 0"}),
        ]),
        html.Div(style={"display": "flex", "gap": "8px", "flexWrap": "wrap"}, children=[
            html.Div(style=pill, children=[html.Div(style={"width": "10px", "height": "10px", "borderRadius": "50%", "backgroundColor": COLORS["Tesla"]}), html.Span("Tesla", style={"fontSize": "13px", "fontWeight": "600", "color": TEXT_DARK}), html.Span("Jun 2012", style={"fontSize": "12px", "color": TEXT_LIGHT})]),
            html.Div(style=pill, children=[html.Div(style={"width": "10px", "height": "10px", "borderRadius": "50%", "backgroundColor": COLORS["Rivian"]}), html.Span("Rivian", style={"fontSize": "13px", "fontWeight": "600", "color": TEXT_DARK}), html.Span("Sep 2021", style={"fontSize": "12px", "color": TEXT_LIGHT})]),
            html.Div(style=pill, children=[html.Div(style={"width": "10px", "height": "10px", "borderRadius": "50%", "backgroundColor": COLORS["Lucid"]}), html.Span("Lucid", style={"fontSize": "13px", "fontWeight": "600", "color": TEXT_DARK}), html.Span("Oct 2021", style={"fontSize": "12px", "color": TEXT_LIGHT})]),
        ]),
    ]),
    # INSIGHT CALLOUTS
    html.Div(style={"display": "flex", "gap": "14px", "marginBottom": "14px", "flexWrap": "wrap"}, children=[
        html.Div(style={"flex": "1", "minWidth": "280px", "padding": "12px 16px", "backgroundColor": CARD_BG, "borderRadius": "8px", "borderLeft": f"4px solid {COLORS['Tesla']}"}, children=[
            html.Div(summaries["tesla"], style={"fontSize": "13px", "color": TEXT_DARK, "lineHeight": "1.5", "fontWeight": "500"}),
        ]),
        html.Div(style={"flex": "1", "minWidth": "280px", "padding": "12px 16px", "backgroundColor": CARD_BG, "borderRadius": "8px", "borderLeft": f"4px solid {COLORS['Rivian']}"}, children=[
            html.Div(summaries["rivian"], style={"fontSize": "13px", "color": TEXT_DARK, "lineHeight": "1.5", "fontWeight": "500"}),
        ]),
        html.Div(style={"flex": "1", "minWidth": "280px", "padding": "12px 16px", "backgroundColor": CARD_BG, "borderRadius": "8px", "borderLeft": f"4px solid {COLORS['Lucid']}"}, children=[
            html.Div(summaries["lucid"], style={"fontSize": "13px", "color": TEXT_DARK, "lineHeight": "1.5", "fontWeight": "500"}),
        ]),
    ]),
    # CHARTS 2x2
    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "14px"}, children=[
        html.Div(style=card, children=[dcc.Graph(id="chart-prod", figure=init_figs["prod"], config={"displayModeBar": False}, style={"height": "calc(50vh - 130px)", "minHeight": "200px"})]),
        html.Div(style=card, children=[dcc.Graph(id="chart-del", figure=init_figs["del"], config={"displayModeBar": False}, style={"height": "calc(50vh - 130px)", "minHeight": "200px"})]),
        html.Div(style=card, children=[dcc.Graph(id="chart-gm", figure=init_figs["gm"], config={"displayModeBar": False}, style={"height": "calc(50vh - 130px)", "minHeight": "200px"})]),
        html.Div(style=card, children=[dcc.Graph(id="chart-nm", figure=init_figs["nm"], config={"displayModeBar": False}, style={"height": "calc(50vh - 130px)", "minHeight": "200px"})]),
    ]),
    # SOURCE
    html.Div(style={"marginTop": "10px", "display": "flex", "justifyContent": "space-between"}, children=[
        html.Span("Source: Public SEC filings & earnings reports", style={"fontSize": "11px", "color": TEXT_LIGHT}),
        html.Span("X-axis = quarters since start of production", style={"fontSize": "11px", "color": TEXT_LIGHT}),
    ]),
    # ADD QUARTER (hidden at bottom)
    html.Details(style={"marginTop": "32px"}, children=[
        html.Summary("Add new quarter", style={"fontSize": "12px", "color": TEXT_LIGHT, "cursor": "pointer"}),
        html.Div(style={"marginTop": "10px", "padding": "14px", "border": f"1px solid {BORDER}", "borderRadius": "8px", "backgroundColor": CARD_BG}, children=[
            html.P("Upload an earnings press release PDF. AI extracts production, deliveries, and margins.",
                   style={"fontSize": "13px", "color": TEXT_MED, "margin": "0 0 10px 0"}),
            html.Div(style={"display": "flex", "gap": "12px", "alignItems": "center", "flexWrap": "wrap"}, children=[
                dcc.Upload(
                    id="pdf-upload",
                    children=html.Div(["Drop PDF or ", html.Span("browse", style={"color": "#2563eb", "textDecoration": "underline"})]),
                    style={"border": f"2px dashed {BORDER}", "borderRadius": "8px", "padding": "14px 24px",
                           "textAlign": "center", "cursor": "pointer", "backgroundColor": "#fafbfc", "fontSize": "14px"},
                    multiple=False, accept=".pdf",
                ),
                # Loading spinner wraps the status
                dcc.Loading(
                    id="upload-loading",
                    type="circle",
                    color="#2563eb",
                    children=[html.Div(id="upload-status", style={"fontSize": "13px", "minHeight": "20px"})],
                ),
            ]),
            # Config hint
            html.Div(
                f"LLM: {LLM_MODEL} @ {LLM_BASE_URL.split('//')[-1][:40]}" if LLM_API_KEY else "\u26a0\ufe0f Set OPENAI_API_KEY env var to enable AI extraction",
                style={"fontSize": "11px", "color": TEXT_LIGHT, "marginTop": "10px"},
            ),
        ]),
    ]),
])

# ---------------------------------------------------------------------------
# CALLBACKS
# ---------------------------------------------------------------------------
@callback(
    Output("chart-prod", "figure"), Output("chart-del", "figure"),
    Output("chart-gm", "figure"), Output("chart-nm", "figure"),
    Output("upload-status", "children"), Output("data-store", "data"),
    Input("pdf-upload", "contents"),
    State("pdf-upload", "filename"), State("data-store", "data"),
    prevent_initial_call=True,
)
def process_upload(contents, filename, current_data):
    if contents is None:
        return no_update

    # Step 1: Decode PDF
    try:
        _, cs = contents.split(",")
        pdf_bytes = base64.b64decode(cs)
    except Exception:
        return no_update, no_update, no_update, no_update, html.Span("\u274c Invalid file format.", style={"color": "#dc2626"}), no_update

    # Step 2: Extract text
    pdf_text = extract_text_from_pdf(pdf_bytes)
    if not pdf_text or len(pdf_text.strip()) < 100:
        return no_update, no_update, no_update, no_update, html.Span("\u274c Could not extract text from PDF.", style={"color": "#dc2626"}), no_update

    log.info(f"Extracted {len(pdf_text)} chars from {filename}")

    # Step 3: Detect company from filename
    hint = None
    fn = (filename or "").lower()
    if "tesla" in fn or "tsla" in fn: hint = "Tesla"
    elif "rivian" in fn or "rivn" in fn: hint = "Rivian"
    elif "lucid" in fn or "lcid" in fn: hint = "Lucid"

    # Step 4: LLM extraction
    extracted, error = extract_data_with_llm(pdf_text, hint)
    if error:
        log.error(f"LLM error: {error}")
        return no_update, no_update, no_update, no_update, html.Span(f"\u274c {error}", style={"color": "#dc2626", "fontSize": "12px"}), no_update
    if not extracted:
        return no_update, no_update, no_update, no_update, html.Span("\u274c Extraction returned empty.", style={"color": "#dc2626"}), no_update

    # Step 5: Assign period and save
    co = extracted["company"]
    eq = {d["quarter"]: d["period"] for d in current_data if d["company"] == co}
    ep = [d["period"] for d in current_data if d["company"] == co]
    extracted["period"] = eq.get(extracted["quarter"], max(ep) + 1 if ep else 3)

    new_data = add_quarter(current_data, extracted)
    figs = build_figures(new_data)

    msg = f"\u2705 Added: {co} {extracted['quarter']} \u2014 Prod: {extracted['production']:,}, Del: {extracted['deliveries']:,}, GM: {extracted['gross_margin']*100:.1f}%"
    return figs["prod"], figs["del"], figs["gm"], figs["nm"], html.Span(msg, style={"color": "#16a34a", "fontWeight": "500"}), new_data


if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("DATABRICKS_APP_PORT", 8000)))
    app.run(debug=False, host="0.0.0.0", port=port)
