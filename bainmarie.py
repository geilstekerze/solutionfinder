import streamlit as st
import streamlit.components.v1 as components
import base64
import os
from fpdf import FPDF

# ==========================================
# 1. BASIS-FUNKTIONEN, LOGO & CSS
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
['apple-mobile-web-app-title','Ersparnisrechner']].forEach(function(d){{
   var m=p.createElement('meta');m.name=d[0];m.content=d[1];p.head.appendChild(m);
}});
}})();
</script>""", height=0)
        except:
            pass

def get_logo_html(height="75px"):
    b64 = get_base64('Logo.png') if os.path.exists('Logo.png') else get_base64('Logo.jpg')
    if b64:
        return f'<div style="text-align:center;margin-bottom:4px;"><img src="data:image/png;base64,{b64}" style="height:{height};object-fit:contain;"></div>'
    # Fallback SVG Logo
    return f'<div style="text-align:center;margin-bottom:4px;"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 370 118" style="height:{height};"><text x="4" y="82" font-family="Arial Black,Arial,sans-serif" font-weight="900" font-style="italic" font-size="86" fill="#E8471C">Rieber</text><text x="10" y="112" font-family="Arial,sans-serif" font-weight="300" font-size="19" fill="#aaaaaa" letter-spacing="7">M E T A  cooking</text></svg></div>'

# SICHERE MULTI-LINE SCHREIBWEISE FÜR CSS
CSS = """
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
.stDeployButton {display:none!important;}
header[data-testid='stHeader'] {background:transparent;}
.stApp {background-color:#f0f2f5;}
.block-container {padding-top:1.5rem!important;}
.eingabe-box {background:#fff; padding:28px; border-radius:16px; border:none; margin-bottom:24px; box-shadow:0 2px 10px rgba(0,0,0,0.07);}
.section-label {font-size:.75em; font-weight:700; letter-spacing:.15em; color:#999; text-transform:uppercase; margin:8px 0 4px;}
div[data-baseweb='select']>div {border:2px solid #E8471C!important; border-radius:10px!important; background-color:white!important;}
div[data-baseweb='input']>div {border:2px solid #E8471C!important; border-radius:10px!important; background-color:white!important;}
.total-card {background:#E8471C; color:white; text-align:center; padding:22px 24px; border-radius:16px; margin:20px 0 28px;}
.total-value {font-size:2.2em; font-weight:900;}
.stDownloadButton>button, .stButton>button {background-color:#E8471C!important; color:white!important; font-weight:700!important; width:100%!important; border:none!important; border-radius:12px!important; padding:14px 24px!important;}
"""

def set_design():
    logo_html = get_logo_html("75px")
    header = f"""
    <div style="background:white; text-align:center; padding:28px 20px 20px; border-radius:16px; margin-bottom:24px; box-shadow:0 2px 10px rgba(0,0,0,0.07);">
        {logo_html}
        <p style="font-size:1.05em; font-weight:700; color:#333; letter-spacing:0.1em; text-transform:uppercase; margin-top:16px; padding-top:14px; border-top:1px solid #f0f0f0;">
            Wirtschaftlichkeits<strong>analyse</strong> Bain Marie
        </p>
    </div>
    """
    st.markdown(f"<style>{CSS}</style>" + header, unsafe_allow_html=True)

# ==========================================
# 2. PDF GENERATOR
# ==========================================

def create_pdf_bain_marie(k_name, anzahl, verfahren, ersparnis, gesamt):
    pdf = FPDF()
    pdf.add_page()
    
    # Logo falls vorhanden
    b64 = get_base64('Logo.png') if os.path.exists('Logo.png') else get_base64('Logo.jpg')
    if b64:
        try: 
            pdf.image('Logo.png' if os.path.exists('Logo.png') else 'Logo.jpg', x=10, y=10, h=18)
            pdf.ln(24)
        except: 
            pass

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt="Rieber - Wirtschaftlichkeitsanalyse Bain Marie", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    if k_name:
        pdf.cell(0, 10, txt=f"Kunde: {k_name}", ln=True)
        
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, txt=f"System: {verfahren}", ln=True)
    pdf.cell(0, 10, txt=f"Anzahl Becken: {anzahl}", ln=True)
    pdf.cell(0, 10, txt=f"Ersparnis pro Becken: {ersparnis:,.2f} EUR / Jahr", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(232, 71, 28) # Rieber Orange
    pdf.cell(0, 10, txt=f"Gesamteinsparung: {gesamt:,.2f} EUR / Jahr", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 3. APP SETUP & HAUPTPROGRAMM
# ==========================================

st.set_page_config(page_title="Rieber Ersparnis-Rechner", page_icon="⚡", layout="centered")
inject_apple_icon()
set_design()

LOGIK_BM = {
    "Trocken Bain Marie": 490.34, 
    "Varithek 800": 496.06, 
    "EST Infrarot": 515.96
}

st.markdown('<div class="eingabe-box">', unsafe_allow_html=True)
st.markdown('<p class="section-label">Eingabedaten</p>', unsafe_allow_html=True)

k_name = st.text_input("Kundenname", placeholder="z. B. Muster GmbH")

c1, c2 = st.columns(2)
with c1:
    anzahl = st.number_input("Anzahl Becken", min_value=1, value=1)
with c2:
    verfahren = st.selectbox("Neue Technik", list(LOGIK_BM.keys()))

st.markdown("<hr style='border:none; border-top:1px solid #f0f0f0; margin:20px 0;'>", unsafe_allow_html=True)

if st.button("Ersparnis Berechnen", use_container_width=True):
    gesamt = anzahl * LOGIK_BM[verfahren]
    
    st.markdown(f'<div class="total-card"><p style="margin:0; font-size:1.1em; text-transform:uppercase; letter-spacing:1px; opacity:0.9;">Gesamteinsparung</p><p class="total-value">+ {gesamt:,.2f} € / Jahr</p></div>', unsafe_allow_html=True)
    
    pdf_bm = create_pdf_bain_marie(k_name, anzahl, verfahren, LOGIK_BM[verfahren], gesamt)
    
    filename = f"Rieber_BainMarie_{k_name.replace(' ', '_')}.pdf" if k_name else "Rieber_BainMarie.pdf"
    
    st.download_button(
        "Ergebnis als PDF speichern", 
        data=pdf_bm, 
        file_name=filename,
        mime="application/pdf"
    )

st.markdown('</div>', unsafe_allow_html=True)
