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
                    var m = p.createElement('meta');
                    m.name = 'mobile-web-app-capable';
                    m.content = 'yes';
                    p.head.appendChild(m);
                    var m2 = p.createElement('meta');
                    m2.name = 'apple-mobile-web-app-capable';
                    m2.content = 'yes';
                    p.head.appendChild(m2);
                    var m3 = p.createElement('meta');
                    m3.name = 'apple-mobile-web-app-title';
                    m3.content = 'Solutionfinder';
                    p.head.appendChild(m3);
                }})();
                </script>
            """, height=0)
        except:
            pass

def set_design():
    st.markdown('''
        <style>
        .stApp { background-color: #f0f2f5; }
        .block-container { padding-top: 1.5rem !important; }

        /* Header / Logo */
        .rieber-header {
            background: white; text-align: center;
            padding: 24px 20px 20px; border-radius: 16px;
            margin-bottom: 24px; box-shadow: 0 2px 10px rgba(0,0,0,0.07);
        }
        .logo-rieber {
            font-size: 3em; font-weight: 900; color: #E8471C;
            line-height: 1; font-style: italic; letter-spacing: -1px;
        }
        .logo-sub {
            font-size: 0.75em; letter-spacing: 0.28em; color: #aaa;
            font-weight: 400; text-transform: uppercase;
            display: block; margin-top: 4px;
        }
        .app-name {
            font-size: 1.05em; font-weight: 700; color: #333;
            letter-spacing: 0.1em; text-transform: uppercase;
            margin-top: 14px; padding-top: 14px;
            border-top: 1px solid #f0f0f0;
        }

        /* Input box */
        .eingabe-box {
            background: #fff; padding: 28px; border-radius: 16px;
            border: none; margin-bottom: 24px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.07);
        }

        /* Section labels */
        .section-label {
            font-size: 0.75em; font-weight: 700; letter-spacing: 0.15em;
            color: #999; text-transform: uppercase; margin: 8px 0 4px;
        }

        /* Result cards */
        .result-card {
            background: #fff; padding: 22px 16px; border-radius: 16px;
            border: none; text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.07); margin-bottom: 16px;
        }
        .metric-title {
            color: #888; font-weight: 600; font-size: 0.82em;
            margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.6px;
        }
        .metric-value {
            font-size: 2.4em; font-weight: 800; color: #1a1a1a; line-height: 1;
        }
        .metric-price {
            font-size: 0.92em; color: #E8471C; font-weight: 600; margin-top: 10px;
        }

        /* Total investment */
        .total-card {
            background: #E8471C; color: white; text-align: center;
            padding: 22px 24px; border-radius: 16px; margin: 20px 0 28px;
        }
        .total-label {
            font-size: 0.82em; font-weight: 600; letter-spacing: 0.12em;
            text-transform: uppercase; opacity: 0.9; margin-bottom: 6px;
        }
        .total-value { font-size: 2.2em; font-weight: 900; }

        /* ROI / ESG cards */
        .roi-card, .esg-card {
            background: #fff; border: none; text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.07);
            padding: 20px 16px; border-radius: 16px;
        }

        /* Download button */
        .stDownloadButton > button, .stButton > button {
            background-color: #E8471C !important;
            color: white !important; font-weight: 700 !important;
            width: 100% !important; border: none !important;
            border-radius: 12px !important; padding: 14px 24px !important;
            font-size: 1em !important; letter-spacing: 0.04em !important;
            box-shadow: 0 4px 12px rgba(232,71,28,0.3) !important;
            transition: all 0.2s !important;
        }
        .stDownloadButton > button:hover, .stButton > button:hover {
            box-shadow: 0 6px 18px rgba(232,71,28,0.4) !important;
            transform: translateY(-1px) !important;
        }
        </style>

        <div class="rieber-header">
            <div class="logo-rieber">Rieber</div>
            <span class="logo-sub">M E T A &nbsp; c o o k i n g</span>
            <div class="app-name">Solution<strong>finder</strong></div>
        </div>
    ''', unsafe_allow_html=True)


def create_pdf(v, a, komp, t_p, s_list, tp_m, t_tp, t_gn, t_rp, n_tp, n_gn, n_dk, n_rp, inv, e_j, a_m, p_j, c_j):
    pdf = FPDF()
    pdf.add_page()

    # Logo header
    pdf.set_font("Arial", 'BI', 24)
    pdf.set_text_color(232, 71, 28)
    pdf.cell(55, 12, txt="Rieber", ln=False, align='L')
    pdf.set_font("Arial", '', 9)
    pdf.set_text_color(170, 170, 170)
    pdf.cell(0, 12, txt="M E T A   c o o k i n g", ln=True, align='L')

    pdf.set_draw_color(232, 71, 28)
    pdf.set_line_width(0.7)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # Title
    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, txt="SOLUTIONFINDER - Bedarfsanalyse", ln=True)
    pdf.ln(5)

    # Inputs
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, txt=f"Verfahren: {v}  |  Bereich: {a}", ln=True)
    pdf.cell(0, 7, txt=f"Menuekomponenten: {komp}  |  Teilnehmer gesamt: {t_p}", ln=True)
    pdf.ln(5)

    # Stueckliste
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

    # Total (orange banner)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(232, 71, 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 11, txt=f"  Gesamtinvestition: {inv:,.2f} EUR Netto", ln=True, fill=True)
    pdf.ln(5)

    # Business case
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
st.set_page_config(page_title="Rieber Solutionfinder", page_icon="🍽️", layout="wide")
inject_apple_icon()
set_design()

# --- EINGABE ---
st.markdown('<div class="eingabe-box">', unsafe_allow_html=True)
n_loc = st.number_input("Anzahl Standorte", min_value=1, value=1)
total_p = 0
loc_reports = []

for i in range(int(n_loc)):
    c1, c2 = st.columns(2)
    with c1: name = st.text_input(f"Name Standort {i+1}", value=f"Standort {i+1}")
    with c2: count = st.number_input(f"Teilnehmer Standort {i+1}", min_value=1, value=50)
    total_p += count
    loc_reports.append((name, count))

st.markdown("<hr style='border:none;border-top:1px solid #f0f0f0;margin:16px 0;'>", unsafe_allow_html=True)

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
    <p class="metric-title">Einweg / Jahr</p>
    <p class="metric-value" style="color:#d9534f;">{roi_j:,.0f} €</p>
</div>''', unsafe_allow_html=True)
o2.markdown(f'''<div class="roi-card">
    <p class="metric-title">Amortisation</p>
    <p class="metric-value">{amo:.1f} <span style="font-size:0.45em;color:#888;font-weight:600;">Mon.</span></p>
</div>''', unsafe_allow_html=True)
o3.markdown(f'''<div class="esg-card">
    <p class="metric-title">Plastik gespart</p>
    <p class="metric-value" style="color:#2a9d8f;">{pla:,.0f} <span style="font-size:0.45em;color:#888;font-weight:600;">kg/J.</span></p>
</div>''', unsafe_allow_html=True)
o4.markdown(f'''<div class="esg-card">
    <p class="metric-title">CO2 reduziert</p>
    <p class="metric-value" style="color:#2a9d8f;">{co2:,.0f} <span style="font-size:0.45em;color:#888;font-weight:600;">kg/J.</span></p>
</div>''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
pdf_b = create_pdf(v_sys, bereich, komp, total_p, loc_reports, tp_m, t_tp, t_gn, t_rp, n_tp, n_gn, n_dk, n_rp, inv, roi_j, amo, pla, co2)
st.download_button("Angebot als PDF speichern", data=pdf_b, file_name="Rieber_Bedarfsanalyse.pdf", mime="application/pdf")
