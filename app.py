import streamlit as st
import streamlit.components.v1 as components
import math
import base64
import os
import uuid
from fpdf import FPDF

# ==========================================
# 1. BASIS-FUNKTIONEN & CSS
# ==========================================

def get_base64(bin_file):
    if not os.path.exists(bin_file):
        return ""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def inject_apple_icon():
    if os.path.exists('Solutionfinder.jpeg'):
        try:
            b64 = get_base64('Solutionfinder.jpeg')
            components.html(f"""<script>
(function(){{
var p=parent.document;
if(!p.querySelector('link[rel="apple-touch-icon"]')){{
   var l=p.createElement('link');l.rel='apple-touch-icon';
   l.href='data:image/jpeg;base64,{b64}';p.head.appendChild(l);
}}
[['mobile-web-app-capable','yes'],['apple-mobile-web-app-capable','yes'],
['apple-mobile-web-app-title','Solutionfinder']].forEach(function(d){{
   var m=p.createElement('meta');m.name=d[0];m.content=d[1];p.head.appendChild(m);
}});
}})();
</script>""", height=0)
        except:
            pass

LOGO_FILES = ['Logo.png', 'Logo.jpg', 'Logo.jpeg', 'logo.png']

def find_logo():
    for f in LOGO_FILES:
        if os.path.exists(f):
            return f
    return None

def get_logo_html(height="75px"):
    logo = find_logo()
    if logo:
        try:
            ext = logo.rsplit('.', 1)[1].lower()
            mime = 'jpeg' if ext in ('jpg', 'jpeg') else 'png'
            b64 = get_base64(logo)
            return (
                '<div style="text-align:center;margin-bottom:4px;">'
                f'<img src="data:image/{mime};base64,{b64}" '
                f'style="height:{height};object-fit:contain;">'
                '</div>'
            )
        except:
            pass
    return (
        f'<div style="text-align:center;margin-bottom:4px;">'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 370 118" style="height:{height};">'
        '<text x="4" y="82" font-family="Arial Black,Arial,sans-serif" '
        'font-weight="900" font-style="italic" font-size="86" fill="#E8471C">Rieber</text>'
        '<text x="10" y="112" font-family="Arial,sans-serif" font-weight="300" '
        'font-size="19" fill="#aaaaaa" letter-spacing="7">M E T A  cooking</text>'
        '</svg></div>'
    )

CSS = (
"#MainMenu{visibility:hidden;}"
"footer{visibility:hidden;}"
".stDeployButton{display:none!important;}"
"header[data-testid='stHeader']{background:transparent;}"
"[data-testid='manage-app-button']{display:none!important;}"
".stApp{background-color:#f0f2f5;}"
".block-container{padding-top:1.5rem!important;}"
".eingabe-box{background:#fff;padding:28px;border-radius:16px;border:none;"
"margin-bottom:24px;box-shadow:0 2px 10px rgba(0,0,0,0.07);}"
".section-label{font-size:.75em;font-weight:700;letter-spacing:.15em;"
"color:#999;text-transform:uppercase;margin:8px 0 4px;}"
"div[data-baseweb='select']>div{border:2px solid #E8471C!important;"
"border-radius:10px!important;background-color:white!important;}"
"div[data-baseweb='input']>div{border:2px solid #E8471C!important;"
"border-radius:10px!important;background-color:white!important;}"
".result-card{background:#fff;padding:22px 16px;border-radius:16px;"
"border:2px solid #E8471C;text-align:center;"
"box-shadow:0 2px 8px rgba(0,0,0,0.05);margin-bottom:16px;}"
".metric-title{color:#888;font-weight:600;font-size:.82em;margin-bottom:8px;"
"text-transform:uppercase;letter-spacing:.6px;}"
".metric-value{font-size:2.4em;font-weight:800;color:#1a1a1a;line-height:1;}"
".total-card{background:#E8471C;color:white;text-align:center;"
"padding:22px 24px;border-radius:16px;margin:20px 0 28px;}"
".total-value{font-size:2.2em;font-weight:900;}"
".roi-card,.esg-card{background:#fff;border:2px solid #E8471C;text-align:center;"
"box-shadow:0 2px 8px rgba(0,0,0,0.05);padding:20px 16px;border-radius:16px;margin-bottom:12px;}"
".stDownloadButton>button,.stButton>button{background-color:#E8471C!important;"
"color:white!important;font-weight:700!important;width:100%!important;"
"border:none!important;border-radius:12px!important;padding:14px 24px!important;}"
".plan-container { display: flex; flex-direction: row; align-items: stretch; justify-content: flex-start; overflow-x: auto; padding: 20px; background: #fff; border: 2px dashed #ccc; border-radius: 16px; margin-top: 10px; }"
".plan-module { position: relative; border: 2px solid #1a1a1a; margin-right: 4px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 0.8em; text-align: center; border-radius: 8px; box-shadow: 2px 2px 0px rgba(0,0,0,0.1); min-height: 100px; }"
".plan-rutsche { position: absolute; bottom: -8px; left: 0; right: 0; height: 5px; background: #E8471C; border-radius: 2px; }"
".plan-abdeckung { position: absolute; bottom: -12px; left: 0; right: 0; height: 10px; background: #333; border-radius: 2px; }"
)

def set_design(title_suffix=""):
   logo_html = get_logo_html("75px")
   header = (
       '<div style="background:white;text-align:center;padding:28px 20px 20px;'
       'border-radius:16px;margin-bottom:24px;box-shadow:0 2px 10px rgba(0,0,0,0.07);">'
       + logo_html +
       f'<p style="font-size:1.05em;font-weight:700;color:#333;letter-spacing:0.1em;'
       f'text-transform:uppercase;margin-top:16px;padding-top:14px;'
       f'border-top:1px solid #f0f0f0;">Solution<strong>finder</strong> {title_suffix}</p>'
       '</div>'
   )
   st.markdown(f'<style>{CSS}</style>' + header, unsafe_allow_html=True)

# ==========================================
# 2. PDF GENERATOREN
# ==========================================

def create_pdf_solutionfinder(v, a, komp, t_p, tage, s_list, tp_m, t_tp, t_gn, t_rp, n_tp, n_gn, n_dk, n_rp, inv, e_j, a_m, p_j, c_j, kunde=""):
   pdf = FPDF()
   pdf.add_page()
   logo = find_logo()
   if logo:
       try: pdf.image(logo, x=10, y=10, h=18); pdf.ln(24)
       except: pass
   pdf.set_font("Arial", 'B', 13); pdf.cell(0, 8, txt="SOLUTIONFINDER - Bedarfsanalyse", ln=True); pdf.ln(3)
   if kunde: pdf.set_font("Arial", 'B', 11); pdf.cell(0, 7, txt=f"Kunde: {kunde}", ln=True)
   pdf.set_font("Arial", '', 10); pdf.cell(0, 6, txt=f"Verfahren: {v} | Bereich: {a}", ln=True); pdf.ln(4)
   pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, txt=f"Gesamtinvestition: {inv:,.2f} EUR Netto", ln=True); pdf.ln(5)
   pdf.set_font("Arial", '', 10); pdf.cell(0, 6, txt=f"Amortisation: ca. {a_m:.1f} Monate", ln=True)
   return pdf.output(dest='S').encode('latin-1')

def create_pdf_bain_marie(k_name, anzahl, verfahren, ersparnis, gesamt):
   pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
   pdf.cell(0, 10, txt="Rieber - Wirtschaftlichkeitsanalyse Bain Marie", ln=True, align="C"); pdf.ln(10)
   pdf.set_font("Arial", '', 12); pdf.cell(0, 10, txt=f"Kunde: {k_name}", ln=True)
   pdf.cell(0, 10, txt=f"System: {verfahren} | Einsparung: {gesamt:,.2f} EUR / Jahr", ln=True)
   return pdf.output(dest='S').encode('latin-1')

def create_pdf_rolling_buffet(glob, modules):
   pdf = FPDF(orientation="L"); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
   pdf.cell(0, 10, txt="Rieber Rolling Buffet - Anlagenplanung", ln=True, align='C'); pdf.ln(10)
   
   if glob.get("kunde"):
       pdf.set_font("Arial", 'B', 12)
       pdf.cell(0, 8, txt=f"Kunde: {glob['kunde']}", ln=True)
       
   pdf.set_font("Arial", '', 10); pdf.cell(0, 6, txt=f"Mobilitaet: {glob['mobilitaet']} | Abdeckung: {glob['abdeckung']}", ln=True)
   pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, txt="Konfigurierte Module:", ln=True)
   pdf.set_font("Arial", '', 9)
   for i, m in enumerate(modules):
      l = m['sonder_laenge'] if m['laenge_typ'] == "SONDERBAU" else int(m['laenge_typ'].split()[0])
      pdf.cell(0, 6, txt=f"M{i+1}: {m['typ']} ({l}mm) | Technik: {m['technik']} | Gaesteseite: {m['peripherie']}", ln=True)
   return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 3. APP SETUP & AUTH
# ==========================================

st.set_page_config(page_title="Rieber Solutionfinder", page_icon="🍽️", layout="wide")
inject_apple_icon()

if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "page" not in st.session_state: st.session_state.page = "home"
if 'buffet_modules' not in st.session_state: st.session_state.buffet_modules = []

if not st.session_state.authenticated:
   set_design()
   _, mid, _ = st.columns([1, 1.5, 1])
   with mid:
       pw = st.text_input("Passwort", type="password", placeholder="Passwort eingeben …", label_visibility="collapsed")
       if st.button("Anmelden", use_container_width=True):
           if pw == "Rieber": st.session_state.authenticated = True; st.rerun()
           else: st.error("Falsches Passwort.")
   st.stop()

# ==========================================
# 4. NAVIGATION (HOME)
# ==========================================

if st.session_state.page == "home":
    set_design()
    st.markdown('<div class="eingabe-box" style="text-align:center;">', unsafe_allow_html=True)
    st.markdown('<p class="section-label" style="font-size:1.1em;">Zentrale Werkzeugauswahl</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📊 Bedarfsanalyse\n(Solutionfinder)"): st.session_state.page = "solutionfinder"; st.rerun()
    with c2:
        if st.button("⚡ Bain Marie\nErsparnis-Rechner"): st.session_state.page = "ersparnis"; st.rerun()
    with c3:
        if st.button("🍱 Rolling Buffet\nAnlagenplanung"): st.session_state.page = "rolling"; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 5. TOOL: SOLUTIONFINDER (ORIGINAL CODE)
# ==========================================

elif st.session_state.page == "solutionfinder":
    if st.sidebar.button("← Zurück zum Hauptmenü"): st.session_state.page = "home"; st.rerun()
    set_design()
    st.markdown('<div class="eingabe-box">', unsafe_allow_html=True)
    kunde = st.text_input("Kundenname", placeholder="z. B. Muster GmbH")
    n_loc = st.number_input("Anzahl Standorte", min_value=1, value=1)
    total_p, loc_reports = 0, []
    for i in range(int(n_loc)):
       c1, c2 = st.columns(2)
       with c1: name = st.text_input(f"Name Standort {i+1}", value=f"Standort {i+1}")
       with c2: count = st.number_input(f"Teilnehmer Standort {i+1}", min_value=1, value=50)
       total_p += count; loc_reports.append((name, count))
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
    tp_m = "thermoport 1000K" if v_sys == "Cook & Chill" else "thermoport 1000KB 4.0"
    tp_lp = 920.0 if v_sys == "Cook & Chill" else 1380.0
    g_p = {"Kita": 280, "Schule": 360, "Altenheim": 435, "Betrieb": 430}[bereich]
    t_tp, t_gn, t_rp = 0, 0, 0
    for _, c in loc_reports:
       gn_loc = math.ceil(((g_p * c) / 1000) / 5)
       gn_f = math.ceil(gn_loc * (1 + puf)); tp_f = math.ceil(gn_f / 5)
       t_tp += tp_f; t_gn += gn_f; t_rp += math.ceil(tp_f / 2)
    rab = 0.3 if gruppe == "Fachhandel" else (0.4 if gruppe == "Großkunde" else 0.0)
    n_tp = round(tp_lp * (1 - rab) * (1 + (p_adj / 100)), 2)
    n_gn = round(42.0 * (1 - rab) * (1 + (p_adj / 100)), 2)
    n_dk = round(22.0 * (1 - rab) * (1 + (p_adj / 100)), 2)
    n_rp = round(310.0 * (1 - rab) * (1 + (p_adj / 100)), 2)
    inv = (t_tp * n_tp) + (t_gn * (n_gn + n_dk)) + (t_rp * n_rp)
    roi_j = einweg * total_p * tage * 52
    amo = (
