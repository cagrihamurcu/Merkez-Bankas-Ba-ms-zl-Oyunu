import random
import streamlit as st

st.set_page_config(page_title="Merkez Bankası Bağımsızlığı Oyunu", layout="centered")


# -----------------------------
# Senaryolar
# -----------------------------
SCENARIOS = [
    {
        "title": "Seçim Öncesi Baskı",
        "text": "Hükümet büyümeyi hızlandırmak için faiz indirimi istiyor. Ancak enflasyon hâlâ yüksek.",
        "pressure": True,
    },
    {
        "title": "Kur Şoku",
        "text": "Kur yükseldi. İthal maliyetleri arttı. Enflasyon baskısı güçleniyor.",
        "pressure": False,
    },
    {
        "title": "Büyüme Zayıflıyor",
        "text": "Şirket yatırımları yavaşladı. İşsizlik artış eğiliminde. Piyasa destek bekliyor.",
        "pressure": True,
    },
    {
        "title": "Beklentiler Bozuluyor",
        "text": "Piyasa aktörleri merkez bankasının kararlılığından emin değil. Güven kırılgan.",
        "pressure": False,
    },
]


# -----------------------------
# Başlangıç
# -----------------------------
def init_game():
    st.session_state.round = 1
    st.session_state.max_rounds = 3
    st.session_state.inflation = 18
    st.session_state.growth = 3
    st.session_state.unemployment = 9
    st.session_state.trust = 55
    st.session_state.score = 0
    st.session_state.history = []
    st.session_state.message = ""
    st.session_state.game_over = False
    st.session_state.current_scenario = random.choice(SCENARIOS)


if "round" not in st.session_state:
    init_game()


# -----------------------------
# Karar motoru
# -----------------------------
def apply_decision(decision, scenario):
    inflation = st.session_state.inflation
    growth = st.session_state.growth
    unemployment = st.session_state.unemployment
    trust = st.session_state.trust
    score = 0

    pressure = scenario["pressure"]
    title = scenario["title"]

    if decision == "Faizi Artır":
        inflation -= 2
        growth -= 1
        unemployment += 1
        trust += 8
        score += 8

        if pressure:
            growth -= 1
            trust += 2
            message = (
                "Siyasi baskıya rağmen sıkılaştırma yapıldı. "
                "Enflasyon kontrol altına alınmaya çalışıldı, güven arttı; "
                "ancak kısa vadede büyüme zayıfladı."
            )
        else:
            message = (
                "Sıkılaştırıcı politika uygulandı. "
                "Enflasyon baskısı azaldı, merkez bankası güven kazandı."
            )

    elif decision == "Faizi Sabit Tut":
        inflation -= 0.5
        growth += 0
        unemployment += 0
        trust += 2
        score += 5

        if title == "Beklentiler Bozuluyor":
            trust -= 3
            inflation += 1
            score -= 2
            message = (
                "Faiz sabit tutuldu; ancak piyasa bunu yetersiz tepki olarak gördü. "
                "Beklentiler tam olarak toparlanmadı."
            )
        else:
            message = (
                "Temkinli bir karar verildi. "
                "Kısa vadede sert bir bozulma yaşanmadı; fakat etki sınırlı kaldı."
            )

    elif decision == "Faizi İndir":
        inflation += 2
        growth += 1
        unemployment -= 1
        trust -= 7
        score += 2

        if pressure:
            growth += 1
            trust -= 3
            inflation += 1
            score -= 3
            message = (
                "Siyasi baskıya uyuldu. "
                "Kısa vadede büyüme desteklendi ve işsizlik baskısı azaldı; "
                "ancak enflasyon yükseldi ve merkez bankasına güven zayıfladı."
            )
        else:
            message = (
                "Genişleyici politika uygulandı. "
                "Büyüme kısa vadede desteklendi; ancak fiyat istikrarı zarar gördü."
            )

    # Senaryo bazlı ek etkiler
    if title == "Kur Şoku" and decision == "Faizi İndir":
        inflation += 2
        trust -= 3
        score -= 3
        message += " Kur şoku altında faiz indirimi ek enflasyon ve güven kaybı yarattı."

    if title == "Büyüme Zayıflıyor" and decision == "Faizi Artır":
        growth -= 1
        unemployment += 1
        score -= 1
        message += " Zayıf büyüme ortamında bu karar reel ekonomi üzerinde ek baskı oluşturdu."

    # Alt-üst sınırlar
    st.session_state.inflation = max(0, round(inflation, 1))
    st.session_state.growth = round(growth, 1)
    st.session_state.unemployment = max(0, round(unemployment, 1))
    st.session_state.trust = min(100, max(0, round(trust, 1)))
    st.session_state.score += score
    st.session_state.message = message

    st.session_state.history.append(
        {
            "Tur": st.session_state.round,
            "Senaryo": title,
            "Karar": decision,
            "Enflasyon": st.session_state.inflation,
            "Büyüme": st.session_state.growth,
            "İşsizlik": st.session_state.unemployment,
            "Güven": st.session_state.trust,
            "Puan": st.session_state.score,
        }
    )


def next_round():
    st.session_state.round += 1
    if st.session_state.round > st.session_state.max_rounds:
        st.session_state.game_over = True
    else:
        st.session_state.current_scenario = random.choice(SCENARIOS)


def final_comment():
    inf = st.session_state.inflation
    trust = st.session_state.trust
    score = st.session_state.score

    if inf <= 15 and trust >= 60 and score >= 18:
        return "Başarılı performans: Fiyat istikrarı ve kurumsal güven arasında güçlü bir denge kurdunuz."
    elif inf <= 20 and trust >= 50:
        return "Orta düzey performans: Ekonomi yönetilebilir kaldı; ancak daha güçlü bir politika çerçevesi mümkündü."
    else:
        return "Zayıf performans: Kısa vadeli baskılar uzun vadeli istikrarın önüne geçti."


# -----------------------------
# Arayüz
# -----------------------------
st.title("🏦 Merkez Bankası Bağımsızlığı Oyunu")
st.caption("3 turlu sınıf içi politika simülasyonu")

c1, c2 = st.columns(2)
c1.metric("Enflasyon", f"%{st.session_state.inflation}")
c2.metric("Büyüme", f"%{st.session_state.growth}")

c3, c4 = st.columns(2)
c3.metric("İşsizlik", f"%{st.session_state.unemployment}")
c4.metric("Güven", f"{st.session_state.trust}/100")

st.metric("Toplam Puan", st.session_state.score)
st.progress(
    (st.session_state.round - 1) / st.session_state.max_rounds,
    text=f"Tur {st.session_state.round} / {st.session_state.max_rounds}"
)

st.write("---")

if not st.session_state.game_over:
    scenario = st.session_state.current_scenario

    st.subheader(f"Tur {st.session_state.round}: {scenario['title']}")
    st.write(scenario["text"])

    if scenario["pressure"]:
        st.warning("Bu turda siyasi baskı var.")
    else:
        st.info("Bu turda karar daha çok teknik değerlendirmeye dayanıyor.")

    decision = st.radio(
        "Merkez bankası başkanı olarak kararınız nedir?",
        ["Faizi Artır", "Faizi Sabit Tut", "Faizi İndir"],
        horizontal=True,
    )

    if st.button("Kararı Uygula", type="primary"):
        apply_decision(decision, scenario)
        next_round()
        st.rerun()

if st.session_state.message:
    st.write("---")
    st.subheader("Sonuç")
    st.success(st.session_state.message)

if st.session_state.history:
    st.write("---")
    st.subheader("Karar Geçmişi")
    st.dataframe(st.session_state.history, use_container_width=True)

if st.session_state.game_over:
    st.write("---")
    st.subheader("Oyun Bitti")
    st.info(final_comment())

    st.write(
        """
**Ders mesajı:**  
Merkez bankası bağımsızlığı özellikle siyasi baskının yükseldiği dönemlerde önem kazanır.  
Kısa vadeli büyüme için alınan gevşek kararlar, uzun vadede enflasyon ve güven kaybı yaratabilir.
"""
    )

if st.button("Baştan Başlat"):
    init_game()
    st.rerun()
