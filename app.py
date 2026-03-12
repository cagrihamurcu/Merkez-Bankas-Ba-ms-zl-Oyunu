import random
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Merkez Bankası Bağımsızlığı Oyunu",
    page_icon="🏦",
    layout="wide"
)

# =========================================================
# Yardımcılar
# =========================================================
def clamp(value, low, high):
    return max(low, min(high, value))


def fmt_pct(x):
    return f"%{x:.1f}"


def fmt_num(x):
    return f"{x:.1f}"


# =========================================================
# Başlangıç durumu
# =========================================================
INITIAL_STATE = {
    "round": 1,
    "max_rounds": 10,
    "inflation": 22.0,
    "growth": 3.2,
    "unemployment": 9.4,
    "trust": 58.0,          # 0-100
    "cds": 320.0,           # baz puan
    "fx": 33.0,             # kur endeksi / temsili
    "score": 0.0,
    "history": [],
    "game_over": False,
    "last_round_summary": None,
}

# =========================================================
# Senaryolar
# political_pressure: 0-10
# external_shock: dışsal şok şiddeti
# demand_bias: + ise talep güçlü, - ise büyüme zayıf
# =========================================================
SCENARIOS = [
    {
        "title": "Talep Aşırı Canlanıyor",
        "text": "Kredi genişlemesi hızlandı. İç talep güçlü. Enflasyon beklentileri yukarı yönlü bozuluyor.",
        "political_pressure": 4,
        "external_shock": 2,
        "demand_bias": 3,
        "fx_shock": 0.4,
        "trust_shock": -1.0,
    },
    {
        "title": "Seçim Öncesi Büyüme Baskısı",
        "text": "Hükümet büyümeyi desteklemek için faiz indirimi mesajı veriyor. Ancak enflasyon hedefin oldukça üzerinde.",
        "political_pressure": 9,
        "external_shock": 1,
        "demand_bias": 2,
        "fx_shock": 0.6,
        "trust_shock": -2.0,
    },
    {
        "title": "Kur Şoku ve Maliyet Enflasyonu",
        "text": "Kurda sert yükseliş var. İthal girdi maliyetleri artıyor. Fiyatlama davranışları bozuluyor.",
        "political_pressure": 3,
        "external_shock": 8,
        "demand_bias": -1,
        "fx_shock": 2.2,
        "trust_shock": -4.0,
    },
    {
        "title": "Büyüme Belirgin Şekilde Yavaşlıyor",
        "text": "Sanayi üretimi zayıf. Yatırım iştahı düşüyor. İşsizlikte artış riski belirginleşti.",
        "political_pressure": 8,
        "external_shock": 3,
        "demand_bias": -4,
        "fx_shock": 0.2,
        "trust_shock": -1.0,
    },
    {
        "title": "Küresel Riskten Kaçış",
        "text": "Yabancı yatırımcılar gelişmekte olan piyasalardan çıkıyor. Ülke risk primi yükseliyor.",
        "political_pressure": 2,
        "external_shock": 7,
        "demand_bias": -2,
        "fx_shock": 1.7,
        "trust_shock": -3.0,
    },
    {
        "title": "Geçici Enflasyon Rahatlaması",
        "text": "Enerji ve emtia fiyatlarında düşüş var. Kısa vadede enflasyon baskısı azaldı.",
        "political_pressure": 3,
        "external_shock": -2,
        "demand_bias": 1,
        "fx_shock": -0.4,
        "trust_shock": 1.5,
    },
    {
        "title": "Bankacılık Sisteminde Likidite Stresi",
        "text": "Bankalar fonlama maliyetinden şikâyet ediyor. Piyasada kısa vadeli likidite ihtiyacı artmış durumda.",
        "political_pressure": 5,
        "external_shock": 5,
        "demand_bias": -1,
        "fx_shock": 0.5,
        "trust_shock": -2.0,
    },
    {
        "title": "Beklentilerde Bozulma",
        "text": "Piyasa aktörleri merkez bankasının kararlılığı konusunda tereddüt yaşamaya başladı.",
        "political_pressure": 6,
        "external_shock": 4,
        "demand_bias": 0,
        "fx_shock": 0.8,
        "trust_shock": -3.5,
    },
]

DECISIONS = {
    "Faizi Güçlü Artır (+500 bp)": {
        "rate_stance": 2.0,
        "inflation_effect": -2.8,
        "growth_effect": -1.3,
        "unemployment_effect": 0.8,
        "trust_effect": 3.8,
        "cds_effect": -28,
        "fx_effect": -0.9,
        "base_score": 8,
        "tone": "çok sıkı",
    },
    "Faizi Ölçülü Artır (+250 bp)": {
        "rate_stance": 1.0,
        "inflation_effect": -1.7,
        "growth_effect": -0.7,
        "unemployment_effect": 0.4,
        "trust_effect": 2.6,
        "cds_effect": -16,
        "fx_effect": -0.5,
        "base_score": 7,
        "tone": "sıkı",
    },
    "Faizi Sabit Tut": {
        "rate_stance": 0.0,
        "inflation_effect": -0.4,
        "growth_effect": 0.0,
        "unemployment_effect": 0.1,
        "trust_effect": 0.8,
        "cds_effect": 0,
        "fx_effect": 0.0,
        "base_score": 5,
        "tone": "nötr",
    },
    "Faizi İndir (-250 bp)": {
        "rate_stance": -1.0,
        "inflation_effect": 1.2,
        "growth_effect": 0.8,
        "unemployment_effect": -0.5,
        "trust_effect": -2.4,
        "cds_effect": 18,
        "fx_effect": 0.7,
        "base_score": 3,
        "tone": "gevşek",
    },
    "Faizi Güçlü İndir (-500 bp)": {
        "rate_stance": -2.0,
        "inflation_effect": 2.2,
        "growth_effect": 1.4,
        "unemployment_effect": -0.8,
        "trust_effect": -4.0,
        "cds_effect": 35,
        "fx_effect": 1.4,
        "base_score": 1,
        "tone": "çok gevşek",
    },
}


def get_random_scenario():
    return random.choice(SCENARIOS)


def explain_decision(scenario, decision_name, old_state, new_state):
    parts = []
    pressure = scenario["political_pressure"]

    if "İndir" in decision_name and pressure >= 7:
        parts.append("Siyasi baskıya uyuldu; kısa vadede büyüme desteklendi.")
        parts.append("Ancak fiyat istikrarı ve kurumsal güven zayıfladı.")
    elif "Artır" in decision_name and pressure >= 7:
        parts.append("Siyasi baskıya rağmen sıkılaştırma yapıldı.")
        parts.append("Kısa vadeli büyüme pahasına merkez bankası kredibilitesi güçlendi.")
    elif "Sabit" in decision_name:
        parts.append("Merkez bankası bekle-gör yaklaşımı benimsedi.")
        parts.append("Piyasa bu kararı veriye dayalı ya da yetersiz kararlı olarak yorumlayabilir.")
    else:
        parts.append("Karar teknik çerçevede alındı.")
    
    if new_state["inflation"] < old_state["inflation"]:
        parts.append("Enflasyon görünümünde iyileşme başladı.")
    else:
        parts.append("Enflasyon baskısı canlı kaldı ya da arttı.")

    if new_state["trust"] > old_state["trust"]:
        parts.append("Kurumsal güven arttı.")
    else:
        parts.append("Kurumsal güven zayıfladı.")

    if new_state["cds"] < old_state["cds"]:
        parts.append("Risk primi geriledi.")
    else:
        parts.append("Ülke risk primi yükseldi.")

    return " ".join(parts)


def evaluate_decision(state, scenario, decision_name):
    d = DECISIONS[decision_name]

    old_state = state.copy()

    # Dışsal ve içsel dinamikler
    inflation_change = (
        scenario["external_shock"] * 0.45
        + scenario["demand_bias"] * 0.35
        + scenario["fx_shock"] * 0.60
        + d["inflation_effect"]
    )

    growth_change = (
        scenario["demand_bias"] * 0.30
        - scenario["external_shock"] * 0.15
        + d["growth_effect"]
    )

    unemployment_change = (
        -growth_change * 0.35
        + d["unemployment_effect"]
    )

    trust_change = (
        scenario["trust_shock"]
        + d["trust_effect"]
    )

    cds_change = (
        scenario["external_shock"] * 6
        + (10 - scenario["political_pressure"]) * (-0.5)
        + d["cds_effect"]
    )

    fx_change = (
        scenario["fx_shock"]
        + scenario["external_shock"] * 0.08
        + d["fx_effect"]
    )

    # Siyasi baskı mekanizması
    pressure = scenario["political_pressure"]

    # Yüksek baskı + faiz indirimi -> kısa vade bonus, uzun vade ceza
    if pressure >= 7 and "İndir" in decision_name:
        growth_change += 0.7
        unemployment_change -= 0.3
        inflation_change += 1.6
        trust_change -= 3.0
        cds_change += 18
        fx_change += 0.7

    # Yüksek baskı + faiz artırımı -> kısa vade maliyet, uzun vade güven kazanımı
    if pressure >= 7 and "Artır" in decision_name:
        growth_change -= 0.4
        unemployment_change += 0.2
        trust_change += 2.2
        cds_change -= 10
        fx_change -= 0.3

    # Beklentilerde bozulma senaryosunda yetersiz tepki cezası
    if scenario["title"] == "Beklentilerde Bozulma" and decision_name in ["Faizi Sabit Tut", "Faizi İndir (-250 bp)", "Faizi Güçlü İndir (-500 bp)"]:
        inflation_change += 1.2
        trust_change -= 2.5
        cds_change += 12

    # Kur şokunda indirime ek ceza
    if scenario["title"] == "Kur Şoku ve Maliyet Enflasyonu" and "İndir" in decision_name:
        inflation_change += 1.5
        fx_change += 1.2
        cds_change += 10
        trust_change -= 2.0

    new_state = state.copy()
    new_state["inflation"] = clamp(state["inflation"] + inflation_change, 0, 150)
    new_state["growth"] = clamp(state["growth"] + growth_change, -12, 15)
    new_state["unemployment"] = clamp(state["unemployment"] + unemployment_change, 2, 35)
    new_state["trust"] = clamp(state["trust"] + trust_change, 0, 100)
    new_state["cds"] = clamp(state["cds"] + cds_change, 50, 2500)
    new_state["fx"] = clamp(state["fx"] + fx_change, 5, 200)

    # Puanlama
    score = d["base_score"]

    # Enflasyon bonus/ceza
    if new_state["inflation"] <= 15:
        score += 8
    elif new_state["inflation"] <= 25:
        score += 3
    elif new_state["inflation"] > 35:
        score -= 6

    # Güven bonus/ceza
    if new_state["trust"] >= 70:
        score += 5
    elif new_state["trust"] < 40:
        score -= 5

    # CDS bonus/ceza
    if new_state["cds"] <= 250:
        score += 4
    elif new_state["cds"] >= 500:
        score -= 4

    # Büyüme / işsizlik dengesi
    if new_state["growth"] < 0:
        score -= 2
    if new_state["unemployment"] >= 14:
        score -= 3

    # Enflasyon düşüş yönü bonusu
    if new_state["inflation"] < state["inflation"]:
        score += 2

    summary = explain_decision(scenario, decision_name, old_state, new_state)

    result = {
        "state": new_state,
        "score_change": round(score, 1),
        "summary": summary,
    }
    return result


def create_history_df(history):
    if not history:
        return pd.DataFrame()

    df = pd.DataFrame(history)
    return df[
        [
            "Tur", "Senaryo", "Karar", "Enflasyon", "Büyüme",
            "İşsizlik", "Güven", "CDS", "Kur", "Tur Puanı"
        ]
    ]


def final_report(state):
    inf = state["inflation"]
    trust = state["trust"]
    cds = state["cds"]
    score = state["score"]

    if inf <= 15 and trust >= 70 and cds <= 250 and score >= 70:
        return "Çok başarılı başkan: Fiyat istikrarı, güven ve risk primi açısından güçlü bir performans gösterdiniz."
    if inf <= 25 and trust >= 55 and cds <= 400:
        return "Dengeli performans: Ekonomiyi yönetilebilir sınırlar içinde tuttunuz; ancak daha güçlü bir kredibilite inşası gerekebilirdi."
    if inf > 35 or trust < 40 or cds > 500:
        return "Zayıf performans: Kısa vadeli baskılar uzun vadeli istikrarı gölgeledi."
    return "Orta düzey performans: Bazı alanlarda başarılı oldunuz, fakat politika bileşimi daha tutarlı olabilirdi."


def reset_game():
    st.session_state.state = INITIAL_STATE.copy()
    st.session_state.current_scenario = get_random_scenario()


# =========================================================
# Session state
# =========================================================
if "state" not in st.session_state:
    st.session_state.state = INITIAL_STATE.copy()

if "current_scenario" not in st.session_state:
    st.session_state.current_scenario = get_random_scenario()

state = st.session_state.state
scenario = st.session_state.current_scenario

# =========================================================
# Başlık
# =========================================================
st.title("🏦 Merkez Bankası Bağımsızlığı Oyunu")
st.caption("Sınıf içi etkileşimli politika simülasyonu")

# =========================================================
# Üst panel
# =========================================================
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Enflasyon", fmt_pct(state["inflation"]))
m2.metric("Büyüme", fmt_pct(state["growth"]))
m3.metric("İşsizlik", fmt_pct(state["unemployment"]))
m4.metric("Güven", f"{state['trust']:.0f}/100")
m5.metric("CDS", f"{state['cds']:.0f} bp")
m6.metric("Kur", fmt_num(state["fx"]))

st.progress((state["round"] - 1) / state["max_rounds"], text=f"Tur {state['round']} / {state['max_rounds']}")

# =========================================================
# Orta panel
# =========================================================
left, right = st.columns([1.2, 1])

with left:
    st.subheader(f"Tur {state['round']}: {scenario['title']}")
    st.write(scenario["text"])

    pressure = scenario["political_pressure"]
    if pressure >= 8:
        st.error(f"Siyasi baskı çok yüksek ({pressure}/10). Hükümet büyüme odaklı gevşeme bekliyor.")
    elif pressure >= 5:
        st.warning(f"Siyasi baskı orta-yüksek düzeyde ({pressure}/10).")
    else:
        st.info(f"Siyasi baskı düşük ({pressure}/10). Teknik karar alanı daha geniş.")

    st.write("**Ek sinyaller**")
    st.write(f"- Dışsal şok şiddeti: {scenario['external_shock']}")
    st.write(f"- Talep eğilimi: {scenario['demand_bias']}")
    st.write(f"- Kur baskısı: {scenario['fx_shock']:+.1f}")

with right:
    st.subheader("Bu turdaki hedefiniz ne?")
    policy_focus = st.radio(
        "Ağırlık vermek istediğiniz öncelik:",
        ["Fiyat istikrarı", "Dengeli yaklaşım", "Büyüme ve istihdam"],
        index=1
    )

    st.subheader("Kararınız")
    decision_name = st.selectbox(
        "Politika tercihi:",
        list(DECISIONS.keys()),
        index=2
    )

    if st.button("Kararı Uygula", type="primary", use_container_width=True) and not state["game_over"]:
        result = evaluate_decision(state, scenario, decision_name)
        new_state = result["state"]

        # Politika odağına göre küçük ek puan mantığı
        bonus = 0
        if policy_focus == "Fiyat istikrarı" and new_state["inflation"] < state["inflation"]:
            bonus += 2
        if policy_focus == "Dengeli yaklaşım" and new_state["inflation"] <= 25 and new_state["growth"] >= 0:
            bonus += 2
        if policy_focus == "Büyüme ve istihdam" and new_state["growth"] >= state["growth"] and new_state["unemployment"] <= state["unemployment"]:
            bonus += 2

        round_score = result["score_change"] + bonus

        state["inflation"] = new_state["inflation"]
        state["growth"] = new_state["growth"]
        state["unemployment"] = new_state["unemployment"]
        state["trust"] = new_state["trust"]
        state["cds"] = new_state["cds"]
        state["fx"] = new_state["fx"]
        state["score"] += round_score
        state["last_round_summary"] = result["summary"]

        state["history"].append({
            "Tur": state["round"],
            "Senaryo": scenario["title"],
            "Karar": decision_name,
            "Enflasyon": round(state["inflation"], 1),
            "Büyüme": round(state["growth"], 1),
            "İşsizlik": round(state["unemployment"], 1),
            "Güven": round(state["trust"], 1),
            "CDS": round(state["cds"], 0),
            "Kur": round(state["fx"], 1),
            "Tur Puanı": round(round_score, 1),
        })

        state["round"] += 1
        if state["round"] > state["max_rounds"]:
            state["game_over"] = True
        else:
            st.session_state.current_scenario = get_random_scenario()

        st.rerun()

# =========================================================
# Son tur özeti
# =========================================================
if state["last_round_summary"]:
    st.markdown("---")
    st.subheader("Son Kararın Etkisi")
    st.write(state["last_round_summary"])

# =========================================================
# Grafikler
# =========================================================
if state["history"]:
    st.markdown("---")
    st.subheader("Göstergelerin Zaman İçindeki Seyri")

    df = create_history_df(state["history"])

    tab1, tab2, tab3 = st.tabs(["Makro Göstergeler", "Risk Göstergeleri", "Karar Geçmişi"])

    with tab1:
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        ax1.plot(df["Tur"], df["Enflasyon"], marker="o", label="Enflasyon")
        ax1.plot(df["Tur"], df["Büyüme"], marker="o", label="Büyüme")
        ax1.plot(df["Tur"], df["İşsizlik"], marker="o", label="İşsizlik")
        ax1.set_xlabel("Tur")
        ax1.set_ylabel("Yüzde")
        ax1.set_title("Makro Göstergeler")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        st.pyplot(fig1)

    with tab2:
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.plot(df["Tur"], df["Güven"], marker="o", label="Güven")
        ax2.plot(df["Tur"], df["CDS"], marker="o", label="CDS")
        ax2.plot(df["Tur"], df["Kur"], marker="o", label="Kur")
        ax2.set_xlabel("Tur")
        ax2.set_title("Risk ve Güven Göstergeleri")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        st.pyplot(fig2)

    with tab3:
        st.dataframe(df, use_container_width=True)

# =========================================================
# Ders içi yorum kutusu
# =========================================================
st.markdown("---")
st.subheader("Sınıf Tartışması İçin Yorum")
if not state["game_over"]:
    st.write(
        "Karar sonrası sınıfa şu soruları yöneltebilirsiniz: "
        "**Bu karar kısa vadede kimi memnun etti? Uzun vadede en çok hangi değişken zarar gördü? "
        "Merkez bankası bağımsız olmasaydı bu karar daha mı farklı olurdu?**"
    )

# =========================================================
# Oyun sonu
# =========================================================
if state["game_over"]:
    st.markdown("---")
    st.subheader("Final Değerlendirmesi")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Final Enflasyon", fmt_pct(state["inflation"]))
    c2.metric("Final Güven", f"{state['trust']:.0f}/100")
    c3.metric("Final CDS", f"{state['cds']:.0f} bp")
    c4.metric("Toplam Puan", f"{state['score']:.1f}")

    report = final_report(state)

    if "Çok başarılı" in report:
        st.success(report)
    elif "Zayıf" in report:
        st.error(report)
    else:
        st.info(report)

    st.write(
        """
**Ders mesajı:**  
Merkez bankası bağımsızlığı, özellikle **yüksek siyasi baskı** dönemlerinde önem kazanır.  
Kısa vadeli büyüme uğruna gevşeme yapmak ilk anda cazip görünebilir; ancak bu durum çoğu zaman  
**enflasyon, CDS, kur ve güven** üzerinden daha ağır bir maliyet doğurur.
"""
    )

    if st.button("Oyunu Yeniden Başlat", use_container_width=True):
        reset_game()
        st.rerun()

# =========================================================
# Alt butonlar
# =========================================================
st.markdown("---")
b1, b2 = st.columns(2)
with b1:
    if st.button("Yeni Senaryo Getir", use_container_width=True, disabled=state["game_over"]):
        st.session_state.current_scenario = get_random_scenario()
        st.rerun()

with b2:
    if st.button("Baştan Başlat", use_container_width=True):
        reset_game()
        st.rerun()
