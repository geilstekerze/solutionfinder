import streamlit as st
import streamlit.components.v1 as components
import math
import base64
import os
from fpdf import FPDF

def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def inject_apple_icon():
    if os.path.exists('Solutionfinder.jpeg'):
        try:
            b64 = get_base64('Solutionfinder.jpeg')
            components.html(f"""
                <script>
                (function() {{
                    var p = parent.document;
                    if (!p.querySelector('link[rel="apple-touch-icon"]')) {{
                        var l = p.createElement('link');
                        l.rel = 'apple-touch-icon';
                        l.href = 'data:image/jpeg;base64,{b64}';
                        p.head.appendChild(l);
                    }}
                    [['mobile-web-app-capable','yes'],
                     ['apple-mobile-web-app-capable','yes'],
                     ['apple-mobile-web-app-title','Solutionfinder']
                    ].forEach(function(d) {{
                        var m = p.createElement('meta');
                        m.name = d[0]; m.content = d[1];
                        p.head.appendChild(m);
                    }});
                }})();
                </script>
            """, height=0)
        except:
            pass

def get_logo_html(height="75px"):
    for fname in ['Logo.png', 'Logo.jpg', 'Logo.jpeg', 'logo.png', 'logo.jpg']:
        if os.path.exists(fname):
            try:
                ext = fname.rsplit('.', 1)[1].lower()
                mime = 'jpeg' if ext in ('jpg', 'jpeg') else 'png'
                b64 = get_base64(fname)
                return (f'<img src="data:image/{mime};base64,{b64}" '
                        f'style="height:{height};max-width:300px;'
                        f'object-fit:contain;display:block;margin:0 auto;">')
            except:
                pass
    # SVG-Fallback bis Logo.png hochgeladen wird
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 370 118" '
            f'style="height:{height};display:block;margin:0 auto;">'
            f'<text x="4" y="82" font-family="Arial Black,Arial,sans-serif" '
            f'font-weight="900" font-style="italic" font-size="86" fill="#E8471C">Rieber</text>'
            f'<text x="10" y="112" font-family="Arial,sans-serif" font-weight="300" '
            f'font-size="19" fill="#aaaaaa" letter-spacing="7">M E T A  cooking</text>'
            f'</svg>')

HIDE_ST = """
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none !important; }
    header[data-testid="stHeader"] { background: transparent; }
    [data-testid="manage-app-button"] { display: none !important; }
"""

FORM_BORDERS = """
    div[data-baseweb="select"] > div {
        border: 2px solid #E8471C !important;
        border-radius: 10px !important;
        background-color: white !important;
    }
    div[data-baseweb="input"] > div {
        border: 2px solid #E8471C !important;
        border-radius: 10px !important;
        background-color: white !important;
    }
    div[data-baseweb="base-input"] { background-color: white !important; }
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="input"] > div:focus-within {
        border-color: #E8471C !important;
        box-shadow: 0 0 0 2px rgba(232,71,28,0.15) !important;
    }
"""

def set_design():
    logo_html = get_logo_html("75px")
    st.markdown(f'''
        <style>
        {HIDE_ST}
        .stApp {{ background-color: #f0f2f5; }}
        .block-container {{ padding-top: 1.5rem !important; }}

        .rieber-header {{
            background: white; text-align: center;
            padding: 28px 20px 22px; border-radius: 16px;
            margin-bottom: 24px; box-shadow: 0 2px 10px rgba(0,0,0,0.07);
        }}
        .app-name {{
            font-size: 1.05em; font-weight: 700; color: #333;
            letter-spacing: 0.1em; text-transform: uppercase;
            margin-top: 16px; padding-top: 14px; border-top: 1px solid #f0f0f0;
        }}
        .eingabe-box {{
            background: #fff; padding: 28px; border-radius: 16px;
            border: none; margin-bottom: 24px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.07);
        }}
        .section-label {{
            font-size: 0.75em; font-weight: 700; letter-spacing: 0.15em;
            color: #999; text-transform: uppercase; margin: 8px 0 4px;
        }}
        {FORM_BORDERS}
        .result-card {{
            background: #fff; padding: 22px 16px; border-radius: 16px;
            border: 2px solid #E8471C; text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 16px;
        }}
        .metric-title {{
            color: #888; font-weight: 600; font-size: 0.82em;
            margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.6px;
        }}
        .metric-value {{ font-size: 2.4em; font-weight: 800; color: #1a1a1a; line-height: 1; }}
        .metric-price {{ font-size: 0.92em; color: #E8471C; font-weight: 600; margin-top: 10px; }}
        .total-card {{
            background: #E8471C; color: white; text-align: center;
            padding: 22px 24px; border-radius: 16px; margin: 20px 0 28px;
        }}
        .total-label {{
            font-size: 0.82em; font-weight: 600; letter-spacing: 0.12em;
            text-transform: uppercase; opacity: 0.9; margin-bottom: 6px;
        }}
        .total-value {{ font-size: 2.2em; font-weight: 900; }}
        .roi-card, .esg-card {{
            background: #fff; border: 2px solid #E8471C; text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            padding: 20px 16px; border-radius: 16px; margin-bottom: 12px;
        }}
        .card-icon {{ font-size: 2em; margin-bottom: 6px; line-height: 1.2; }}
        .stDownloadButton > button, .stButton > button {{
            background-color: #E8471C !important; color: white !important;
            font-weight: 700 !important; width: 100% !important;
            border: none !important; border-radius: 12px !important;
            padding: 14px 24px !important; font-size: 1em !important;
            letter-spacing: 0.04em !important;
            box-shadow: 0 4px 12px rgba(232,71,28,0.3) !important;
        }}
        </style>
        <div class="rieber-header">
            {logo_html}
            <div class="app-name">Solution<strong>finder</strong></div>
        </div>
    ''', unsafe_allow_html=True)


def create_pdf(v, a, komp, t_p, s_list, tp_m, t_tp, t_gn, t_rp,
               n_tp, n_gn, n_dk, n_rp, inv, e_j, a_m, p_j, c_j, kunde=""):
    pdf = FPDF()
    pdf.add_page()

    # Logo
    logo_added = False
    for fname in ['Logo.png', 'Logo.jpg', 'Logo.jpeg', 'logo.png']:
        if os.path.exists(fname):
            try:
                pdf.image(fname, x=10, y=10, h=18)
                pdf.ln(24)
                logo_added = True
                break
            except:
                pass
    if not logo_added:
        pdf.set_font("Arial", 'BI', 24)
        pdf.set_text_color(232, 71, 28)
        pdf.cell(55, 12, txt="Rieber", ln=False)
        pdf.set_font("Arial", '', 9)
        pdf.set_text_color(170, 170, 170)
        pdf.cell(0, 12, txt="M E T A   c o o k i n g", ln=True)

    pdf.set_draw_color(232, 71, 28)
    pdf.set_line_width(0.7)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, txt="SOLUTIONFINDER - Bedarfsanalyse", ln=True)
    if kunde:
        pdf.set_font("Arial", '', 11)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 7, txt=f"Kunde: {kunde}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, txt=f"Verfahren: {v}  |  Bereich: {a}", ln=True)
    pdf.cell(0, 7, txt=f"Menuekomponenten: {komp}  |  Teilnehmer gesamt: {t_p}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, txt="Detaillierte Stueckliste (Netto-Einzelpreise):", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 6, txt=f"  {t_tp}x  {tp_m}  (a {n_tp:,.2f} EUR)", ln=True)
    pdf.cell(0, 6, txt=f"  {t_gn}x  GN-Behaelter 1/1 65mm  (a {n_gn:,.2f} EUR)", ln=True)
    pdf.cell(0, 6, txt=f"  {t_gn}x  GN-Steckdeckel  (a {n_dk:,.2f} EUR)", ln=True)
    pdf.cell(0, 6, txt=f"  {t_rp}x  Rolliport  (a {n_rp:,.2f} EUR)", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(232, 71, 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 11, txt=f"  Gesamtinvestition: {inv:,.2f} EUR Netto", ln=True, fill=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, txt="Business Case & Nachhaltigkeit:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 6, txt=f"  Amortisation:          ca. {a_m:.1f} Monate", ln=True)
    pdf.cell(0, 6, txt=f"  Eingespartes Plastik:  {p_j:,.0f} kg / Jahr", ln=True)
    pdf.cell(0, 6, txt=f"  CO2-Reduktion:         {c_j:,.0f} kg / Jahr", ln=True)

    return pdf.output(dest='S').encode('latin-1')


# --- APP ---
st.set_page_config(
    page_title="Rieber Solutionfinder",
    page_icon="🍽️",
    layout="wide",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': '© Rieber GmbH'}
)
inject_apple_icon()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    logo_html = get_logo_html("70px")
    st.markdown(f'''
        <style>
        {HIDE_ST}
        .stApp {{ background-color: #f0f2f5; }}
        .login-wrap {{
            max-width: 380px; margin: 60px auto 0; background: white;
            padding: 40px 36px; border-radius: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center;
        }}
        .login-title {{
            font-size: 1em; font-weight: 700; color: #333;
            letter-spacing: 0.1em; text-transform: uppercase;
            margin-top: 16px; padding-top: 14px; border-top: 1px solid #f0f0f0;
        }}
        {FORM_BORDERS}
        .stButton > button {{
            background-color: #E8471C !important; color: white !important;
            font-weight: 700 !important; width: 100% !important;
            border: none !important; border-radius: 12px !important;
            padding: 12px 24px !important;
            box-shadow: 0 4px 12px rgba(232,71,28,0.3) !important;
        }}
        </style>
        <div class="login-wrap">
            {logo_html}
            <div class="login-title">Solutionfinder</div>
        </div>
    ''', unsafe_allow_html=True)
    pw = st.text_input("pw", type="password", label_visibility="collapsed",
                       placeholder="Passwort eingeben …")
    if st.button("Anmelden"):
        if pw == "Rieber":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Falsches Passwort.")
    st.stop()

set_design()

# --- EINGABE ---
st.markdown('<div class="eingabe-box">', unsafe_allow_html=True)
kunde = st.text_input("Kundenname", placeholder="z. B. Muster GmbH")
n_loc = st.number_input("Anzahl Standorte", min_value=1, value=1)
total_p = 0
loc_reports = []

for i in range(int(n_loc)):
    c1, c2 = st.columns(2)
    with c1: name = st.text_input(f"Name Standort {i+1}", value=f"Standort {i+1}")
    with c2: count = st.number_input(f"Teilnehmer Standort {i+1}", min_value=1, value=50)
    total_p += count
    loc_reports.append((name, count))

st.markdown("<hr style='border:none;border-top:1px solid #f0f0f0;margin:16px 0;'>",
            unsafe_allow_html=True)

k1, k2, k3 = st.columns(3)
with k1:
    v_sys = st.selectbox("Verfahren", ["Cook & Chill", "Cook & Hold"])
    komp = st.selectbox("Menükomponenten", ["1", "2", "3", "4"], index=2)
    tage = st.number_input("Tage pro Woche", value=5)
with k2:
    bereich = st.selectbox("Anwendungsbereich", ["Kita", "Schule", "Altenheim", "Betrieb"])
    puf = st.number_input("Umlauf-Puffer (%)", value=20) / 100
with k3:
    gruppe = st.selectbox("Kundengruppe", ["Endkunde", "Fachhandel", "Großkunde"])
    p_adj = st.number_input("Projekt Zu/Abschlag (%)", value=0.0)
    einweg = st.number_input("Einweg €/Portion", value=0.35)
st.markdown('</div>', unsafe_allow_html=True)

# --- LOGIK ---
tp_m = "thermoport 1000K" if v_sys == "Cook & Chill" else "thermoport 1000KB 4.0"
tp_lp = 920.0 if v_sys == "Cook & Chill" else 1380.0
g_map = {"Kita": 280, "Schule": 360, "Altenheim": 435, "Betrieb": 430}
g_p = g_map[bereich]

t_tp, t_gn, t_rp = 0, 0, 0
for _, c in loc_reports:
    gn_loc = math.ceil(((g_p * c) / 1000) / 5)
    gn_f = math.ceil(gn_loc * (1 + puf))
    tp_f = math.ceil(gn_f / 5)
    t_tp += tp_f
    t_gn += gn_f
    t_rp += math.ceil(tp_f / 2)

rab = 0.3 if gruppe == "Fachhandel" else (0.4 if gruppe == "Großkunde" else 0.0)

def calc_final_netto(lp, r_base, adjustment):
    return round(lp * (1 - r_base) * (1 + (adjustment / 100)), 2)

n_tp = calc_final_netto(tp_lp, rab, p_adj)
n_gn = calc_final_netto(42.0, rab, p_adj)
n_dk = calc_final_netto(22.0, rab, p_adj)
n_rp = calc_final_netto(310.0, rab, p_adj)

inv = (t_tp * n_tp) + (t_gn * (n_gn + n_dk)) + (t_rp * n_rp)
roi_j = einweg * total_p * tage * 52
amo = (inv / (einweg * total_p)) / (tage * 4.33) if total_p > 0 and einweg > 0 else 0
pla = total_p * 0.03 * tage * 52
co2 = pla * 3.5

# --- OUTPUT ---
st.markdown('<p class="section-label">Bedarf &amp; Investition</p>', unsafe_allow_html=True)
r1, r2, r3, r4 = st.columns(4)
r1.markdown(f'''<div class="result-card">
    <p class="metric-title">{tp_m}</p>
    <p class="metric-value">{t_tp}</p>
    <p class="metric-price">à {n_tp:.2f} €</p>
</div>''', unsafe_allow_html=True)
r2.markdown(f'''<div class="result-card">
    <p class="metric-title">GN 1/1 65mm</p>
    <p class="metric-value">{t_gn}</p>
    <p class="metric-price">à {n_gn:.2f} €</p>
</div>''', unsafe_allow_html=True)
r3.markdown(f'''<div class="result-card">
    <p class="metric-title">Steckdeckel</p>
    <p class="metric-value">{t_gn}</p>
    <p class="metric-price">à {n_dk:.2f} €</p>
</div>''', unsafe_allow_html=True)
r4.markdown(f'''<div class="result-card">
    <p class="metric-title">Rolliport</p>
    <p class="metric-value">{t_rp}</p>
    <p class="metric-price">à {n_rp:.2f} €</p>
</div>''', unsafe_allow_html=True)

st.markdown(f'''<div class="total-card">
    <p class="total-label">Gesamtinvestition</p>
    <p class="total-value">{inv:,.2f} € Netto</p>
</div>''', unsafe_allow_html=True)

st.markdown('<p class="section-label">ROI &amp; Nachhaltigkeit</p>', unsafe_allow_html=True)
o1, o2, o3, o4 = st.columns(4)
o1.markdown(f'''<div class="roi-card">
    <div class="card-icon">♻️</div>
    <p class="metric-title">Einweg / Jahr</p>
    <p class="metric-value" style="color:#d9534f;">{roi_j:,.0f} €</p>
</div>''', unsafe_allow_html=True)
o2.markdown(f'''<div class="roi-card">
    <div class="card-icon">🪙</div>
    <p class="metric-title">Amortisation</p>
    <p class="metric-value">{amo:.1f} <span style="font-size:0.45em;color:#888;font-weight:600;">Mon.</span></p>
</div>''', unsafe_allow_html=True)
o3.markdown(f'''<div class="esg-card">
    <div class="card-icon">🥤</div>
    <p class="metric-title">Plastik gespart</p>
    <p class="metric-value" style="color:#2a9d8f;">{pla:,.0f} <span style="font-size:0.45em;color:#888;font-weight:600;">kg/J.</span></p>
</div>''', unsafe_allow_html=True)
o4.markdown(f'''<div class="esg-card">
    <div class="card-icon">🌫️</div>
    <p class="metric-title">CO₂ reduziert</p>
    <p class="metric-value" style="color:#2a9d8f;">{co2:,.0f} <span style="font-size:0.45em;color:#888;font-weight:600;">kg/J.</span></p>
</div>''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
pdf_b = create_pdf(v_sys, bereich, komp, total_p, loc_reports, tp_m, t_tp, t_gn, t_rp,
                   n_tp, n_gn, n_dk, n_rp, inv, roi_j, amo, pla, co2, kunde)
st.download_button("Bedarfsanalyse als PDF speichern", data=pdf_b,
                   file_name="Rieber_Bedarfsanalyse.pdf", mime="application/pdf")
