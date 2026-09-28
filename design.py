"""Identidad visual de Tu Lado B."""
import streamlit as st


def apply_design():
    st.markdown('''<style>
    [data-testid="stToolbar"] {display:none;}
    [data-testid="stFileUploaderDropzone"] button * {display:none;}
    [data-testid="stFileUploaderDropzone"] button {font-size:0;}
    [data-testid="stFileUploaderDropzone"] button::after {content:"Seleccionar archivos"; font-size:14px;}
    [data-testid="stFileUploaderDropzone"] small, [data-testid="stFileUploaderDropzoneInstructions"] {display:none;}
    .stApp {background: radial-gradient(ellipse at 8% 0%, #123b27 0%, #101412 35%, #0b0d0c 75%); color:#f5f7f5;}
    [data-testid="stHeader"] {background:rgba(11,13,12,.92);}
    .block-container {max-width:1450px; padding-top:2rem; padding-bottom:4rem;}
    h1,h2,h3 {letter-spacing:-.035em; color:#f7faf7;}
    [data-testid="stCaptionContainer"] {color:#b0bcb4;}
    [data-testid="stMetric"] {background:linear-gradient(135deg,#203429,#17231c); border:1px solid #34533e; border-radius:18px; padding:20px; min-height:126px;}
    [data-testid="stMetricValue"] {color:#fff; font-weight:800;}
    [data-testid="stMetricLabel"] {color:#bed0c3;}
    [data-testid="stVerticalBlockBorderWrapper"] {border-radius:20px;}
    [data-testid="stFileUploaderDropzone"] {background:#17261d; border:1px dashed #4c8a60; border-radius:16px; padding:24px;}
    [data-baseweb="tab-list"] {gap:8px; overflow-x:auto; padding:12px 0; border-bottom:1px solid #2a3b30;}
    button[data-baseweb="tab"] {background:#1b241f; border-radius:24px; padding:10px 18px; color:#d7e0da; white-space:nowrap;}
    button[data-baseweb="tab"][aria-selected="true"] {background:#1ed760; color:#07150b; font-weight:800;}
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {display:none;}
    button[kind="primary"], [data-testid="stDownloadButton"] button {background:#1ed760; color:#07150b; border:0; border-radius:28px; font-weight:800; padding:.65rem 1.4rem;}
    button[kind="primary"]:hover, [data-testid="stDownloadButton"] button:hover {background:#65ed91; color:#07150b;}
    button:focus-visible {outline:3px solid #b5f56b !important; outline-offset:3px;}
    [data-testid="stExpander"] {background:#142019; border-radius:16px;}
    [data-testid="stPlotlyChart"] {border:1px solid #2b3d31; border-radius:20px; overflow:hidden; margin:10px 0 18px;}
    [data-testid="stImage"] img {border-radius:20px;}
    .persona-hero {position:relative; overflow:hidden; padding:38px; border:1px solid #396348; border-radius:28px; margin-bottom:24px; background:linear-gradient(115deg,#205635,#13291c 65%,#14251a);}
    .persona-hero:after {content:'♫'; position:absolute; right:32px; top:-55px; font-size:260px; color:#1ed760; opacity:.13; transform:rotate(-12deg); pointer-events:none;}
    .persona-kicker {font-size:12px; font-weight:800; letter-spacing:.2em; color:#98f9b5;}
    .persona-hero h1 {font-size:clamp(36px,5vw,66px); margin:10px 0 6px; line-height:1.08; font-weight:900;}
    .persona-hero p {font-size:18px; color:#d6e5da; max-width:760px; margin-bottom:20px;}
    .persona-chip {display:inline-block; border:1px solid #58906a; border-radius:30px; padding:6px 12px; margin:4px 6px 0 0; font-size:12px; color:#d8efdf; background:#12321f;}
    .persona-footer {margin-top:32px; color:#91a698; font-size:12px; border-top:1px solid #2b3d31; padding-top:18px;}
    @media(max-width:700px) {.block-container {padding-left:1rem; padding-right:1rem;} .persona-hero {padding:24px;} .persona-hero p {font-size:16px;} [data-testid="stMetric"] {padding:14px; min-height:110px;} }
    </style>''', unsafe_allow_html=True)


def hero():
    st.markdown('''<section class="persona-hero">
    <div class="persona-kicker">TU MÚSICA TIENE MUCHO QUE CONTAR</div>
    <h1>Tu Lado B<span style="color:#1ed760">.</span></h1>
    <p>Los hábitos y obsesiones que tu historial esconde.</p>
    <span class="persona-chip">Tu historial completo</span><span class="persona-chip">5 arquetipos · una identidad</span><span class="persona-chip">Tu resumen listo para compartir</span>
    </section>''', unsafe_allow_html=True)


def chart(fig, **kwargs):
    from rich_charts import polish
    # Apply the same appearance to old and new charts without replacing their data.
    old_hover = fig.layout.hovermode
    polish(fig, fig.layout.height or 450)
    if old_hover:
        fig.update_layout(hovermode=old_hover)
    fig.update_layout(separators='.,')
    kwargs.setdefault('theme', None)
    kwargs.setdefault('config', {'displaylogo': False, 'displayModeBar': False, 'responsive': True})
    st.plotly_chart(fig, **kwargs)
