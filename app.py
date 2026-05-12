import streamlit as st
import pycountry
import plotly.graph_objects as go
import os

# --- 1. Sayfa Ayarları ve Başlık ---
st.set_page_config(layout="wide", page_title="Dünya Dillerinde Türkçenin İzi")

# --- 2. Özel CSS ile Tarihi Tema, Filigran ve Menü Gizleme ---
custom_css = """
<style>
/* Sağ üstteki 'Share' menüsünü, header'ı ve footer'ı tamamen gizleme */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Ana arka plan rengi */
.stApp {
    background-color: #FDF6E3;
}

/* Piri Reis Haritası Filigranı */
.stApp::before {
    content: "";
    position: fixed; /* Kaydırmalarda haritanın sabit kalması için */
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-image: url("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Piri_reis_world_map_01.jpg/1024px-Piri_reis_world_map_01.jpg");
    background-size: cover;
    background-position: center center;
    opacity: 0.12; /* Metinlerin okunurluğunu bozmamak için şeffaflık seviyesi */
    z-index: -1; /* En arka planda kalmasını sağlar */
    pointer-events: none;
}

/* Başlık renkleri ve fontu */
h1, h2, h3, h4, h5, h6 {
    color: #8B0000 !important;
    font-family: 'Georgia', serif !important;
}

/* Yan panel (Sidebar) arka planını hafif yarı saydam yapıyoruz */
[data-testid="stSidebar"] {
    background-color: rgba(244, 236, 216, 0.90);
    border-right: 2px solid #D3C6A6;
}

/* Genel metin stili */
html, body, p, span, div, li {
    font-family: 'Georgia', serif !important;
    color: #3E2723;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Başlık (TR yerine Türk Bayrağı Emojisi eklendi)
st.title("🇹🇷 Dünya Dillerinde Türkçenin İzi")

# --- kelime.txt oku ---
cwd = os.getcwd()
path = os.path.join(cwd, "kelime.txt")
if not os.path.exists(path):
    st.error("kelime.txt bulunamadı. Lütfen app.py ile aynı klasöre koyun.")
    st.stop()

with open(path, "r", encoding="utf-8-sig") as f:
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
st.sidebar.header("Ayarlar")
words = sorted(mapping.keys(), key=lambda s: s.lower())
selected = st.sidebar.selectbox("Bir kelime seçin", words)

highlight_color = st.sidebar.color_picker("Vurgulama rengi", "#8B0000") 
base_color = "#EAE0C8" 
show_markers = st.sidebar.checkbox("Ülke işaretçileri göster", value=True)

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
    title_text=f"'{selected}' kelimesinin dillerdeki izleri",
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
    st.markdown("### Seçilen Kelime")
    st.write(f"**{selected}**")
    st.markdown("### Ülkeler ve Yerel Karşılık")
    for e in entries:
        country_raw = e.get("country")
        local = e.get("local")
        if local:
            st.write(f"- **{country_raw}** — *{local}*")
        else:
            st.write(f"- **{country_raw}**")
    if unrecognized:
        st.markdown("### Tanınmayan Ülke İsimleri")
        for u in unrecognized:
            st.error(u)
