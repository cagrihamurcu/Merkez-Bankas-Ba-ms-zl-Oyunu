import streamlit as st

st.set_page_config(page_title="Merkez Bankası Oyunu", layout="centered")

# Başlangıç değerleri
if "inflation" not in st.session_state:
    st.session_state.inflation = 20
    st.session_state.growth = 3
    st.session_state.trust = 50
    st.session_state.score = 0
    st.session_state.round = 1
    st.session_state.message = ""

st.title("Merkez Bankası Bağımsızlığı Oyunu")

st.write("### Ekonomik Durum")
c1, c2 = st.columns(2)
c1.metric("Enflasyon", f"%{st.session_state.inflation}")
c2.metric("Büyüme", f"%{st.session_state.growth}")

c3, c4 = st.columns(2)
c3.metric("Güven", f"{st.session_state.trust}/100")
c4.metric("Puan", st.session_state.score)

st.write("---")

# Sabit senaryo
st.write("### Senaryo")
st.write(
    "Seçim öncesi hükümet faiz indirimi istiyor. "
    "Ancak enflasyon hâlâ yüksek. "
    "Merkez bankası başkanı olarak karar vermelisiniz."
)

decision = st.radio(
    "Kararınız nedir?",
    ["Faizi Artır", "Faizi Sabit Tut", "Faizi İndir"]
)

if st.button("Kararı Uygula"):
    if decision == "Faizi Artır":
        st.session_state.inflation -= 3
        st.session_state.growth -= 1
        st.session_state.trust += 10
        st.session_state.score += 10
        st.session_state.message = (
            "Merkez bankası bağımsız davrandı. "
            "Enflasyon düştü, güven arttı; ancak büyüme biraz yavaşladı."
        )

    elif decision == "Faizi Sabit Tut":
        st.session_state.inflation -= 1
        st.session_state.growth += 0
        st.session_state.trust += 2
        st.session_state.score += 5
        st.session_state.message = (
            "Temkinli bir karar verildi. "
            "Enflasyon sınırlı düştü, güven az da olsa arttı."
        )

    elif decision == "Faizi İndir":
        st.session_state.inflation += 3
        st.session_state.growth += 1
        st.session_state.trust -= 10
        st.session_state.score -= 5
        st.session_state.message = (
            "Kısa vadede büyüme desteklendi; "
            "ancak enflasyon arttı ve merkez bankasına güven azaldı."
        )

    st.session_state.round += 1

if st.session_state.message:
    st.write("---")
    st.write("### Sonuç")
    st.success(st.session_state.message)

st.write("---")
if st.button("Baştan Başlat"):
    st.session_state.inflation = 20
    st.session_state.growth = 3
    st.session_state.trust = 50
    st.session_state.score = 0
    st.session_state.round = 1
    st.session_state.message = ""
    st.rerun()
