import streamlit as st
import pycountry
import plotly.graph_objects as go
import os
import base64 # Yerel görseli CSS içine gömmek için gerekli kütüphane

# --- 1. Sayfa Ayarları ve Başlık ---
st.set_page_config(layout="wide", page_title="Dünya Dillerinde Türkçenin İzi", initial_sidebar_state="expanded")

# --- 2. Yerel Arka Plan Görselini Hazırlama (Base64) ---
cwd = os.getcwd()
bg_image_path = os.path.join(cwd, "arkaplan.jpg")

# Eğer arkaplan.jpg varsa onu oku ve base64'e çevir, yoksa boş veya varsayılan bir renk bırak
if os.path.exists(bg_image_path):
    with open(bg_image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    bg_image_url = f"data:image/jpeg;base64,{encoded_string}"
else:
    # Dosya bulunamazsa hata vermemesi için boş bırakıyoruz
    bg_image_url = ""

# --- 3. Özel CSS ile Tarihi Tema, Yerel Filigran, Menü Gizleme ve Panel Sabitleme ---
custom_css = """
<style>
/* Sağ üstteki 'Share' menüsünü, header'ı ve footer'ı tamamen gizleme */
#MainMenu {visibility: hidden;}
header {visibility: hidden; height: 0px !important;}
footer {visibility: hidden;}

/* Yan paneli kapatma (ok) tuşunu ve 'keyboard_double' yazısını KESİN olarak gizleme */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
button[kind="header"] {
    display: none !important;
    opacity: 0 !important;
    pointer-events: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    position: absolute !important;
    z-index: -9999 !important;
}

/* Ana arka plan ve YEREL Piri Reis Haritası Filigranı */
[data-testid="stAppViewContainer"] {
    background-image: linear-gradient(rgba(253, 246, 227, 0.88), rgba(253, 246, 227, 0.88)), url("BG_IMAGE_URL_PLACEHOLDER");
    background-size: cover;
    background-position: center center;
    background-attachment: fixed;
}

/* Yan panel (Sidebar) arka planını yarı saydam yapıyoruz ve genişliği sabitliyoruz */
[data-testid="stSidebar"] {
    background-color: rgba(244, 236, 216, 0.95) !important;
    border-right: 2px solid #D3C6A6 !important;
    min-width: 320px !important;
    max-width: 320px !important; 
}

/* Genel metin stili */
html, body, p, span, div, li {
    font-family: 'Georgia', serif !important;
    color: #3E2723;
}
</style>
"""
# Hazırladığımız yerel base64 görselini CSS kodunun içine yerleştiriyoruz
custom_css = custom_css.replace("BG_IMAGE_URL_PLACEHOLDER", bg_image_url)
st.markdown(custom_css, unsafe_allow_html=True)

# --- 4. Başlık (HTML ile gerçek Türk Bayrağı resmi eklendi) ---
st.markdown(
    """
    <h1 style="display: flex; align-items: center; color: #8B0000; font-family: 'Georgia', serif; font-size: 2.5rem; margin-bottom: 20px;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/b/b4/Flag_of_Turkey.svg" width="55" style="margin-right: 15px; border-radius: 4px; box-shadow: 0px 2px 4px rgba(0,0,0,0.3);">
        Dünya Dillerinde Türkçenin İzi
    </h1>
    """, 
    unsafe_allow_html=True
)

# --- kelime.txt oku ---
words_path = os.path.join(cwd, "kelime.txt")
if not os.path.exists(words_path):
    st.error("kelime.txt bulunamadı. Lütfen app.py ile aynı klasöre koyun.")
    st.stop()

with open(words_path, "r", encoding="utf-8-sig") as f:
    raw = f.read()

# --- esnek parse fonksiyonu ---
def parse_text(text: str):
    mapping = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "," in line:
            key, rest = line.split(",", 1)
        elif ":" in line:
            key, rest = line.split(":", 1)
        else:
            continue
        key = key.strip()
        parts = [p.strip() for p in rest.split(";") if p.strip()]
        entries = []
        for p in parts:
            country = None
            local = None
            if "|" in p:
                country, local = p.split("|", 1)
            elif "," in p:
                country, local = p.split(",", 1)
            elif ":" in p:
                country, local = p.split(":", 1)
            else:
                country = p
            country = country.strip() if country else None
            local = local.strip() if local else None
            if country:
                entries.append({"country": country, "local": local})
        if entries:
            if key in mapping:
                mapping[key].extend(entries)
            else:
                mapping[key] = entries
    return mapping

mapping = parse_text(raw)
if not mapping:
    st.error("kelime.txt parse edilemedi veya uygun satır yok.")
    st.stop()

# --- basit Türkçe -> İngilizce ülke eşleme ---
tur_to_eng = {
    "türkiye": "Turkey", "almanya": "Germany", "fransa": "France",
    "italya": "Italy", "ispanya": "Spain", "ingiltere": "United Kingdom",
    "çin": "China", "hindistan": "India", "brezilya": "Brazil", "meksika": "Mexico",
    "japonya": "Japan", "rusya": "Russia", "kanada": "Canada", "avustralya": "Australia"
}

def name_to_iso3(name: str):
    if not name:
        return None
    nm = name.strip()
    eng = tur_to_eng.get(nm.lower())
    candidates = [eng] if eng else []
    candidates.append(nm)
    for cand in candidates:
        if not cand:
            continue
        try:
            c = pycountry.countries.get(name=cand)
            if c:
                return c.alpha_3
        except Exception:
            pass
    for cand in candidates:
        for c in pycountry.countries:
            if c.name.lower() == cand.lower():
                return c.alpha_3
            if hasattr(c, "official_name") and getattr(c, "official_name", "").lower() == cand.lower():
                return c.alpha_3
            if hasattr(c, "common_name") and getattr(c, "common_name", "").lower() == cand.lower():
                return c.alpha_3
    return None

# --- UI ve Tema Ayarları ---
st.sidebar.markdown("<h2 style='color: #8B0000; margin-top: 0;'>Ayarlar</h2>", unsafe_allow_html=True)

words = sorted(mapping.keys(), key=lambda s: s.lower())
selected = st.sidebar.selectbox("Bir kelime seçin", words)

highlight_color = st.sidebar.color_picker("Vurgulama rengi", "#8B0000") 
show_markers = st.sidebar.checkbox("Ülke işaretçileri göster", value=True)

# --- Proje Bilgileri (Yan Panel) ---
st.sidebar.markdown("---")
st.sidebar.markdown("**Okul:** Yahya Turan Fen Lisesi")
st.sidebar.markdown("**Danışman Öğretmen:** İsa TAŞ")
st.sidebar.markdown("**Öğrenciler:** <br>Meryem Rana GÖÇMEZ <br>Mehmet AÇIKGÖZ <br>Eylül ÖZELKARA", unsafe_allow_html=True)

st.sidebar.markdown("<br><br><br><div style='color: #2e8b57; font-weight: bold; font-family: sans-serif; font-size: 14px;'>Sistem Aktif 🟢</div>", unsafe_allow_html=True)

base_color = "#EAE0C8" 

# --- seçili kelimenin girdilerini işle ---
entries = mapping.get(selected, [])
iso_list = []
hover_texts = []
unrecognized = []
for e in entries:
    country_raw = e.get("country")
    local = e.get("local")
    iso = name_to_iso3(country_raw)
    if iso:
        iso_list.append(iso)
        if local:
            hover_texts.append(f"{country_raw}\nYerel karşılık: {local}")
        else:
            hover_texts.append(f"{country_raw}")
    else:
        eng = tur_to_eng.get(country_raw.lower())
        if eng:
            iso2 = name_to_iso3(eng)
            if iso2:
                iso_list.append(iso2)
                if local:
                    hover_texts.append(f"{country_raw}\nYerel karşılık: {local}")
                else:
                    hover_texts.append(f"{country_raw}")
                continue
        unrecognized.append(country_raw)

# --- tüm dünya ISO-3 listesi ---
all_iso = [c.alpha_3 for c in pycountry.countries]

# --- Plotly figür ---
fig = go.Figure()

# dünya tabanı
fig.add_trace(go.Choropleth(
    locations=all_iso,
    z=[0]*len(all_iso),
    locationmode="ISO-3",
    colorscale=[[0, base_color], [1, base_color]],
    showscale=False,
    marker_line_color="rgba(139, 0, 0, 0.2)",
    marker_line_width=0.3,
    hoverinfo="none",
    name="world"
))

# seçili ülkeler
if iso_list:
    fig.add_trace(go.Choropleth(
        locations=iso_list,
        z=[1]*len(iso_list),
        locationmode="ISO-3",
        colorscale=[[0, base_color], [1, highlight_color]],
        showscale=False,
        marker_line_color="#4A0000",
        marker_line_width=1.4,
        hoverinfo="text",
        hovertext=hover_texts,
        name="selected"
    ))

# işaretçiler
if show_markers and iso_list:
    fig.add_trace(go.Scattergeo(
        locations=iso_list,
        locationmode="ISO-3",
        hoverinfo="text",
        text=hover_texts,
        mode="markers",
        marker=dict(size=8, color=highlight_color, line=dict(width=1, color="white")),
        name="markers"
    ))

fig.update_layout(
    title_text=f"<b style='color:#8B0000;'>'{selected}'</b> kelimesinin dillerdeki izleri",
    title_font=dict(family="Georgia, serif", size=20, color="#8B0000"),
    geo=dict(
        showframe=False, 
        showcoastlines=True, 
        coastlinecolor="rgba(139,0,0,0.3)",
        projection_type="natural earth",
        bgcolor="rgba(0,0,0,0)" 
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=50, b=10),
    transition=dict(duration=600, easing="cubic-in-out")
)

# --- göster ve yan panel ---
col1, col2 = st.columns([3,1])
with col1:
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.markdown("<h3 style='color:#8B0000;'>Seçilen Kelime</h3>", unsafe_allow_html=True)
    st.write(f"**{selected}**")
    st.markdown("<h3 style='color:#8B0000;'>Ülkeler ve Yerel Karşılık</h3>", unsafe_allow_html=True)
    for e in entries:
        country_raw = e.get("country")
        local = e.get("local")
        if local:
            st.write(f"- **{country_raw}** — *{local}*")
        else:
            st.write(f"- **{country_raw}**")
    if unrecognized:
        st.markdown("<h3 style='color:#8B0000;'>Tanınmayan Ülke İsimleri</h3>", unsafe_allow_html=True)
        for u in unrecognized:
            st.error(u)
