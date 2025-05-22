
import streamlit as st
import json

# Sayfa stili ve başlık
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f0fff0;
    }
    h1 {
        text-align: center;
        color: #2e7d32;
        font-size: 36px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1>Hınıs Tarımı İçin Karar Destek Sistemi</h1>", unsafe_allow_html=True)
st.subheader("👋 Hoş geldiniz! Lütfen giriş yapınız.")

# Giriş tipi seçimi
giris_tipi = st.radio("Veri Giriş Türünü Seçin", ["Manuel Giriş", "Drone / Cihaz Verisi (JSON)"])

# Ortak algoritmalar
def ekim_zamani_onerisi(urun, don_riski, urun_cesidi):
    if urun == "bugday":
        if don_riski == "Evet" and urun_cesidi == "geççi":
            return "Geççi çeşit don riskine uygunsuz. İlkbahar sonu önerilir."
        return "İlkbahar sonu (don riski geçince)" if don_riski == "Evet" else "Sonbahar (Ağustos sonu - Eylül başı)"
    elif urun == "arpa":
        return "Eylül ortası (kışlık) veya Nisan sonu (ilkbahar)"
    elif urun == "fasulye":
        return "Mayıs ortası (don riski geçtikten sonra)"
    return "Bilinmeyen ürün"

def gubre_tavsiyesi(organik_madde, fosfor, toprak_tipi):
    tavsiyeler = []
    if organik_madde < 2:
        tavsiyeler.append("Organik gübre (ahır gübresi)")
    if fosfor < 5:
        tavsiyeler.append("Fosforlu gübre (DAP, TSP)")
    if toprak_tipi == "killi":
        tavsiyeler.append("Killi toprakta yavaş çözünen gübreler tercih edilmelidir")
    if not tavsiyeler:
        tavsiyeler.append("Toprak besin değerleri yeterli")
    return ", ".join(tavsiyeler)

def tahmini_verim(urun, sulama_var_mi, yillik_yagis, toprak_tipi):
    verim_degerleri = {
        "bugday": (124, 196),
        "arpa": (150, 200),
        "fasulye": (180, 210)
    }
    verim = verim_degerleri.get(urun, (0, 0))[1 if sulama_var_mi == "Evet" else 0]
    uyari = None
    if yillik_yagis < 300:
        verim *= 0.75
        uyari = "Düşük yağış nedeniyle verim düşebilir."
    if toprak_tipi == "killi" and sulama_var_mi == "Hayır":
        verim *= 0.9
        uyari = (uyari or "") + " Killi toprakta sulama yoksa verim azalabilir."
    return round(verim, 1), uyari

def gelismis_sulama_takvimi(urun, et0=4.3):
    evreler_dict = {
        "bugday": [
            {"isim": "Başlangıç", "gun": "0–15", "kc": 0.3},
            {"isim": "Gelişim", "gun": "15–40", "kc": 0.7},
            {"isim": "Orta Evre", "gun": "40–65", "kc": 1.15},
            {"isim": "Son Evre", "gun": "65–90", "kc": 0.25}
        ],
        "arpa": [
            {"isim": "Başlangıç", "gun": "0–12", "kc": 0.3},
            {"isim": "Gelişim", "gun": "12–35", "kc": 0.6},
            {"isim": "Orta Evre", "gun": "35–60", "kc": 1.05},
            {"isim": "Son Evre", "gun": "60–85", "kc": 0.2}
        ],
        "fasulye": [
            {"isim": "Başlangıç", "gun": "0–10", "kc": 0.4},
            {"isim": "Gelişim", "gun": "10–30", "kc": 0.7},
            {"isim": "Orta Evre", "gun": "30–55", "kc": 1.05},
            {"isim": "Son Evre", "gun": "55–75", "kc": 0.3}
        ]
    }

    if urun not in evreler_dict:
        return ["Bu ürün için sulama takvimi mevcut değil."]

    takvim = []
    for evre in evreler_dict[urun]:
        etc = round(et0 * evre["kc"], 2)
        if etc < 2:
            tavsiye = "Sulama gerekmez veya 10 günde bir"
        elif 2 <= etc < 4:
            tavsiye = "Haftalık sulama önerilir"
        else:
            tavsiye = "Her 2-3 günde bir sulama önerilir"

        takvim.append(
            f"{evre['isim']} evresi ({evre['gun']} gün): Kc={evre['kc']} → ETc={etc} mm/gün → {tavsiye}"
        )

    return takvim

# Drone JSON yükleme
if giris_tipi == "Drone / Cihaz Verisi (JSON)":
    dosya = st.file_uploader("📂 Drone JSON Verisini Yükleyin", type="json")
    if dosya is not None:
        veri = json.load(dosya)
        urun = veri["urun"]
        toprak_ph = veri["toprak_ph"]
        organik_madde = veri["organik_madde"]
        fosfor = veri["fosfor"]
        sulama_var_mi = veri["sulama_var_mi"]
        don_riski = veri["don_riski"]
        yillik_yagis = veri["yillik_yagis"]
        toprak_tipi = veri["toprak_tipi"]
        urun_cesidi = veri["urun_cesidi"]

        st.success("Drone verisi başarıyla yüklendi ve analiz başladı.")
        st.write("📋 Aşağıda analiz sonuçları yer almaktadır:")

        sonuc = {}
        sonuc["ekim_zamani"] = ekim_zamani_onerisi(urun, don_riski, urun_cesidi)
        sonuc["gubre_tavsiyesi"] = gubre_tavsiyesi(organik_madde, fosfor, toprak_tipi)
        verim, uyari = tahmini_verim(urun, sulama_var_mi, yillik_yagis, toprak_tipi)
        sonuc["tahmini_verim_kg_da"] = verim
        if uyari:
            sonuc["uyari"] = uyari

        st.subheader("🌱 Öneriler")
        st.success(f"**Ekim Zamanı:** {sonuc['ekim_zamani']}")
        st.info(f"**Gübre Tavsiyesi:** {sonuc['gubre_tavsiyesi']}")
        st.success(f"**Tahmini Verim:** {sonuc['tahmini_verim_kg_da']} kg/da")
        if "uyari" in sonuc:
            st.warning(sonuc["uyari"])

        st.subheader("📆 Gelişmiş Sulama Takvimi (FAO 56 Uyumlu)")
        for satir in gelismis_sulama_takvimi(urun):
            st.markdown(f"- {satir}")

# Manuel form alanları
elif giris_tipi == "Manuel Giriş":
    urun = st.selectbox("Ürün Seçin", ["bugday", "arpa", "fasulye"])
    toprak_ph = st.number_input("Toprak pH Değeri", min_value=4.0, max_value=9.0, value=7.0, step=0.1)
    organik_madde = st.number_input("Organik Madde (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.1)
    fosfor = st.number_input("Fosfor (P₂O₅) kg/da", min_value=0.0, max_value=20.0, value=5.0, step=0.1)
    sulama_var_mi = st.radio("Sulama Var mı?", ["Evet", "Hayır"])
    don_riski = st.radio("Don Riski Var mı?", ["Evet", "Hayır"])
    yillik_yagis = st.number_input("Yıllık Yağış (mm)", min_value=0, max_value=1000, value=450, step=10)
    toprak_tipi = st.selectbox("Toprak Tipi", ["tınlı", "killi-tınlı", "killi"])
    urun_cesidi = st.selectbox("Ürün Çeşidi", ["erkenci", "geççi", "yerli tohum"])

    if st.button("Hesapla"):
        sonuc = {}
        sonuc["ekim_zamani"] = ekim_zamani_onerisi(urun, don_riski, urun_cesidi)
        sonuc["gubre_tavsiyesi"] = gubre_tavsiyesi(organik_madde, fosfor, toprak_tipi)
        verim, uyari = tahmini_verim(urun, sulama_var_mi, yillik_yagis, toprak_tipi)
        sonuc["tahmini_verim_kg_da"] = verim
        if uyari:
            sonuc["uyari"] = uyari

        st.subheader("🌱 Öneriler")
        st.success(f"**Ekim Zamanı:** {sonuc['ekim_zamani']}")
        st.info(f"**Gübre Tavsiyesi:** {sonuc['gubre_tavsiyesi']}")
        st.success(f"**Tahmini Verim:** {sonuc['tahmini_verim_kg_da']} kg/da")
        if "uyari" in sonuc:
            st.warning(sonuc["uyari"])

        st.subheader("📆 Gelişmiş Sulama Takvimi (FAO 56 Uyumlu)")
        for satir in gelismis_sulama_takvimi(urun):
            st.markdown(f"- {satir}")
