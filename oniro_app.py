import streamlit as st
import openai
from fpdf import FPDF
import requests
from io import BytesIO
import re

# --- KONFIGURACJA ---
st.set_page_config(page_title="Oniro - Dream Portal", page_icon="🌙", layout="wide")

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


# --- PROFESJONALNA KLASA PDF ---
class DreamPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font('Arial', 'B', 24)
            self.set_text_color(109, 40, 217)
            self.cell(0, 25, 'ONIRO - YOUR VISION', 0, 1, 'C')
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()} | Oniro Dream Analysis', 0, 0, 'C')


def create_pro_pdf(analysis, image_url):
    pdf = DreamPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # 1. OBRAZ (Wycentrowany, wysoka jakosc pozycjonowania)
    try:
        response = requests.get(image_url)
        img_data = BytesIO(response.content)
        with open("temp_img.png", "wb") as f:
            f.write(img_data.getbuffer())
        pdf.image("temp_img.png", x=25, y=45, w=160)
        pdf.set_y(210)
    except:
        pdf.set_y(40)

    # 2. KONWERTER ZNAKOW (Zastepuje polskie litery)
    def to_latin(t):
        t = t.replace('**', '').replace('##', '').replace('#', '')
        rep = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
               'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'}
        for k, v in rep.items(): t = t.replace(k, v)
        return re.sub(r'[^\x00-\x7f]', '', t)

    # 3. TRESC
    lines = analysis.split('\n')
    for line in lines:
        if not line.strip(): continue
        txt = to_latin(line)

        # Detekcja naglowkow (np. ATMOSPHERE, SYMBOLS)
        if len(txt) < 40 and any(keyword in txt.upper() for keyword in ["ATMOSFERA", "SYMBOLE", "PRZESLANIE", "WIZJA"]):
            pdf.ln(8)
            pdf.set_font("Arial", 'B', 15)
            pdf.set_text_color(109, 40, 217)
            pdf.cell(0, 10, txt.strip().upper(), 0, 1, 'L')
            pdf.set_draw_color(109, 40, 217)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 50, pdf.get_y())
            pdf.ln(5)
        else:
            pdf.set_font("Arial", size=11)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(0, 8, txt=txt, align='J')
            pdf.ln(2)

    return pdf.output(dest='S').encode('latin-1')


# --- LOGIKA AI ---
def get_ai_response(text, api_key, mode):
    client = openai.OpenAI(api_key=api_key)

    if mode == "Premium ✨":
        sys_prompt = "You are Oniro Pro. Provide a deep, mystical, and long psychological analysis (400+ words). Use headers: ATMOSFERA, SYMBOLE, PRZESLANIE. Respond in Polish."
        quality = "hd"
    else:
        sys_prompt = "You are Oniro Standard. Give a wise but short 5-sentence analysis in Polish. Leave the user wanting more."
        quality = "standard"

    # Analiza
    analysis = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": text}]
    ).choices[0].message.content

    # Obraz (zawsze bezpieczny prompt)
    img_prompt = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "Convert dream to safe DALL-E 3 prompt. Surrealism, 8k, Cinematic."},
                  {"role": "user", "content": text}]
    ).choices[0].message.content

    img_url = client.images.generate(model="dall-e-3", prompt=img_prompt, quality=quality, size="1024x1024").data[0].url

    return analysis, img_url


# --- INTERFEJS ---
def main():
    st.markdown("<h1>🌙 ONIRO</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.6, 1])

    with col2:
        st.markdown("### ✨ Wybierz Poziom")
        mode = st.radio("Mode:", ["Standard", "Premium ✨"], label_visibility="collapsed")

        if mode == "Standard":
            st.markdown("<div class='tier-card'>• Wizja Standard<br>• Analiza podstawowa<br>✕ Brak PDF</div>",
                        unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class='tier-card premium-active'>
                <span class='gold-text'>★ Twój sen jako obraz Ultra HD</span><br>
                <span class='gold-text'>★ Pełna mapa Twoich emocji i symboli</span><br>
                <span class='gold-text'>★ Elegancki Raport PDF do zachowania</span><br>
                <span class='gold-text'>★ Klucz do wewnętrznego świata</span><br><br>
                <h2 style='color:#ffd700; text-align:center;'>9.00 PLN</h2>
                </div>
            """, unsafe_allow_html=True)

        api_key = st.secrets["OPENAI_API_KEY"]

    with col1:
        dream_text = st.text_area("Opisz swoją wizję...", height=300)

        if st.button("✨ DEKODUJ SEN"):
            if api_key and dream_text:
                with st.spinner("Oniro analizuje Twoją duszę..."):
                    try:
                        analysis, img_url = get_ai_response(dream_text, api_key, mode)
                        st.image(img_url, use_container_width=True)
                        st.markdown(f"<div class='dream-report'>{analysis}</div>", unsafe_allow_html=True)

                        if mode == "Premium ✨":
                            pdf = create_pro_pdf(analysis, img_url)
                            st.download_button("📥 POBIERZ RAPORT PREMIUM PDF", data=pdf, file_name="Oniro_Report.pdf",
                                               mime="application/pdf")
                    except Exception as e:
                        st.error(f"Error: {e}")


if __name__ == "__main__":

    main()
