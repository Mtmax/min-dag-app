import streamlit as st
import json
import os
from datetime import datetime, date
import pytz
import calendar
import streamlit.components.v1 as components

# Mapp för användardata
DATA_DIR = "anv_data"
USERS_FILE = "anvandare.json"
VATTENMÅL_DL = 20  # 2 liter = 20 dl
PROMENADMÅL_MINUTER = 30  # Målet är 30 minuter

def ladda_anvandare():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            st.warning(f"Filen '{USERS_FILE}' var felaktig och har nollställts.")
    # Återställ om filen är tom eller felaktig
    data = {"Kalle": ""}
    spara_anvandare(data)
    return data

def spara_anvandare(anvandare):
    with open(USERS_FILE, "w") as f:
        json.dump(anvandare, f)

def nu_svensk_tid():
    svensk_tz = pytz.timezone("Europe/Stockholm")
    return datetime.now(svensk_tz)

GODKÄNDA_ANVÄNDARE = ladda_anvandare() or {}

def lagg_till_anvandare(namn):
    if namn not in GODKÄNDA_ANVÄNDARE:
        GODKÄNDA_ANVÄNDARE[namn] = ""
        spara_anvandare(GODKÄNDA_ANVÄNDARE)
        return True
    return False

# --- Hjälpfunktioner ---
def ladda_data(anv):
    filnamn = os.path.join(DATA_DIR, f"{anv}.json")
    if os.path.exists(filnamn):
        with open(filnamn, "r") as f:
            return json.load(f)
    else:
        return {
            "datum": str(date.today()),
            "vatten": 0,
            "vatten_tid": [],
            "promenad": 0,
            "promenad_tid": [],
            "streak": 0,
            "veckodata": {},
            "fodelsedagar": []  # 👈 detta är nytt
}

def spara_data(anv, data):
    filnamn = os.path.join(DATA_DIR, f"{anv}.json")
    with open(filnamn, "w") as f:
        json.dump(data, f)

# --- Startgränssnitt ---
st.set_page_config(page_title="Min dag", layout="centered", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
    button:hover, button:focus, button:active {
        color: inherit !important;
    }
    </style>
""", unsafe_allow_html=True)
if "anvandare" not in st.session_state:
    st.session_state.anvandare = None
if "visa_bekraftelse" not in st.session_state:
    st.session_state["visa_bekraftelse"] = False
st.title("🍀 Min dag")
if st.session_state.anvandare:
    sida = st.selectbox("Navigera", ["Hem", "Vatten", "Promenad", "Födelsedagar", "Veckovy (kommande)", "Avsluta"])
else:
    sida = "Hem"
    
if st.session_state.anvandare is None:
    st.subheader("Ange ditt namn:")
    namn_input_raw = st.text_input("", key="namn_input", placeholder="Ange ditt namn", label_visibility="collapsed")
    login = st.button("Fortsätt")
    namn_input = namn_input_raw.strip() if namn_input_raw else ""
    if not namn_input:
        st.stop()

    if login and namn_input:
        pass  # behåll originalformatet
        if isinstance(GODKÄNDA_ANVÄNDARE, dict) and namn_input in GODKÄNDA_ANVÄNDARE:
            st.session_state.anvandare = namn_input
            st.rerun()
        elif namn_input_raw:  # Only show error if something has been typed
            st.error("❌ Användaren finns inte. Vänligen skriv in ett annat namn eller kontakta administratören.")

anv = st.session_state.anvandare if "anvandare" in st.session_state else None

if anv is not None and anv in GODKÄNDA_ANVÄNDARE:
    if anv == "admin":
        st.info("🔐 Adminläge: Du kan lägga till nya användare.")
        nytt_namn = st.text_input("Lägg till ny användare:")
        if st.button("Lägg till användare"):
            nytt_namn = nytt_namn.strip()
            if nytt_namn:
                if lagg_till_anvandare(nytt_namn):
                    st.success(f"✅ Användare '{nytt_namn}' har lagts till.")
                else:
                    st.warning(f"⚠️ Användare '{nytt_namn}' finns redan.")

        st.markdown("### 👥 Nuvarande användare:")
        for anvandare in GODKÄNDA_ANVÄNDARE:
            cols = st.columns([3, 1, 1])
            cols[0].markdown(f"- {anvandare}")
            if anvandare != "admin":  # admin ska inte kunna raderas
                if cols[1].button("✏️ Ändra", key=f"edit_{anvandare}"):
                    st.session_state["edit_user"] = anvandare
                if cols[2].button("❌ Ta bort", key=f"delete_{anvandare}"):
                    del GODKÄNDA_ANVÄNDARE[anvandare]
                    spara_anvandare(GODKÄNDA_ANVÄNDARE)
                    st.success(f"Användaren '{anvandare}' har tagits bort.")
                    st.rerun()

        st.markdown("### 🔑 Lägg till eller uppdatera lösenord för användare")
        anv_for_losen = st.selectbox("Välj användare:", list(GODKÄNDA_ANVÄNDARE.keys()))
        nytt_losen = st.text_input("Ange nytt lösenord:", type="password")
        if st.button("Spara lösenord"):
            if nytt_losen:
                GODKÄNDA_ANVÄNDARE[anv_for_losen] = nytt_losen
                spara_anvandare(GODKÄNDA_ANVÄNDARE)
                st.success(f"Lösenord för '{anv_for_losen}' har sparats.")
            else:
                st.warning("Vänligen skriv in ett giltigt lösenord.")

        if "edit_user" in st.session_state:
            gammalt_namn = st.session_state["edit_user"]
            nytt_namn = st.text_input("Nytt namn:", value=gammalt_namn, key="nytt_namn_input")
            if st.button("Spara nytt namn"):
                nytt_namn = nytt_namn.strip()
                if nytt_namn and nytt_namn not in GODKÄNDA_ANVÄNDARE:
                    # byt namn i listan
                    index = list(GODKÄNDA_ANVÄNDARE.keys()).index(gammalt_namn)
                    GODKÄNDA_ANVÄNDARE[nytt_namn] = GODKÄNDA_ANVÄNDARE.pop(gammalt_namn)
                    spara_anvandare(GODKÄNDA_ANVÄNDARE)
                    # byt namn på fil om data finns
                    gammalt_filnamn = os.path.join(DATA_DIR, f"{gammalt_namn}.json")
                    nytt_filnamn = os.path.join(DATA_DIR, f"{nytt_namn}.json")
                    if os.path.exists(gammalt_filnamn):
                        os.rename(gammalt_filnamn, nytt_filnamn)
                    del st.session_state["edit_user"]
                    st.success(f"Användarnamn ändrat till '{nytt_namn}'.")
                    st.rerun()
                else:
                    st.warning("Namn finns redan eller är ogiltigt.")
            if st.button("Avbryt"):
                del st.session_state["edit_user"]
                st.rerun()

    data = ladda_data(anv)
    
    st.header(f"Hej, {st.session_state.anvandare.capitalize()}!")
    veckodagar = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]
    idag = date.today()
    veckodag = veckodagar[idag.weekday()]
    st.markdown(f"**Idag är det {veckodag} den {idag.day} {idag.strftime('%B').capitalize()}**")

    if sida == "Hem":
        st.subheader("📊 Sammanställning för idag")
        if data["vatten"] > 0 or data["promenad"] > 0:
            if data["vatten"] > 0:
                tider_vatten = ", ".join(data["vatten_tid"])
                st.markdown(f"- 💧 **{data['vatten']} glas vatten**")
                st.markdown(f"  - Tider: {tider_vatten}")
            if data["promenad"] > 0:
                tider_promenad = ", ".join(data["promenad_tid"])
                st.markdown(f"- 🚶 **{data['promenad']} minuter promenad**")
                st.markdown(f"  - Tider: {tider_promenad}")
        else:
            st.info("Ingen registrering ännu för idag.")

        if "fodelsedagar" in data and data["fodelsedagar"]:
            st.markdown("### 🎂 Kommande födelsedagar")
            idag = date.today()
            kommande = []
            visade = set()
 
            for f in data["fodelsedagar"]:
                namn = f["namn"]
                datum = datetime.strptime(f["datum"], "%Y-%m-%d").date()
                datum_i_ar = datum.replace(year=idag.year)
                if datum_i_ar < idag:
                    datum_i_ar = datum_i_ar.replace(year=idag.year + 1)
                dagar_kvar = (datum_i_ar - idag).days
                alder = datum_i_ar.year - datum.year
                veckodag = ["måndag", "tisdag", "onsdag", "torsdag", "fredag", "lördag", "söndag"][datum_i_ar.weekday()]
                manad = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober", "november", "december"][datum_i_ar.month - 1]
                nyckel = (namn, datum_i_ar)
 
                if nyckel not in visade:
                    visade.add(nyckel)
                    if dagar_kvar == 0:
                        st.success(f"🎉 Idag fyller {namn} {alder} år!")
                    elif dagar_kvar == 5:
                        st.info(f"🔔 Om 5 dagar fyller {namn} {alder} år ({veckodag} den {datum_i_ar.day} {manad})")
                    else:
                        text = f"{namn} fyller {alder} år {veckodag} den {datum_i_ar.day} {manad} (om {dagar_kvar} dagar)"
                        kommande.append((dagar_kvar, text))
 
            kommande.sort()
            for _, text in kommande:
                st.markdown(f"- {text}")
    elif sida == "Vatten":
        st.subheader("💧 Har du druckit vatten?")
        st.info("Ditt mål är 2 liter = 10 glas")
        st.markdown("###")
        if st.button("Jag drack ett glas", use_container_width=True):
            if "vatten_tid" not in data:
                data["vatten_tid"] = []
            data["vatten_tid"].append(nu_svensk_tid().strftime("%H:%M"))
            data["vatten"] += 1
            spara_data(anv, data)
            st.success("Du har registrerat att du druckit vatten idag.")
        if data["vatten"] > 0:
            antal_glas = data["vatten"]
            tot_dl = antal_glas * 2
            tot_l = tot_dl / 10

            st.markdown(f"Du har druckit **{antal_glas} glas av {VATTENMÅL_DL // 2}**")
            if antal_glas == VATTENMÅL_DL // 2:
                st.info("🟢 Du är klar med dagens mål!")
            st.progress(min(tot_dl / VATTENMÅL_DL, 1.0))
            
            if tot_dl < 10:
                st.info("🔵 Bra start! Fortsätt dricka.")
            elif tot_dl < VATTENMÅL_DL:
                kvar = int((VATTENMÅL_DL - tot_dl) / 2)
                st.info(f"🟡 Snart där! Du behöver dricka {kvar} glas till.")
            else:
                st.success(f"🟢 Du har klarat målet för idag! 🏅 Bra jobbat – {VATTENMÅL_DL // 10} liter vatten!")

            tider = ", ".join(data["vatten_tid"]) if "vatten_tid" in data else "okänd tid"
            st.markdown(f"🔘 **Du drack klockan:** {tider}")
        else:
            st.info("Du har inte registrerat något vatten ännu.")
        st.divider()
        if st.button("🔄 Rensa dagens data", use_container_width=True):
            st.session_state["visa_bekraftelse"] = True

        if st.session_state.get("visa_bekraftelse", False):
            st.warning("Är du säker på att du vill rensa dagens registreringar?")
            if st.button("✅ Ja, rensa", use_container_width=True):
                data["vatten"] = 0
                data["vatten_tid"] = []
                data["promenad"] = 0
                data["promenad_tid"] = []
                data["streak"] = 0
                data["datum"] = str(date.today())
                spara_data(anv, data)
                st.success("Dagens registreringar har rensats.")
                st.session_state["visa_bekraftelse"] = False
                st.rerun()
            if st.button("❌ Avbryt", use_container_width=True):
                st.session_state["visa_bekraftelse"] = False
                st.rerun()
    elif sida == "Promenad":
        st.subheader("🚶 Har du promenerat?")
        st.info(f"Ditt mål är {PROMENADMÅL_MINUTER} minuter.")
        minut_val = st.radio("Välj antal minuter:", [10, 20, "30 minuter eller mer"], horizontal=True)
        st.markdown("###")
        if st.button("Jag gick en promenad", use_container_width=True):
            if minut_val == "30 minuter eller mer":
                minut_val = 30  # Sätter till 30 om användaren väljer detta alternativ
            if "promenad_tid" not in data:
                data["promenad_tid"] = []
            data["promenad_tid"].append(nu_svensk_tid().strftime("%H:%M"))
            data["promenad"] += minut_val
            data["streak"] += 1 if data["promenad"] == minut_val else 0
            spara_data(anv, data)
            st.success(f"Promenad registrerad kl {data['promenad_tid'][-1]}. Totalt {data['promenad']} minuter idag.")

        if data["promenad"] > 0:
            tider = ", ".join(data["promenad_tid"]) if "promenad_tid" in data else "okänd tid"
            st.markdown(f"Du har promenerat **{data['promenad']} minuter av {PROMENADMÅL_MINUTER}**")
            if data["promenad"] == PROMENADMÅL_MINUTER:
                st.info("🟢 Du är klar med dagens mål!")
            
            st.progress(min(data["promenad"] / PROMENADMÅL_MINUTER, 1.0))
            if data["promenad"] < 10:
                st.info("🔵 Bra start! Fortsätt gärna med en promenad till.")
            elif data["promenad"] < PROMENADMÅL_MINUTER:
                kvar = PROMENADMÅL_MINUTER - data["promenad"]
                st.info(f"🟡 Snart där! Bara {kvar} minuter kvar.")
            else:
                st.success("🟢 Du har nått målet för idag! 🏅")

            st.markdown(f"Du gick klockan: {tider}")
        st.divider()
        if st.button("🔄 Rensa dagens data", use_container_width=True):
            st.session_state["visa_bekraftelse"] = True

        if st.session_state.get("visa_bekraftelse", False):
            st.warning("Är du säker på att du vill rensa dagens registreringar?")
            if st.button("✅ Ja, rensa", use_container_width=True):
                data["vatten"] = 0
                data["vatten_tid"] = []
                data["promenad"] = 0
                data["promenad_tid"] = []
                data["streak"] = 0
                data["datum"] = str(date.today())
                spara_data(anv, data)
                st.success("Dagens registreringar har rensats.")
                st.session_state["visa_bekraftelse"] = False
                st.rerun()
            if st.button("❌ Avbryt", use_container_width=True):
                st.session_state["visa_bekraftelse"] = False
                st.rerun()
    elif sida == "Veckovy (kommande)":
        st.subheader("📅 Veckosammanställning")
    elif sida == "Födelsedagar":
        st.subheader("🎂 Födelsedagar")
        st.markdown("Lägg till en födelsedag i formatet `Namn, YYYY-MM-DD`.")
        ny_fodelsedag = st.text_input("Ny födelsedag")
        if ny_fodelsedag:
            try:
                namn, datum_str = [s.strip() for s in ny_fodelsedag.split(",")]
                datetime.strptime(datum_str, "%Y-%m-%d")  # validera
                if "fodelsedagar" not in data:
                    data["fodelsedagar"] = []
                redan_finns = any(fd["namn"] == namn and fd["datum"] == datum_str for fd in data["fodelsedagar"])
                if redan_finns:
                    st.warning(f"{namn}s födelsedag är redan tillagd.")
                else:
                    redan_finns = any(fd["namn"] == namn and fd["datum"] == datum_str for fd in data["fodelsedagar"])
                    if redan_finns:
                        st.warning(f"{namn}s födelsedag är redan tillagd.")
                    else:
                        data["fodelsedagar"].append({"namn": namn, "datum": datum_str})
                        spara_data(anv, data)
                        st.success(f"{namn}s födelsedag har lagts till!")
                        st.rerun()
            except Exception:
                st.warning("Fel format. Använd Namn, YYYY-MM-DD.")

        # Ta bort eventuella dubbletter i data["fodelsedagar"]
        if "fodelsedagar" in data:
            seen = set()
            unique_birthdays = []
            for fd in data["fodelsedagar"]:
                key = (fd["namn"], fd["datum"])
                if key not in seen:
                    seen.add(key)
                    unique_birthdays.append(fd)
            if len(unique_birthdays) != len(data["fodelsedagar"]):
                data["fodelsedagar"] = unique_birthdays
                spara_data(anv, data)
        if "fodelsedagar" in data:
            idag = date.today()
            kommande = []

            for i, f in enumerate(data["fodelsedagar"]):
                namn = f["namn"]
                datum = datetime.strptime(f["datum"], "%Y-%m-%d").date()
                datum_i_ar = datum.replace(year=idag.year)
                if datum_i_ar < idag:
                    datum_i_ar = datum_i_ar.replace(year=idag.year + 1)

                dagar_kvar = (datum_i_ar - idag).days
                alder = datum_i_ar.year - datum.year
                veckodag = ["måndag", "tisdag", "onsdag", "torsdag", "fredag", "lördag", "söndag"][datum_i_ar.weekday()]
                manad = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober", "november", "december"][datum_i_ar.month - 1]

                if dagar_kvar == 0:
                    st.success(f"🎉 Idag fyller {namn} {alder} år!")
                elif dagar_kvar == 5:
                    st.info(f"🔔 Om 5 dagar fyller {namn} {alder} år ({veckodag} den {datum_i_ar.day} {manad})")
                else:
                    kommande.append((dagar_kvar, namn, alder, veckodag, datum_i_ar, f["datum"]))

            if kommande:
                kommande.sort()
                st.markdown("#### Kommande födelsedagar")
                for i, (dagar, namn, alder, veckodag, datum_i_ar, datum_str) in enumerate(kommande):
                    manad = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober", "november", "december"][datum_i_ar.month - 1]
                    datumtext = f"{veckodag} den {datum_i_ar.day} {manad}"
                    st.markdown(f"- {namn} fyller {alder} år {datumtext} (om {dagar} dagar)")
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button(f"✏️ Redigera", key=f"edit_bday_{i}"):
                            st.session_state["edit_fodelsedag_index"] = i
                    with col2:
                        if st.button(f"❌ Ta bort", key=f"delete_bday_{i}"):
                            data["fodelsedagar"] = [fd for fd in data["fodelsedagar"] if not (fd["namn"] == namn and fd["datum"] == datum_str)]
                            spara_data(anv, data)
                            st.success(f"Födelsedag för {namn} borttagen.")
                            st.rerun()

        if "edit_fodelsedag_index" in st.session_state:
            idx = st.session_state["edit_fodelsedag_index"]
            if idx < len(data["fodelsedagar"]):
                fd = data["fodelsedagar"][idx]
                nytt_namn = st.text_input("Redigera namn:", value=fd["namn"], key="edit_namn")
                nytt_datum = st.text_input("Redigera datum (YYYY-MM-DD):", value=fd["datum"], key="edit_datum")
                if st.button("💾 Spara ändringar"):
                    try:
                        datetime.strptime(nytt_datum, "%Y-%m-%d")  # validera
                        data["fodelsedagar"][idx] = {"namn": nytt_namn, "datum": nytt_datum}
                        spara_data(anv, data)
                        st.success("Födelsedag uppdaterad.")
                        del st.session_state["edit_fodelsedag_index"]
                        st.rerun()
                    except Exception:
                        st.warning("Fel datumformat. Använd YYYY-MM-DD.")
                if st.button("❌ Avbryt ändring"):
                    del st.session_state["edit_fodelsedag_index"]
                    st.rerun()

    spara_data(anv, data)

    if data["datum"] != str(date.today()):
        dagens_datum = data["datum"]
        if "veckodata" not in data:
            data["veckodata"] = {}
        data["veckodata"][dagens_datum] = {
            "vatten": data["vatten"],
            "vatten_tid": data["vatten_tid"],
            "promenad": data["promenad"],
            "promenad_tid": data["promenad_tid"]
        }
        data = {
            "datum": str(date.today()),
            "vatten": 0,
            "vatten_tid": [],
            "promenad": 0,
            "promenad_tid": [],
            "streak": 0,
            "veckodata": {}
        }
        spara_data(anv, data)
