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
    {
        "title": "Küresel Risk İştahı Düştü",
        "text": "Yabancı yatırımcılar gelişmekte olan piyasalardan çıkıyor. Ülke risk primi yükseliyor.",
        "pressure": False,
        "shock_inflation": 1.2,
        "shock_growth": -0.7,
        "shock_unemployment": 0.5,
        "shock_trust": -2.5,
    },
    {
        "title": "Enflasyonda Geçici Rahatlama",
        "text": "Enerji fiyatlarında düşüş oldu. Kısa vadede enflasyon baskısı sınırlı görünüyor.",
        "pressure": False,
        "shock_inflation": -1.0,
        "shock_growth": 0.2,
        "shock_unemployment": -0.1,
        "shock_trust": 1.0,
    },
]

DECISIONS = {
    "Faizi Artır": {
        "inflation": -2.0,
        "growth": -0.8,
        "unemployment": 0.6,
        "trust": 3.5,
        "score_base": 8,
        "label": "Sıkılaştırıcı politika",
    },
    "Faizi Sabit Tut": {
        "inflation": -0.5,
        "growth": 0.0,
        "unemployment": 0.1,
        "trust": 1.0,
        "score_base": 5,
        "label": "Bekle-gör yaklaşımı",
    },
    "Faizi İndir": {
        "inflation": 1.8,
        "growth": 1.0,
        "unemployment": -0.6,
        "trust": -3.0,
        "score_base": 3,
        "label": "Genişleyici politika",
    },
}


# -----------------------------
# Yardımcı fonksiyonlar
# -----------------------------
def get_initial_state():
    return {
        "round": 1,
        "max_rounds": 8,
        "inflation": 18.0,
        "growth": 3.0,
        "unemployment": 9.0,
        "trust": 60.0,
        "score": 0.0,
        "history": [],
        "game_over": False,
        "cooldown_until": 0,
        "pending_next_round": None,
        "pending_game_over": False,
    }


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def scenario_for_round():
    return random.choice(SCENARIOS)


def build_comment_sections(decision_name, scenario, old_state, new_state):
    old_inflation = old_state["inflation"]
    old_growth = old_state["growth"]
    old_unemployment = old_state["unemployment"]
    old_trust = old_state["trust"]

    new_inflation = new_state["inflation"]
    new_growth = new_state["growth"]
    new_unemployment = new_state["unemployment"]
    new_trust = new_state["trust"]

    delta_inflation = round(new_inflation - old_inflation, 1)
    delta_growth = round(new_growth - old_growth, 1)
    delta_unemployment = round(new_unemployment - old_unemployment, 1)
    delta_trust = round(new_trust - old_trust, 1)

    # 1) Karar
    if decision_name == "Faizi Artır":
        action_text = "Merkez bankası politika faizini artırarak sıkılaştırıcı bir duruş benimsedi."
    elif decision_name == "Faizi Sabit Tut":
        action_text = "Merkez bankası politika faizini sabit tutarak temkinli ve veri odaklı bir duruş sergiledi."
    else:
        action_text = "Merkez bankası politika faizini indirerek genişleyici bir duruş benimsedi."

    # 2) Sonuç
    def trend_text(delta, positive_word, negative_word, neutral_word="değişmedi"):
        if delta > 0:
            return positive_word
        elif delta < 0:
            return negative_word
        return neutral_word

    inflation_text = trend_text(delta_inflation, "arttı", "azaldı")
    growth_text = trend_text(delta_growth, "iyileşti", "zayıfladı")
    unemployment_text = trend_text(delta_unemployment, "arttı", "azaldı")
    trust_text = trend_text(delta_trust, "arttı", "azaldı")

    outcome_text = (
        f"Bu kararın ardından enflasyon {inflation_text}, büyüme görünümü {growth_text}, "
        f"işsizlik {unemployment_text} ve kurumsal güven {trust_text}."
    )

    # 3) Mekanizma
    mechanism_text = ""

    if scenario["pressure"] and decision_name == "Faizi İndir":
        mechanism_text = (
            "Siyasi baskı altında yapılan faiz indirimi kısa vadede toplam talebi ve büyümeyi destekleyebilir; "
            "ancak beklentiler kanalı üzerinden enflasyonu besler ve merkez bankasının kredibilitesini zayıflatır. "
            "Bu durum literatürde zaman tutarsızlığı problemiyle ilişkilidir."
        )
    elif scenario["pressure"] and decision_name == "Faizi Artır":
        mechanism_text = (
            "Siyasi baskıya rağmen sıkılaşma yapılması kısa vadede çıktı maliyeti doğurabilir; "
            "ancak beklentileri çıpalayarak ve merkez bankasının bağımsızlığına işaret ederek güveni güçlendirir. "
            "Bu, kredibilite kanalıyla çalışan tipik bir dezenflasyon mantığıdır."
        )
    elif scenario["title"] == "Kur Şoku" and decision_name == "Faizi İndir":
        mechanism_text = (
            "Kur şoku sırasında faiz indirimi, döviz kuru geçişkenliği yüksek ekonomilerde maliyet enflasyonunu "
            "daha da artırabilir. Gerçek hayatta bu tür durumlarda fiyat istikrarı ile büyüme desteği arasındaki çatışma belirginleşir."
        )
    elif scenario["title"] == "Kur Şoku" and decision_name == "Faizi Artır":
        mechanism_text = (
            "Kur şoku döneminde faiz artırımı yalnızca iç talebi soğutmaz; aynı zamanda beklentileri yönetme "
            "ve yerli para üzerindeki baskıyı azaltma işlevi de görebilir."
        )
    elif decision_name == "Faizi Artır":
        mechanism_text = (
            "Faiz artışı kredi koşullarını sıkılaştırır, iç talebi yavaşlatır ve orta vadede enflasyon baskısını azaltır. "
            "Bu etki toplam talep ve beklentiler kanalı üzerinden açıklanır."
        )
    elif decision_name == "Faizi Sabit Tut":
        mechanism_text = (
            "Faizi sabit tutmak, merkez bankasının yeni veri beklediği ve mevcut sıkılık derecesini korumayı tercih ettiği anlamına gelebilir. "
            "Gerçek hayatta bu tür kararlar özellikle belirsizlik yüksekken bekle-gör stratejisi olarak kullanılır."
        )
    else:
        mechanism_text = (
            "Faiz indirimi kredi ve talep kanalı üzerinden ekonomik aktiviteyi destekleyebilir. "
            "Ancak enflasyon hâlâ yüksekse veya beklentiler tam olarak çıpalanmamışsa, bu karar fiyat istikrarı açısından ek risk yaratır."
        )

    return {
        "action": action_text,
        "outcome": outcome_text,
        "mechanism": mechanism_text,
    }


def evaluate_decision(decision_name, scenario, current_state):
    decision = DECISIONS[decision_name]

    old_state = {
        "inflation": current_state["inflation"],
        "growth": current_state["growth"],
        "unemployment": current_state["unemployment"],
        "trust": current_state["trust"],
    }

    new_inflation = current_state["inflation"] + scenario["shock_inflation"] + decision["inflation"]
    new_growth = current_state["growth"] + scenario["shock_growth"] + decision["growth"]
    new_unemployment = current_state["unemployment"] + scenario["shock_unemployment"] + decision["unemployment"]
    new_trust = current_state["trust"] + scenario["shock_trust"] + decision["trust"]

    political_bonus = 0

    # Siyasi baskı altında gevşeme: kısa vadeli çıktı desteği, orta vadeli kredibilite ve enflasyon maliyeti
    if scenario["pressure"] and decision_name == "Faizi İndir":
        new_growth += 0.8
        new_unemployment -= 0.4
        new_inflation += 1.5
        new_trust -= 4.0
        political_bonus = 2

    # Siyasi baskıya rağmen sıkılaşma: kısa vadeli çıktı maliyeti, uzun vadeli güven/kredibilite kazancı
    if scenario["pressure"] and decision_name == "Faizi Artır":
        new_growth -= 0.4
        new_unemployment += 0.3
        new_trust += 2.0

    # Kur şoku altında gevşeme ek olarak enflasyonist olur
    if scenario["title"] == "Kur Şoku" and decision_name == "Faizi İndir":
        new_inflation += 1.0
        new_trust -= 1.5

    # Kur şoku altında sıkılaşma beklenti yönetimini destekler
    if scenario["title"] == "Kur Şoku" and decision_name == "Faizi Artır":
        new_trust += 1.0

    # Büyüme yavaşlarken sıkılaşmanın reel maliyeti daha yüksek olur
    if scenario["title"] == "Büyüme Yavaşlıyor" and decision_name == "Faizi Artır":
        new_growth -= 0.5
        new_unemployment += 0.2

    # Geçici rahatlama döneminde sabit tutmak "erken gevşeme" riskinden kaçınma olarak okunabilir
    if scenario["title"] == "Enflasyonda Geçici Rahatlama" and decision_name == "Faizi Sabit Tut":
        new_trust += 0.5

    # Makul sınırlar
    new_inflation = clamp(new_inflation, 0, 120)
    new_growth = clamp(new_growth, -10, 12)
    new_unemployment = clamp(new_unemployment, 2, 35)
    new_trust = clamp(new_trust, 0, 100)

    # Puanlama
    score = decision["score_base"] + political_bonus

    if new_inflation <= 15:
        score += 5
    elif new_inflation <= 25:
        score += 2
    else:
        score -= 4

    if new_trust >= 70:
        score += 4
    elif new_trust < 40:
        score -= 4

    if new_unemployment >= 15:
        score -= 3

    if new_growth < 0:
        score -= 2

    new_state = {
        "inflation": round(new_inflation, 1),
        "growth": round(new_growth, 1),
        "unemployment": round(new_unemployment, 1),
        "trust": round(new_trust, 1),
    }

    comment_sections = build_comment_sections(decision_name, scenario, old_state, new_state)

    result = {
        "new_inflation": new_state["inflation"],
        "new_growth": new_state["growth"],
        "new_unemployment": new_state["unemployment"],
        "new_trust": new_state["trust"],
        "score_change": round(score, 1),
        "decision_label": decision["label"],
        "comment_action": comment_sections["action"],
        "comment_outcome": comment_sections["outcome"],
        "comment_mechanism": comment_sections["mechanism"],
    }
    return result


def final_assessment(current_state):
    inf = current_state["inflation"]
    trust = current_state["trust"]
    score = current_state["score"]

    if inf <= 15 and trust >= 70 and score >= 50:
        return "Başarılı başkan: Fiyat istikrarını güçlendirdiniz ve kurumsal güveni artırdınız."
    elif inf <= 25 and trust >= 50:
        return "Kısmen başarılı: Sistemi yönetilebilir tuttunuz; ancak daha güçlü bir çapa gerekebilirdi."
    else:
        return "Zor dönem: Kısa vadeli baskılar uzun vadeli istikrarın önüne geçti."


def reset_game():
    st.session_state.state = get_initial_state()
    st.session_state.current_scenario = scenario_for_round()
    st.session_state.last_result = None


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
cooldown_active = now < state.get("cooldown_until", 0)

if cooldown_active:
    remaining = int(state["cooldown_until"] - now)
    minutes = remaining // 60
    seconds = remaining % 60

    st.title("Piyasa Tepkisi Bekleniyor")
    st.warning("Verdiğiniz kararın piyasalarda etkilerinin görülmesi için lütfen bekleyiniz.")
    st.metric("Kalan süre", f"{minutes:02d}:{seconds:02d}")

    time.sleep(1)
    st.rerun()

# Bekleme bittiyse yeni turu veya oyun bitişini aktive et
if state.get("pending_next_round") is not None:
    state["round"] = state["pending_next_round"]["round"]
    st.session_state.current_scenario = state["pending_next_round"]["scenario"]
    state["pending_next_round"] = None

if state.get("pending_game_over", False):
    state["game_over"] = True
    state["pending_game_over"] = False


# -----------------------------
# Başlık
# -----------------------------
st.title("Merkez Bankası Bağımsızlığı Oyunu")
st.caption("Sınıfta kullanılabilecek etkileşimli mini simülasyon")

left, right = st.columns([1.1, 1.4])

with left:
    st.subheader("Mevcut Ekonomik Görünüm")

    c1, c2 = st.columns(2)
    c1.metric("Enflasyon", f"%{state['inflation']}")
    c2.metric("Büyüme", f"%{state['growth']}")

    c3, c4 = st.columns(2)
    c3.metric("İşsizlik", f"%{state['unemployment']}")
    c4.metric("Güven", f"{state['trust']}/100")

    st.metric("Toplam Puan", f"{state['score']}")

    current_round_display = min(state["round"], state["max_rounds"])
    progress_ratio = (current_round_display - 1) / state["max_rounds"]
    progress_ratio = max(0.0, min(progress_ratio, 1.0))
    st.progress(progress_ratio, text=f"Tur: {current_round_display} / {state['max_rounds']}")

with right:
    scenario = st.session_state.current_scenario
    current_round_display = min(state["round"], state["max_rounds"])
    st.subheader(f"Tur {current_round_display}: {scenario['title']}")
    st.write(scenario["text"])

    if scenario["pressure"]:
        st.warning("Siyasi baskı var: Hükümet kısa vadeli büyüme için faiz indirimi bekliyor.")
    else:
        st.info("Bu turda doğrudan siyasi baskı görünmüyor. Teknik değerlendirme öne çıkıyor.")

# -----------------------------
# Oyun devam ediyorsa
# -----------------------------
if not state["game_over"]:
    st.markdown("---")
    st.subheader("Kararınız")

    decision = st.radio(
        "Merkez bankası başkanı olarak ne yaparsınız?",
        ["Faizi Artır", "Faizi Sabit Tut", "Faizi İndir"],
        horizontal=True,
    )

    if st.button("Kararı Uygula", type="primary"):
        result = evaluate_decision(decision, scenario, state)

        state["inflation"] = result["new_inflation"]
        state["growth"] = result["new_growth"]
        state["unemployment"] = result["new_unemployment"]
        state["trust"] = result["new_trust"]
        state["score"] += result["score_change"]

        history_item = {
            "Tur": state["round"],
            "Senaryo": scenario["title"],
            "Karar": decision,
            "Enflasyon": state["inflation"],
            "Büyüme": state["growth"],
            "İşsizlik": state["unemployment"],
            "Güven": state["trust"],
            "Tur Puanı": result["score_change"],
            "Karar Notu": result["comment_action"],
            "Sonuç Notu": result["comment_outcome"],
            "Mekanizma Notu": result["comment_mechanism"],
        }

        state["history"].append(history_item)
        st.session_state.last_result = history_item

        # Hemen yeni tura geçme; önce bekleme ekranı göster
        if state["round"] >= state["max_rounds"]:
            state["pending_game_over"] = True
        else:
            state["pending_next_round"] = {
                "round": state["round"] + 1,
                "scenario": scenario_for_round(),
            }

        state["cooldown_until"] = time.time() + 180  # 3 dakika
        st.rerun()

# -----------------------------
# Son karar sonucu
# -----------------------------
if st.session_state.last_result is not None:
    st.markdown("---")
    last = st.session_state.last_result
    st.subheader("Son Tur Sonucu")

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Enflasyon", f"%{last['Enflasyon']}")
    a2.metric("Büyüme", f"%{last['Büyüme']}")
    a3.metric("İşsizlik", f"%{last['İşsizlik']}")
    a4.metric("Güven", f"{last['Güven']}/100")

    st.write(f"**Karar:** {last['Karar']}")
    st.write(f"**Tur puanı:** {last['Tur Puanı']}")

    st.write("**Karar Notu:**")
    st.write(last["Karar Notu"])

    st.write("**Sonuç Notu:**")
    st.write(last["Sonuç Notu"])

    st.write("**Mekanizma Notu:**")
    st.write(last["Mekanizma Notu"])

# -----------------------------
# Geçmiş tablo
# -----------------------------
if state["history"]:
    st.markdown("---")
    st.subheader("Karar Geçmişi")
    st.dataframe(state["history"], use_container_width=True, hide_index=True)

# -----------------------------
# Oyun bittiğinde
# -----------------------------
if state["game_over"]:
    st.markdown("---")
    st.subheader("Oyun Tamamlandı")

    st.success(final_assessment(state))

    st.write("### Nihai Göstergeler")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Son Enflasyon", f"%{state['inflation']}")
    b2.metric("Son Büyüme", f"%{state['growth']}")
    b3.metric("Son İşsizlik", f"%{state['unemployment']}")
    b4.metric("Son Güven", f"{state['trust']}/100")

    st.metric("Nihai Toplam Puan", f"{state['score']}")

    st.write("""
**Ders mesajı:**  
Merkez bankası kısa vadeli büyüme baskısı ile uzun vadeli fiyat istikrarı arasında zor bir denge kurar.  
Bağımsızlık, bu kararların siyasi takvim yerine ekonomik göstergelere göre alınmasını kolaylaştırır.
""")

    if st.button("Oyunu Yeniden Başlat"):
        reset_game()
        st.rerun()
