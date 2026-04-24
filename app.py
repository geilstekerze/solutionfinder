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
".plan-rutsche { position: absolute; bottom: -8px; left:
