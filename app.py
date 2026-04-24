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
    "div[data-baseweb='base-input']{background-color:white!important;}"
    ".result-card{background:#fff;padding:22px 16px;border-radius:16px;"
    "border:2px solid #E8471C;text-align:center;"
    "box-shadow:0 2px 8px rgba(0,0,0,0.05);margin-bottom:16px;}"
    ".metric-title{color:#888;font-weight:600;font-size:.82em;margin-bottom:8px;"
    "text-transform:uppercase;letter-spacing:.6px;}"
    ".metric-value{font-size:2.4em;font-weight:800;color:#1a1a1a;line-height:1;}"
    ".metric-price{font-size:.92em;color:#E8471C;font-weight:600;margin-top:10px;}"
    ".total-card{background:#E8471C;color:white;text-align:center;"
    "padding:22px 24px;border-radius:16px;margin:20px 0 28px;}"
    ".total-label{font-size:.82em;font-weight:600;letter-spacing:.12em;"
    "text-transform:uppercase;opacity:.9;margin-bottom:6px;}"
    ".total-value{font-size:2.2em;font-weight:900;}"
    ".roi-card,.esg-card{background:#fff;border:2px solid #E8471C;text-align:center;"
    "box-shadow:0 2px 8px rgba(0,0,0,0.05);padding:20px 16px;"
    "border-radius:16px;margin-bottom:12px;}"
    ".card-icon{font-size:2em;margin-bottom:6px;line-height:1.2;}"
    ".stDownloadButton>button,.stButton>button{background-color:#E8471C!important;"
    "color:white!important;font-weight:700!important;width:100%!important;"
    "border:none!important;border-radius:12px!important;padding:14px 24px!important;"
    "font-size:1em!important;box-shadow:0 4px 12px rgba(232,71,28,.3)!important;}"
)


def set_design(title_suffix=""):
    logo_html = get_logo_html("75px")
    suffix_html = f" &ndash; {title_suffix}" if title_suffix else ""
    header = (
        '<div style="background:white;text-align:center;padding:28px 20px 20px;'
        'border-radius:16px;margin-bottom:24px;box-shadow:0 2px 10px rgba(0,0,0,0.07);">'
        + logo_html +
        f'<p style="font-size:1.05em;font-weight:700;color:#333;letter-spacing:0.1em;'
        f'text-transform:uppercase;margin-top:16px;padding-top:14px;'
        f'border-top:1px solid #f0f0f0;">'
        f'Solution<strong>finder</strong>{suffix_html}</p>'
        '</div>'
    )
    st.markdown(f'<style>{CSS}</style>' + header, unsafe_allow_html=True)


# ==========================================
# 2. PDF GENERATOREN
# ==========================================

def create_pdf(v, a, komp, t_p, tage, s_list, tp_m, t_tp, t_gn, t_rp,
               n_tp, n_gn, n_dk, n_rp, inv, e_j, a_m, p_j, c_j, kunde=""):
    pdf = FPDF()
    pdf.add_page()
    logo = find_logo()
    if logo:
        try:
            pdf.image(logo, x=10, y=10, h=18)
            pdf.ln(24)
            logo = True
        except:
            logo = None
    if not logo:
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
    pdf.ln(3)
    if kunde:
        pdf.set_font("Arial", 'B', 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 7, txt=f"Kunde: {kunde}", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, txt=f"Verfahren: {v}  |  Bereich: {a}", ln=True)
    pdf.cell(0, 7, txt=f"Menuekomponenten: {komp}  |  Tage/Woche: {tage}", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 7, txt=f"Standorte ({len(s_list)}):", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(60, 60, 60)
    for loc_name, loc_count in s_list:
        pdf.cell(0, 6, txt=f"  - {loc_name}: {loc_count} Teilnehmer", ln=True)
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 7, txt=f"  Gesamt: {t_p} Teilnehmer", ln=True)
    pdf.ln(4)
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


def create_pdf_bain_marie(kundenname, anzahl, verfahren, ersparnis, gesamt_ersparnis, prozent):
    pdf = FPDF()
    pdf.add_page()
    logo = find_logo()
    if logo:
        try:
            pdf.image(logo, x=10, y=10, h=18)
            pdf.ln(24)
            logo = True
        except:
            logo = None
    if not logo:
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
    pdf.cell(0, 8, txt="Wirtschaftlichkeitsanalyse - Bain Marie", ln=True)
    pdf.ln(3)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 7, txt=f"Kunde: {kundenname}", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, txt=f"Zu ersetzende Wasser-Bain-Maries: {anzahl}", ln=True)
    pdf.cell(0, 7, txt=f"Gewaehltes Rieber System: {verfahren}", ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, txt="Berechnung der Kosteneinsparung:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 6, txt=f"  Einsparung pro Becken: {ersparnis:,.2f} EUR / Jahr", ln=True)
    pdf.cell(0, 6, txt=f"  Reduktion des Stromverbrauchs: {prozent}%", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(232, 71, 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 11, txt=f"  Gesamtersparnis: {gesamt_ersparnis:,.2f} EUR / Jahr", ln=True, fill=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5,
        txt="Berechnungsgrundlage: 0,372 Euro/kWh bei 365 Betriebstagen pro Jahr. "
            "Referenzwert: Klassisches Wasser-Bain-Marie (1,2 kW).")
    return pdf.output(dest="S").encode("latin-1")


def create_pdf_rolling_buffet(glob, modules):
    pdf = FPDF(orientation="L")
    pdf.add_page()
    logo = find_logo()
    logo_placed = False
    if logo:
        try:
            pdf.image(logo, x=10, y=10, h=18)
            pdf.ln(24)
            logo_placed = True
        except:
            pass
    if not logo_placed:
        pdf.set_font("Arial", 'BI', 24)
        pdf.set_text_color(232, 71, 28)
        pdf.cell(55, 12, txt="Rieber", ln=False)
        pdf.set_font("Arial", '', 9)
        pdf.set_text_color(170, 170, 170)
        pdf.cell(0, 12, txt="M E T A   c o o k i n g", ln=True)
    pdf.set_draw_color(232, 71, 28)
    pdf.set_line_width(0.7)
    pdf.line(10, pdf.get_y(), 287, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, txt="Rolling Buffet - Anlagenplanung", ln=True)
    pdf.ln(2)
    if glob.get("kunde"):
        pdf.set_font("Arial", 'B', 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 7, txt=f"Kunde: {glob['kunde']}", ln=True)
    abd_text = glob.get("abdeckung", "")
    if glob.get("abdeckung_farbe"):
        abd_text += f" ({glob['abdeckung_farbe']})"
    des_text = glob.get("design", "")
    if glob.get("design_farbe"):
        des_text += f" ({glob['design_farbe']})"
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6,
        txt=f"Mobilitaet: {glob.get('mobilitaet', '')}  |  "
            f"Abdeckung: {abd_text}  |  Design: {des_text}",
        ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(232, 71, 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(12, 7, txt="Nr.",          fill=True)
    pdf.cell(45, 7, txt="Typ",          fill=True)
    pdf.cell(32, 7, txt="Laenge",       fill=True)
    pdf.cell(58, 7, txt="Technik",      fill=True)
    pdf.cell(52, 7, txt="Unterbau",     fill=True)
    pdf.cell(0,  7, txt="Gaesteseite",  fill=True, ln=True)
    pdf.set_font("Arial", '', 9)
    pdf.set_text_color(30, 30, 30)
    for i, m in enumerate(modules):
        laenge = (
            m.get("sonder_laenge", "?")
            if m.get("laenge_typ") == "SONDERBAU"
            else m.get("laenge_typ", "")
        )
        pdf.set_fill_color(255, 245, 242) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        pdf.cell(12, 6, txt=str(i + 1),             fill=True)
        pdf.cell(45, 6, txt=m.get("typ", ""),        fill=True)
        pdf.cell(32, 6, txt=str(laenge),             fill=True)
        pdf.cell(58, 6, txt=m.get("technik", ""),    fill=True)
        pdf.cell(52, 6, txt=m.get("unterbau", ""),   fill=True)
        pdf.cell(0,  6, txt=m.get("peripherie", ""), fill=True, ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 7, txt="Grafische Anlagenoebersicht (massstabsgetreu):", ln=True)
    total_mm = sum(
        m.get("sonder_laenge", 1500) if m.get("laenge_typ") == "SONDERBAU"
        else int(m.get("laenge_typ", "1770 mm").split()[0])
        for m in modules
    ) if modules else 1
    AVAILABLE_W = 267.0
    BLOCK_H     = 28.0
    X_START     = 10.0
    y_grafik    = pdf.get_y() + 2
    PDF_COLORS  = {
        "Warmbuffet":    (205, 78, 74),
        "Kaltbuffet":    (58, 168, 205),
        "Front-Cooking": (218, 155, 50),
        "Neutral":       (125, 125, 125),
        "Kasse":         (72, 165, 72),
    }
    x_cursor = X_START
    for i, m in enumerate(modules):
        laenge_mm = (
            m.get("sonder_laenge", 1500) if m.get("laenge_typ") == "SONDERBAU"
            else int(m.get("laenge_typ", "1770 mm").split()[0])
        )
        block_w = max(4.0, (laenge_mm / total_mm) * AVAILABLE_W)
        r, g, b = PDF_COLORS.get(m.get("typ", "Neutral"), (125, 125, 125))
        pdf.set_fill_color(r, g, b)
        pdf.set_draw_color(255, 255, 255)
        pdf.set_line_width(0.4)
        pdf.rect(x_cursor, y_grafik, block_w, BLOCK_H, style="FD")
        pdf.set_draw_color(min(r+60,255), min(g+60,255), min(b+60,255))
        pdf.set_line_width(0.8)
        pdf.line(x_cursor+0.4, y_grafik+0.4, x_cursor+block_w-0.4, y_grafik+0.4)
        pdf.set_font("Arial", 'B', 7)
        pdf.set_text_color(255, 255, 255)
        nr_txt = f"M{i+1}"
        nr_w = pdf.get_string_width(nr_txt)
        if block_w > nr_w + 1:
            pdf.set_xy(x_cursor+(block_w-nr_w)/2, y_grafik+4)
            pdf.cell(nr_w+0.5, 4, txt=nr_txt)
        pdf.set_font("Arial", '', 5.5)
        typ_txt = m.get("typ", "")
        while typ_txt and pdf.get_string_width(typ_txt) > block_w - 1:
            typ_txt = typ_txt[:-1]
        tw = pdf.get_string_width(typ_txt)
        if block_w > tw + 1:
            pdf.set_xy(x_cursor+(block_w-tw)/2, y_grafik+10)
            pdf.cell(tw+0.5, 4, txt=typ_txt)
        pdf.set_font("Arial", 'I', 5)
        tec_txt = m.get("technik", "")
        while tec_txt and pdf.get_string_width(tec_txt) > block_w - 1:
            tec_txt = tec_txt[:-1]
        tcw = pdf.get_string_width(tec_txt)
        if block_w > tcw + 1:
            pdf.set_xy(x_cursor+(block_w-tcw)/2, y_grafik+17)
            pdf.cell(tcw+0.5, 3, txt=tec_txt)
        if m.get("peripherie") == "Tablettrutsche":
            pdf.set_fill_color(232, 71, 28)
            pdf.set_draw_color(232, 71, 28)
            pdf.rect(x_cursor, y_grafik+BLOCK_H, block_w, 3.5, style="F")
        elif m.get("peripherie") == "Verbreiterte Abdeckung":
            pdf.set_fill_color(40, 40, 40)
            pdf.set_draw_color(40, 40, 40)
            pdf.rect(x_cursor, y_grafik+BLOCK_H, block_w, 5.0, style="F")
        y_dim = y_grafik + BLOCK_H + 7
        pdf.set_draw_color(150, 150, 150)
        pdf.set_line_width(0.2)
        pdf.line(x_cursor+0.5, y_dim-1, x_cursor+0.5, y_dim+2.5)
        pdf.line(x_cursor+block_w-0.5, y_dim-1, x_cursor+block_w-0.5, y_dim+2.5)
        pdf.line(x_cursor+0.5, y_dim+1, x_cursor+block_w-0.5, y_dim+1)
        pdf.set_font("Arial", '', 5.5)
        pdf.set_text_color(80, 80, 80)
        dim_txt = f"{laenge_mm}"
        dw = pdf.get_string_width(dim_txt)
        if block_w > dw + 1:
            pdf.set_fill_color(255, 255, 255)
            pdf.rect(x_cursor+(block_w-dw)/2-0.5, y_dim-0.5, dw+1, 3.5, style="F")
            pdf.set_xy(x_cursor+(block_w-dw)/2, y_dim-0.5)
            pdf.cell(dw+0.5, 3.5, txt=dim_txt)
        x_cursor += block_w
    y_gesamt = y_grafik + BLOCK_H + 14
    pdf.set_draw_color(232, 71, 28)
    pdf.set_line_width(0.3)
    pdf.line(X_START, y_gesamt, X_START+AVAILABLE_W, y_gesamt)
    pdf.set_font("Arial", 'B', 7)
    pdf.set_text_color(232, 71, 28)
    pdf.set_xy(X_START, y_gesamt+1)
    pdf.cell(0, 4, txt=f"Gesamtlaenge Anlage: {total_mm:,} mm  ({total_mm/1000:.2f} m)", ln=True)
    pdf.set_font("Arial", '', 6.5)
    pdf.set_text_color(80, 80, 80)
    pdf.set_xy(X_START+80, y_gesamt+1)
    pdf.cell(20, 4, txt="Legende: ", ln=False)
    for typ, (r, g, b) in PDF_COLORS.items():
        pdf.set_fill_color(r, g, b)
        pdf.set_draw_color(80, 80, 80)
        pdf.set_line_width(0.1)
        cx, cy = pdf.get_x(), pdf.get_y()
        if cx + 25 < X_START + AVAILABLE_W:
            pdf.rect(cx, cy+0.5, 3.5, 3.5, style="FD")
            pdf.set_text_color(80, 80, 80)
            pdf.set_xy(cx+4.5, cy)
            pdf.cell(pdf.get_string_width(typ)+3, 4, txt=typ, ln=False)
    pdf.set_y(y_gesamt+6)
    pdf.set_x(X_START)
    pdf.set_font("Arial", 'I', 6)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 4,
        txt="  Roter Streifen = Tablettrutsche   |   "
            "Dunkelgrauer Streifen = Verbreiterte Abdeckung", ln=True)
    pdf.set_y(y_gesamt+12)
    pdf.set_draw_color(220, 220, 220)
    pdf.set_line_width(0.3)
    pdf.line(X_START, pdf.get_y(), X_START+AVAILABLE_W, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5,
        txt="Alle Angaben vorbehaltlich technischer Aenderungen. "
            "Dieses Dokument stellt kein verbindliches Angebot dar.", ln=True)
    return pdf.output(dest='S').encode('latin-1')


# ==========================================
# 3. APP SETUP & LOGIN
# ==========================================

st.set_page_config(
    page_title="Rieber Solutionfinder",
    page_icon="🍽️",
    layout="wide",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': '© Rieber GmbH'}
)
inject_apple_icon()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "home"
if "buffet_modules" not in st.session_state:
    st.session_state.buffet_modules = []

if not st.session_state.authenticated:
    logo_html = get_logo_html("80px")
    login_card = (
        '<style>' + CSS + '</style>'
        '<div style="max-width:360px;margin:60px auto 0;background:white;padding:36px;'
        'border-radius:20px;box-shadow:0 4px 20px rgba(0,0,0,0.1);text-align:center;">'
        + logo_html +
        '<p style="font-size:1em;font-weight:700;color:#333;letter-spacing:0.1em;'
        'text-transform:uppercase;margin-top:16px;padding-top:14px;'
        'border-top:1px solid #f0f0f0;">Solutionfinder</p>'
        '</div>'
    )
    st.markdown(login_card, unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.5, 1])
    with mid:
        pw = st.text_input("pw", type="password", label_visibility="collapsed",
                           placeholder="Passwort eingeben …")
        if st.button("Anmelden", use_container_width=True):
            if pw == "Rieber":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Falsches Passwort.")
    st.stop()


# ==========================================
# 4. NAVIGATION & ROUTING
# ==========================================

if st.session_state.page == "home":
    set_design()
    st.markdown('<div class="eingabe-box" style="text-align:center;">', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-label" style="font-size:1.2em;margin-bottom:20px;">'
        'Bitte wählen Sie ein Tool:</p>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🍽️ Bedarfsanalyse\n(Solutionfinder)"):
            st.session_state.page = "solutionfinder"
            st.rerun()
    with col2:
        if st.button("⚡ Bain Marie\nErsparnis-Berechnung"):
            st.session_state.page = "ersparnis"
            st.rerun()
    with col3:
        if st.button("🍱 Rolling Buffet\nAnlagenplanung"):
            st.session_state.page = "rolling"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


elif st.session_state.page == "solutionfinder":
    set_design()
    c_nav1, c_nav2 = st.columns([1, 4])
    with c_nav1:
        if st.button("← Zurück zum Menü"):
            st.session_state.page = "home"
            st.rerun()
    st.markdown('<div class="eingabe-box">', unsafe_allow_html=True)
    kunde = st.text_input("Kundenname", placeholder="z. B. Muster GmbH")
    n_loc = st.number_input("Anzahl Standorte", min_value=1, value=1)
    total_p = 0
    loc_reports = []
    for i in range(int(n_loc)):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input(f"Name Standort {i+1}", value=f"Standort {i+1}")
        with c2:
            count = st.number_input(f"Teilnehmer Standort {i+1}", min_value=1, value=50)
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
    st.markdown('<p class="section-label">Bedarf &amp; Investition</p>', unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)
    r1.markdown(
        f'<div class="result-card"><p class="metric-title">{tp_m}</p>'
        f'<p class="metric-value">{t_tp}</p><p class="metric-price">à {n_tp:.2f} €</p></div>',
        unsafe_allow_html=True)
    r2.markdown(
        f'<div class="result-card"><p class="metric-title">GN 1/1 65mm</p>'
        f'<p class="metric-value">{t_gn}</p><p class="metric-price">à {n_gn:.2f} €</p></div>',
        unsafe_allow_html=True)
    r3.markdown(
        f'<div class="result-card"><p class="metric-title">Steckdeckel</p>'
        f'<p class="metric-value">{t_gn}</p><p class="metric-price">à {n_dk:.2f} €</p></div>',
        unsafe_allow_html=True)
    r4.markdown(
        f'<div class="result-card"><p class="metric-title">Rolliport</p>'
        f'<p class="metric-value">{t_rp}</p><p class="metric-price">à {n_rp:.2f} €</p></div>',
        unsafe_allow_html=True)
    st.markdown(
        f'<div class="total-card"><p class="total-label">Gesamtinvestition</p>'
        f'<p class="total-value">{inv:,.2f} € Netto</p></div>', unsafe_allow_html=True)
    st.markdown('<p class="section-label">ROI &amp; Nachhaltigkeit</p>', unsafe_allow_html=True)
    o1, o2, o3, o4 = st.columns(4)
    o1.markdown(
        f'<div class="roi-card"><div class="card-icon">♻️</div>'
        f'<p class="metric-title">Einweg / Jahr</p>'
        f'<p class="metric-value" style="color:#d9534f;">{roi_j:,.0f} €</p></div>',
        unsafe_allow_html=True)
    o2.markdown(
        f'<div class="roi-card"><div class="card-icon">🪙</div>'
        f'<p class="metric-title">Amortisation</p>'
        f'<p class="metric-value">{amo:.1f} '
        f'<span style="font-size:.45em;color:#888;font-weight:600;">Mon.</span></p></div>',
        unsafe_allow_html=True)
    o3.markdown(
        f'<div class="esg-card"><div class="card-icon">🥤</div>'
        f'<p class="metric-title">Plastik gespart</p>'
        f'<p class="metric-value" style="color:#2a9d8f;">{pla:,.0f} '
        f'<span style="font-size:.45em;color:#888;font-weight:600;">kg/J.</span></p></div>',
        unsafe_allow_html=True)
    o4.markdown(
        f'<div class="esg-card"><div class="card-icon">🌫️</div>'
        f'<p class="metric-title">CO₂ reduziert</p>'
        f'<p class="metric-value" style="color:#2a9d8f;">{co2:,.0f} '
        f'<span style="font-size:.45em;color:#888;font-weight:600;">kg/J.</span></p></div>',
        unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    pdf_b = create_pdf(v_sys, bereich, komp, total_p, tage, loc_reports,
                       tp_m, t_tp, t_gn, t_rp, n_tp, n_gn, n_dk, n_rp,
                       inv, roi_j, amo, pla, co2, kunde)
    st.download_button("Bedarfsanalyse als PDF speichern", data=pdf_b,
                       file_name="Rieber_Bedarfsanalyse.pdf", mime="application/pdf")


elif st.session_state.page == "ersparnis":
    set_design()
    LOGIK_DATEN_BM = {
        "Trocken Bain Marie": {"ersparnis": 490.34, "prozent": 81},
        "Varithek 800":        {"ersparnis": 496.06, "prozent": 82},
        "EST Infrarot":        {"ersparnis": 515.96, "prozent": 85},
    }
    c_nav1, c_nav2 = st.columns([1, 4])
    with c_nav1:
        if st.button("← Zurück zum Menü"):
            st.session_state.page = "home"
            st.rerun()
    st.markdown('<p class="section-label">Bain Marie Ersparnis-Berechnung</p>',
                unsafe_allow_html=True)
    st.markdown('<div class="eingabe-box">', unsafe_allow_html=True)
    k_name = st.text_input("Kundenname", placeholder="z. B. Muster GmbH")
    anzahl = st.number_input("Anzahl zu ersetzender Wasser-Bain-Maries", min_value=1, value=1)
    system = st.selectbox("Auswahl neue Rieber Technik", options=list(LOGIK_DATEN_BM.keys()))
    st.markdown('</div>', unsafe_allow_html=True)
    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        berechnen_click = st.button("Ersparnis berechnen")
    if berechnen_click:
        daten = LOGIK_DATEN_BM[system]
        gesamt = anzahl * daten["ersparnis"]
        st.markdown(
            f'<div class="total-card" style="margin-top:30px;">'
            f'<p class="total-label">Ergebnis für {k_name if k_name else "Kunde"}</p>'
            f'<p class="total-value">+ {gesamt:,.2f} € / Jahr</p>'
            f'<p style="margin-top:15px;font-weight:600;font-size:1.1em;">'
            f'Stromreduktion: {daten["prozent"]}%</p></div>', unsafe_allow_html=True)
        pdf_data_bm = create_pdf_bain_marie(
            k_name if k_name else "Kunde",
            anzahl, system, daten["ersparnis"], gesamt, daten["prozent"])
        st.download_button(
            label="Bain Marie Berechnung als PDF speichern",
            data=pdf_data_bm,
            file_name=f"Rieber_Bain_Marie_Ersparnis_{k_name if k_name else 'Kunde'}.pdf",
            mime="application/pdf")


elif st.session_state.page == "rolling":
    set_design("Rolling Buffet")
    c_nav1, _ = st.columns([1, 4])
    with c_nav1:
        if st.button("← Zurück zum Menü"):
            st.session_state.page = "home"
            st.rerun()

    # Schritt 1: Globales Setup
    st.markdown('<div class="eingabe-box">', unsafe_allow_html=True)
    st.markdown('<p class="section-label">Schritt 1: Globales Setup</p>', unsafe_allow_html=True)
    kunde_rolling = st.text_input("Kundenname", placeholder="z. B. Muster GmbH", key="rolling_kunde")
    c1, c2, c3 = st.columns(3)
    with c1:
        mob = st.selectbox("Mobilitaet",
            ["Fahrbar (Standard)", "Fahrbar mit abnehmbarer Sockelblende", "Stationaer"])
        auf = st.selectbox("Aufstellung", ["Freistehend", "Wandstehend", "Solo (Insel)"])
    with c2:
        abd = st.selectbox("Abdeckung", ["Edelstahl", "Granit", "Kunststein"])
        abd_f = (st.text_input("Farbe Abdeckung", placeholder="z.B. Bianco Carrara")
                 if abd != "Edelstahl" else "")
    with c3:
        des = st.selectbox("Design", ["Standard (Schwarz/Grau)", "Sonderfarbe"])
        des_f = (st.text_input("Farbcode", placeholder="z.B. RAL 9010")
                 if des == "Sonderfarbe" else "")
    st.markdown('</div>', unsafe_allow_html=True)

    # Schritt 2: Module
    st.markdown('<div class="eingabe-box">', unsafe_allow_html=True)
    st.markdown('<p class="section-label">Schritt 2: Module konfigurieren</p>', unsafe_allow_html=True)
    to_delete = None
    for i, m in enumerate(st.session_state.buffet_modules):
        col_m1, col_m2, col_m3, col_m4 = st.columns([2, 2, 2, 1])
        m["typ"] = col_m1.selectbox(f"Typ (M{i+1})",
            ["Warmbuffet", "Kaltbuffet", "Front-Cooking", "Neutral", "Kasse"],
            key=f"typ_{m['id']}")
        m["laenge_typ"] = col_m2.selectbox(f"Laenge (M{i+1})",
            ["1270 mm", "1770 mm", "2270 mm", "SONDERBAU"], key=f"laenge_{m['id']}")
        if m["laenge_typ"] == "SONDERBAU":
            m["sonder_laenge"] = col_m2.number_input("Sonderlaenge (mm)", min_value=400,
                value=int(m.get("sonder_laenge", 1500)), key=f"sonder_{m['id']}")
        m["peripherie"] = col_m3.selectbox(f"Gaesteseite (M{i+1})",
            ["Keine", "Tablettrutsche", "Verbreiterte Abdeckung"], key=f"peri_{m['id']}")
        if col_m4.button("🗑️", key=f"del_{m['id']}"):
            to_delete = i
        with st.expander(f"⚙️ Technik & Unterbau (M{i+1})"):
            tc1, tc2 = st.columns(2)
            if m["typ"] == "Warmbuffet":
                m["technik"] = tc1.selectbox("Technik",
                    ["Wasserbad (Bain-Marie)", "Varithek Ceran", "Varithek Infrarot"],
                    key=f"tc_{m['id']}_{m['typ']}")
                m["unterbau"] = tc2.selectbox("Unterbau",
                    ["Offen", "Schrank Neutral", "Schrank Gewaermt"],
                    key=f"uc_{m['id']}_{m['typ']}")
            elif m["typ"] == "Kaltbuffet":
                m["technik"] = tc1.selectbox("Technik",
                    ["Kuehlwanne tief (210mm)", "Kuehlwanne flach (45mm)", "Granit gekuehlt"],
                    key=f"tc_{m['id']}_{m['typ']}")
                m["unterbau"] = tc2.selectbox("Unterbau",
                    ["Offen", "Schrank Neutral", "Schrank Gekuehlt"],
                    key=f"uc_{m['id']}_{m['typ']}")
            elif m["typ"] == "Front-Cooking":
                m["technik"] = tc1.selectbox("Technik", ["Varithek Systemtraeger"],
                    key=f"tc_{m['id']}_{m['typ']}")
                m["unterbau"] = tc2.selectbox("Unterbau", ["Offen", "Schrank Neutral"],
                    key=f"uc_{m['id']}_{m['typ']}")
            else:
                tc1.markdown("<span style='font-size:14px;color:#888;'>Technik: <b>Neutral / Ohne</b></span>",
                             unsafe_allow_html=True)
                m["technik"] = "Ohne"
                m["unterbau"] = tc2.selectbox("Unterbau", ["Offen", "Flügeltüren"],
                    key=f"uc_{m['id']}_{m['typ']}")
        st.markdown("<hr style='border:none;border-top:1px solid #f0f0f0;margin:6px 0 12px;'>",
                    unsafe_allow_html=True)
    if to_delete is not None:
        st.session_state.buffet_modules.pop(to_delete)
        st.rerun()
    if st.button("➕ Modul hinzufügen"):
        st.session_state.buffet_modules.append({
            "id": str(uuid.uuid4()), "typ": "Warmbuffet", "laenge_typ": "1770 mm",
            "sonder_laenge": 1500, "peripherie": "Keine",
            "technik": "Wasserbad (Bain-Marie)", "unterbau": "Offen",
        })
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Schritt 3: Draufsicht & Export
    if st.session_state.buffet_modules:
        st.markdown('<div class="eingabe-box">', unsafe_allow_html=True)
        st.markdown('<p class="section-label">Schritt 3: Draufsicht &amp; Export</p>',
                    unsafe_allow_html=True)

        FARB_MAP = {
            "Warmbuffet":    "#cd4e4a",
            "Kaltbuffet":    "#3aa8cd",
            "Front-Cooking": "#da9f32",
            "Neutral":       "#888888",
            "Kasse":         "#48a548",
        }
        TYP_ICONS = {
            "Warmbuffet":    "🔥",
            "Kaltbuffet":    "❄️",
            "Front-Cooking": "👨‍🍳",
            "Neutral":       "⬜",
            "Kasse":         "💳",
        }

        total_mm_display = sum(
            m["sonder_laenge"] if m["laenge_typ"] == "SONDERBAU"
            else int(m["laenge_typ"].split()[0])
            for m in st.session_state.buffet_modules
        )
        n_mod = len(st.session_state.buffet_modules)

        plan_parts = []
        plan_parts.append(
            f'<div style="background:#fff;border-radius:14px;padding:20px;border:1px solid #e8e0dc;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">'
            f'<span style="font-size:0.7em;font-weight:700;color:#999;text-transform:uppercase;letter-spacing:1px;">'
            f'Draufsicht \u2013 {n_mod} Modul{"e" if n_mod != 1 else ""}</span>'
            f'<span style="font-size:0.75em;color:#E8471C;font-weight:700;">'
            f'Gesamt:&nbsp;{total_mm_display:,}&nbsp;mm&nbsp;|&nbsp;{total_mm_display/1000:.2f}&nbsp;m</span>'
            f'</div>'
            f'<div style="display:flex;flex-direction:row;align-items:flex-end;overflow-x:auto;'
            f'padding:16px 12px 32px;gap:3px;'
            f'background:repeating-linear-gradient(90deg,rgba(232,71,28,0.04) 0,rgba(232,71,28,0.04) 1px,transparent 1px,transparent 24px),'
            f'repeating-linear-gradient(rgba(232,71,28,0.04) 0,rgba(232,71,28,0.04) 1px,transparent 1px,transparent 24px),#f9f7f6;'
            f'border:1.5px solid #ddd;border-radius:10px;">'
        )

        for idx, m in enumerate(st.session_state.buffet_modules):
            real_l = (m["sonder_laenge"] if m["laenge_typ"] == "SONDERBAU"
                      else int(m["laenge_typ"].split()[0]))
            bg   = FARB_MAP.get(m["typ"], "#888888")
            w_px = max(72, real_l // 10)
            icon = TYP_ICONS.get(m["typ"], "")
            peri = m.get("peripherie", "Keine")
            peri_html = ""
            if peri == "Tablettrutsche":
                peri_html = ('<div style="position:absolute;bottom:-8px;left:0;right:0;'
                             'height:6px;background:#E8471C;border-radius:0 0 3px 3px;'
                             'box-shadow:0 2px 4px rgba(232,71,28,0.4);"></div>')
            elif peri == "Verbreiterte Abdeckung":
                peri_html = ('<div style="position:absolute;bottom:-10px;left:0;right:0;'
                             'height:10px;background:#2a2a2a;border-radius:0 0 3px 3px;"></div>')
            plan_parts.append(
                f'<div style="position:relative;display:flex;flex-direction:column;'
                f'align-items:center;justify-content:center;color:white;font-weight:700;'
                f'font-size:0.78em;text-align:center;border-radius:6px 6px 0 0;'
                f'border:1.5px solid rgba(0,0,0,0.18);'
                f'box-shadow:0 4px 10px rgba(0,0,0,0.18),inset 0 1px 0 rgba(255,255,255,0.22);'
                f'min-width:{w_px}px;height:120px;padding:8px 6px 12px;'
                f'background:linear-gradient(160deg,{bg}ee 0%,{bg}bb 100%);">'
                f'<div style="font-size:1.5em;margin-bottom:4px;line-height:1;">{icon}</div>'
                f'<div style="font-size:0.7em;opacity:0.8;margin-bottom:2px;">M{idx+1}</div>'
                f'<div style="font-size:0.85em;font-weight:800;">{m["typ"]}</div>'
                f'<div style="font-size:0.68em;margin-top:5px;background:rgba(0,0,0,0.18);'
                f'border-radius:3px;padding:2px 5px;">{real_l}&nbsp;mm</div>'
                f'{peri_html}</div>'
            )

        plan_parts.append('</div>')
        plan_parts.append(
            '<div style="display:flex;gap:12px;margin-top:14px;flex-wrap:wrap;'
            'padding-top:12px;border-top:1px solid #f0f0f0;align-items:center;">'
            '<span style="font-size:0.7em;font-weight:700;color:#aaa;'
            'text-transform:uppercase;letter-spacing:.8px;">Legende</span>'
        )
        for typ, farbe in FARB_MAP.items():
            ic = TYP_ICONS.get(typ, "")
            plan_parts.append(
                f'<span style="display:flex;align-items:center;gap:5px;font-size:0.78em;color:#444;">'
                f'<span style="width:12px;height:12px;border-radius:3px;background:{farbe};'
                f'display:inline-block;box-shadow:0 1px 3px rgba(0,0,0,0.2);"></span>'
                f'{ic}&nbsp;{typ}</span>'
            )
        plan_parts.append(
            '<span style="display:flex;align-items:center;gap:5px;font-size:0.78em;color:#444;'
            'margin-left:6px;padding-left:6px;border-left:1px solid #eee;">'
            '<span style="width:22px;height:5px;background:#E8471C;display:inline-block;'
            'border-radius:2px;"></span>Tablettrutsche</span>'
            '<span style="display:flex;align-items:center;gap:5px;font-size:0.78em;color:#444;">'
            '<span style="width:22px;height:8px;background:#2a2a2a;display:inline-block;'
            'border-radius:2px;"></span>Verbreiterte Abdeckung</span>'
        )
        plan_parts.append('</div></div>')

        st.markdown("".join(plan_parts), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        glob_data = {
            "kunde": kunde_rolling, "mobilitaet": mob,
            "abdeckung": abd, "abdeckung_farbe": abd_f,
            "design": des, "design_farbe": des_f,
        }
        pdf_rb = create_pdf_rolling_buffet(glob_data, st.session_state.buffet_modules)
        fname = (f"Rieber_RollingBuffet_{kunde_rolling.replace(' ', '_')}.pdf"
                 if kunde_rolling else "Rieber_RollingBuffet.pdf")
        st.download_button("Anlagenplanung als PDF speichern",
                           data=pdf_rb, file_name=fname, mime="application/pdf")
        st.markdown('</div>', unsafe_allow_html=True)
