import streamlit as st
import openai
from fpdf import FPDF
import requests
from io import BytesIO
import re

# --- KONFIGURACJA ---
st.set_page_config(page_title="Oniro - Dream Portal", page_icon="🌙", layout="wide")

# Pamięć sesji do blokady wielokrotnego użytku
if 'access_verified' not in st.session_state:
    st.session_state['access_verified'] = False
if 'balloons_done' not in st.session_state:
    st.session_state['balloons_done'] = False

# --- DESIGN CSS ---
st.markdown("""
    <style>
    .main { background: #0f0f1b; color: #e0e0e0; }
    .stTextArea textarea { background-color: #161b22; color: white; border: 1px solid #4c1d95; }
    .tier-card { padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.02); }
    .premium-active { border: 2px solid #ffd700; background: rgba(167, 139, 250, 0.05); }
    .gold-text { color: #ffd700; font-weight: bold; font-size: 16px; }
    .dream-report { background: rgba(255, 255, 255, 0.05); padding: 30px; border-radius: 20px; border-left: 5px solid #6d28d9; line-height: 1.8; font-size: 18px; }
    h1 { color: #a78bfa; text-align: center; font-size: 50px; text-shadow: 2px 2px 15px rgba(109, 40, 217, 0.6); }
    </style>
""", unsafe_allow_html=True)

# --- KLASA PDF (BEZ ZMIAN) ---
class DreamPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font('Arial', 'B', 24); self.set_text_color(109, 40, 217)
            self.cell(0, 25, 'ONIRO - YOUR VISION', 0, 1, 'C'); self.ln(10)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()} | Oniro Dream Analysis', 0, 0, 'C')

def create_pro_pdf(analysis, image_url):
    pdf = DreamPDF(); pdf.set_auto_page_break(auto=True, margin=20); pdf.add_page()
    try:
        res = requests.get(image_url); img = BytesIO(res.content)
        with open("temp_img.png", "wb") as f: f.write(img.getbuffer())
        pdf.image("temp_img.png", x=25, y=45, w=160); pdf.set_y(210)
    except: pdf.set_y(40)
    def to_latin(t):
        rep = {'ą':'a','ć':'c','ę':'e','ł':'l','ń':'n','ó':'o','ś':'s','ź':'z','ż':'z'}
        for k,v in rep.items(): t = t.replace(k,v).replace(k.upper(),v.upper())
        return re.sub(r'[^\x00-\x7f]', '', t)
    for line in analysis.split('\n'):
        if not line.strip(): continue
        txt = to_latin(line)
        pdf.set_font("Arial", size=11); pdf.multi_cell(0, 8, txt=txt); pdf.ln(2)
    return pdf.output(dest='S').encode('latin-1')

def get_ai_response(text, api_key, mode):
    client = openai.OpenAI(api_key=api_key)
    sys_prompt = "You are Oniro Pro. Deep mystical analysis in Polish." if mode == "Premium ✨" else "Short 5 sentences in Polish."
    analysis = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": text}]).choices[0].message.content
    img_url = client.images.generate(model="dall-e-3", prompt=text, quality="hd" if mode == "Premium ✨" else "standard").data[0].url
    return analysis, img_url

def main():
    st.markdown("<h1>🌙 ONIRO</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns([1.6, 1])
    try: api_key = st.secrets["OPENAI_API_KEY"]
    except: api_key = None
    
    with col2:
        st.markdown("### ✨ Wybierz Poziom")
        mode = st.radio("Mode:", ["Standard", "Premium ✨"], label_visibility="collapsed")
        
        if mode == "Standard":
            st.markdown("<div class='tier-card'>• Wizja Standard<br>• Analiza podstawowa</div>", unsafe_allow_html=True)
            st.session_state['access_verified'] = True
        else:
            st.markdown(f"""
                <div class='tier-card premium-active'>
                <span class='gold-text'>★ Obraz Ultra HD | ★ PDF</span><br>
                <h2 style='color:#ffd700; text-align:center;'>9.00 PLN</h2>
                <a href="https://buy.stripe.com/eVqdR25as8jU8FJ4hs4Ni01" target="_blank" style="text-decoration:none;">
                <div style="background:#ffd700;color:black;padding:12px;border-radius:10px;font-weight:bold;text-align:center;">KUP DOSTĘP</div></a></div>
            """, unsafe_allow_html=True)
            
            # UNIKALNE POLE HASŁA Z RESETEM
            password = st.text_input("Wpisz kod i naciśnij Enter:", type="password", key="pass_input")
            
            if password == "MAGIA2026":
                if not st.session_state['balloons_done']:
                    st.balloons()
                    st.session_state['balloons_done'] = True
                st.success("Kod poprawny! Możesz teraz użyć przycisku DEKODUJ SEN.")
                st.session_state['access_verified'] = True
            elif password != "":
                st.error("Błędny kod.")
                st.session_state['access_verified'] = False

    with col1:
        dream_text = st.text_area("Opisz swój sen...", height=300)
        if st.button("✨ DEKODUJ SEN"):
            if mode == "Premium ✨" and not st.session_state.get('access_verified', False):
                st.warning("Najpierw wpisz poprawny kod!")
            elif api_key and dream_text:
                with st.spinner("Oniro pracuje..."):
                    try:
                        ans, img = get_ai_response(dream_text, api_key, mode)
                        st.image(img, use_container_width=True)
                        st.markdown(f"<div class='dream-report'>{ans}</div>", unsafe_allow_html=True)
                        
                        if mode == "Premium ✨":
                            st.download_button("📥 POBIERZ PDF", data=create_pro_pdf(ans, img), file_name="Oniro.pdf")
                            # --- BLOKADA PO UŻYCIU ---
                            st.session_state['access_verified'] = False
                            st.session_state['balloons_done'] = False
                            st.info("Dostęp Premium został zużyty dla tej wizji. Aby zdekodować kolejny sen, wpisz kod ponownie.")
                    except Exception as e:
                        st.error(f"Błąd: {e}")

if __name__ == "__main__":
    main()
