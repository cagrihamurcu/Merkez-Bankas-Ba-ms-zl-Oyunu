import streamlit as st
import random
import time

st.set_page_config(page_title="Merkez Bankası Bağımsızlığı Oyunu", layout="wide")

# -----------------------------
# Senaryolar
# -----------------------------
SCENARIOS = [
    {
        "title": "Talep Canlanıyor",
        "text": "Ekonomide iç talep artıyor. Kredi genişlemesi hızlandı. Enflasyon yukarı yönlü baskı veriyor.",
        "pressure": False,
        "shock_inflation": 1.5,
        "shock_growth": 0.8,
        "shock_unemployment": -0.3,
        "shock_trust": 0.5,
    },
    {
        "title": "Seçim Öncesi Baskı",
        "text": "Hükümet büyümeyi desteklemek için faiz indirimi bekliyor. Ancak enflasyon zaten yüksek seyrediyor.",
        "pressure": True,
        "shock_inflation": 1.0,
        "shock_growth": 0.5,
        "shock_unemployment": -0.2,
        "shock_trust": -1.0,
    },
    {
        "title": "Kur Şoku",
        "text": "Kur hızlı yükseldi. İthal maliyetleri arttı. Piyasada fiyatlama davranışları bozuluyor.",
        "pressure": False,
        "shock_inflation": 2.5,
        "shock_growth": -0.6,
        "shock_unemployment": 0.4,
        "shock_trust": -3.0,
    },
    {
        "title": "Büyüme Yavaşlıyor",
        "text": "Sanayi üretimi zayıfladı. Şirketler yatırım kararlarını erteliyor. İşsizlikte artış riski var.",
        "pressure": True,
        "shock_inflation": -0.5,
        "shock_growth": -1.0,
        "shock_unemployment": 0.8,
        "shock_trust": -0.5,
    },
]

DECISIONS = {
    "Faizi Artır": {"inflation": -2, "growth": -0.8, "unemployment": 0.6, "trust": 3},
    "Faizi Sabit Tut": {"inflation": -0.5, "growth": 0, "unemployment": 0.1, "trust": 1},
    "Faizi İndir": {"inflation": 1.8, "growth": 1, "unemployment": -0.6, "trust": -3},
}


# -----------------------------
# Başlangıç
# -----------------------------
def get_initial_state():
    return {
        "round": 1,
        "max_rounds": 8,
        "inflation": 18.0,
        "growth": 3.0,
        "unemployment": 9.0,
        "trust": 60.0,
        "score": 0,
        "history": [],
        "game_over": False,
        "cooldown_until": 0,
        "pending_scenario": None,
    }


def scenario_for_round():
    return random.choice(SCENARIOS)


# -----------------------------
# Session state
# -----------------------------
if "state" not in st.session_state:
    st.session_state.state = get_initial_state()
    st.session_state.current_scenario = scenario_for_round()
    st.session_state.last_result = None

state = st.session_state.state


# -----------------------------
# Bekleme ekranı
# -----------------------------
now = time.time()

if now < state.get("cooldown_until", 0):

    remaining = int(state["cooldown_until"] - now)
    minutes = remaining // 60
    seconds = remaining % 60

    st.title("Piyasa Tepkisi Bekleniyor")

    st.warning(
        "Verdiğiniz kararın piyasalarda etkilerinin görülmesi için lütfen bekleyiniz."
    )

    st.metric("Kalan süre", f"{minutes:02d}:{seconds:02d}")

    time.sleep(1)
    st.rerun()


# -----------------------------
# Bekleme bittiyse yeni turu başlat
# -----------------------------
if state.get("pending_scenario") is not None:
    st.session_state.current_scenario = state["pending_scenario"]
    state["pending_scenario"] = None


# -----------------------------
# Başlık
# -----------------------------
st.title("Merkez Bankası Bağımsızlığı Oyunu")

left, right = st.columns([1.1, 1.4])

with left:

    st.subheader("Ekonomik Görünüm")

    c1, c2 = st.columns(2)
    c1.metric("Enflasyon", f"%{state['inflation']}")
    c2.metric("Büyüme", f"%{state['growth']}")

    c3, c4 = st.columns(2)
    c3.metric("İşsizlik", f"%{state['unemployment']}")
    c4.metric("Güven", f"{state['trust']}/100")

    st.metric("Toplam Puan", state["score"])

    progress = (state["round"] - 1) / state["max_rounds"]
    st.progress(progress, text=f"Tur {state['round']} / {state['max_rounds']}")

with right:

    scenario = st.session_state.current_scenario

    st.subheader(f"Tur {state['round']}: {scenario['title']}")
    st.write(scenario["text"])

    if scenario["pressure"]:
        st.warning("Siyasi baskı var.")
    else:
        st.info("Teknik değerlendirme ön planda.")


# -----------------------------
# Karar
# -----------------------------
if not state["game_over"]:

    st.markdown("---")
    st.subheader("Kararınız")

    decision = st.radio(
        "Merkez bankası başkanı olarak ne yaparsınız?",
        ["Faizi Artır", "Faizi Sabit Tut", "Faizi İndir"],
        horizontal=True,
    )

    if st.button("Kararı Uygula"):

        d = DECISIONS[decision]

        state["inflation"] += scenario["shock_inflation"] + d["inflation"]
        state["growth"] += scenario["shock_growth"] + d["growth"]
        state["unemployment"] += scenario["shock_unemployment"] + d["unemployment"]
        state["trust"] += scenario["shock_trust"] + d["trust"]

        history_item = {
            "Tur": state["round"],
            "Senaryo": scenario["title"],
            "Karar": decision,
            "Enflasyon": round(state["inflation"], 1),
            "Büyüme": round(state["growth"], 1),
            "İşsizlik": round(state["unemployment"], 1),
            "Güven": round(state["trust"], 1),
        }

        state["history"].append(history_item)
        st.session_state.last_result = history_item

        # yeni turu hazırla ama göstermeden önce beklet
        if state["round"] >= state["max_rounds"]:
            state["game_over"] = True
        else:
            state["round"] += 1
            state["pending_scenario"] = scenario_for_round()

        state["cooldown_until"] = time.time() + 180

        st.rerun()


# -----------------------------
# Sonuç
# -----------------------------
if st.session_state.last_result is not None:

    last = st.session_state.last_result

    st.markdown("---")
    st.subheader("Son Tur Sonucu")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Enflasyon", f"%{last['Enflasyon']}")
    c2.metric("Büyüme", f"%{last['Büyüme']}")
    c3.metric("İşsizlik", f"%{last['İşsizlik']}")
    c4.metric("Güven", f"{last['Güven']}/100")


# -----------------------------
# Geçmiş
# -----------------------------
if state["history"]:

    st.markdown("---")
    st.subheader("Karar Geçmişi")

    st.dataframe(state["history"], use_container_width=True)


# -----------------------------
# Oyun bitti
# -----------------------------
if state["game_over"]:

    st.markdown("---")
    st.subheader("Oyun Tamamlandı")

    st.write("Nihai ekonomik göstergeler:")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Enflasyon", f"%{round(state['inflation'],1)}")
    c2.metric("Büyüme", f"%{round(state['growth'],1)}")
    c3.metric("İşsizlik", f"%{round(state['unemployment'],1)}")
    c4.metric("Güven", f"{round(state['trust'],1)}/100")

    if st.button("Oyunu Yeniden Başlat"):
        st.session_state.state = get_initial_state()
        st.session_state.current_scenario = scenario_for_round()
        st.session_state.last_result = None
        st.rerun()
