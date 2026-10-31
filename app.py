import streamlit as st
import json
import uuid
import os
from datetime import datetime
from urllib.parse import quote_plus

# ==================================================
# 1. INSTELLINGEN
# ==================================================

st.set_page_config(
    page_title="De Kletsende Kieten",
    page_icon="🥾",
    layout="wide"
)

DATA_FILE = "wandelplatform_data.json"
CALENDAR_URL = "https://wandel.be/wandelkalender/"


# ==================================================
# 2. GEGEVENS
# ==================================================

def naar_tekst(waarde):
    if waarde is None:
        return ""
    if isinstance(waarde, float) and waarde.is_integer():
        return str(int(waarde))
    return str(waarde)


def normaliseer_afstanden(afstanden):
    if afstanden is None:
        return []
    if isinstance(afstanden, (str, int, float)):
        afstanden = [afstanden]
    if not isinstance(afstanden, list):
        return []

    return [
        naar_tekst(afstand).strip()
        for afstand in afstanden
        if naar_tekst(afstand).strip()
    ]


def lege_data():
    return {
        "walks": [],
        "signups": [],
        "banner_x": 50,
        "banner_y": 50
    }


def load_data():
    if not os.path.exists(DATA_FILE):
        return lege_data()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            opgeslagen_data = json.load(file)

        if not isinstance(opgeslagen_data, dict):
            return lege_data()

        if not isinstance(opgeslagen_data.get("walks"), list):
            opgeslagen_data["walks"] = []

        if not isinstance(opgeslagen_data.get("signups"), list):
            opgeslagen_data["signups"] = []

        opgeslagen_data.setdefault("banner_x", 50)
        opgeslagen_data.setdefault("banner_y", 50)

        nieuwe_wandelingen = []

        for i, wandeling in enumerate(opgeslagen_data["walks"]):
            if not isinstance(wandeling, dict):
                continue

            standaard = {
                "id": str(uuid.uuid4()),
                "name": f"Wandeling {i + 1}",
                "date": "",
                "time": "09:00",
                "location": "",
                "maps_link": "",
                "distances": [],
                "group_distance": "",
                "description": "",
                "notes": ""
            }

            for veld, waarde in standaard.items():
                wandeling.setdefault(veld, waarde)

            for veld in [
                "name", "date", "time", "location", "maps_link",
                "group_distance", "description", "notes"
            ]:
                wandeling[veld] = naar_tekst(wandeling.get(veld))

            wandeling["distances"] = normaliseer_afstanden(
                wandeling.get("distances")
            )

            nieuwe_wandelingen.append(wandeling)

        opgeslagen_data["walks"] = nieuwe_wandelingen

        nieuwe_inschrijvingen = []

        for inschrijving in opgeslagen_data["signups"]:
            if not isinstance(inschrijving, dict):
                continue

            standaard = {
                "id": str(uuid.uuid4()),
                "walk_id": "",
                "walk_name": "Wandeling",
                "person_name": "Onbekend",
                "distances": [],
                "coming": "Ja",
                "paid": "Nee"
            }

            for veld, waarde in standaard.items():
                inschrijving.setdefault(veld, waarde)

            for veld in [
                "walk_id", "walk_name", "person_name", "coming", "paid"
            ]:
                inschrijving[veld] = naar_tekst(inschrijving.get(veld))

            inschrijving["distances"] = normaliseer_afstanden(
                inschrijving.get("distances")
            )

            nieuwe_inschrijvingen.append(inschrijving)

        opgeslagen_data["signups"] = nieuwe_inschrijvingen

        return opgeslagen_data

    except (json.JSONDecodeError, OSError, TypeError):
        st.error(
            "Het gegevensbestand kon niet goed worden gelezen. "
            "Controleer wandelplatform_data.json."
        )
        return lege_data()


def save_data(data):
    tijdelijk_bestand = DATA_FILE + ".tmp"

    with open(tijdelijk_bestand, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    os.replace(tijdelijk_bestand, DATA_FILE)


data = load_data()


# ==================================================
# 3. HULPFUNCTIES
# ==================================================

def maak_maps_link(adres):
    if not adres.strip():
        return ""

    return (
        "https://www.google.com/maps/search/?api=1&query="
        + quote_plus(adres)
    )


def datum_omzetten(datum):
    try:
        return datetime.strptime(datum, "%d/%m/%Y").date()
    except (ValueError, TypeError):
        return None


def wandeling_sorteren(wandeling):
    """
    Nieuwste datum bovenaan.
    Oudste datum onderaan.
    Wandelingen zonder geldige datum komen helemaal onderaan.
    """

    datum = datum_omzetten(wandeling.get("date", ""))

    if datum is None:
        return (0, datetime.min)

    try:
        tijd = datetime.strptime(
            wandeling.get("time", "09:00"),
            "%H:%M"
        ).time()
    except (ValueError, TypeError):
        tijd = datetime.min.time()

    return (1, datetime.combine(datum, tijd))


def zoek_wandeling(walk_id):
    for wandeling in data["walks"]:
        if wandeling.get("id") == walk_id:
            return wandeling

    return None


def afstandstekst(afstanden):
    afstanden = normaliseer_afstanden(afstanden)

    if afstanden:
        return " / ".join(afstanden)

    return "Nog geen afstanden ingesteld"


def verwijder_inschrijvingen(walk_id):
    data["signups"] = [
        inschrijving
        for inschrijving in data["signups"]
        if inschrijving.get("walk_id") != walk_id
    ]


def unieke_wandeling_keuzes(wandelingen):
    keuzes = {}

    for wandeling in wandelingen:
        walk_id = wandeling.get("id", "")
        naam = wandeling.get("name") or "Wandeling"
        datum = wandeling.get("date") or "Datum onbekend"

        label = f"{naam} - {datum} ({walk_id[:6]})"
        keuzes[label] = walk_id

    return keuzes


def toon_veld(label, waarde):
    st.markdown(
        f'<div class="veld">'
        f'<span class="veld-label">{label}</span>'
        f'<span class="veld-waarde">{waarde if waarde else "—"}</span>'
        f'</div>',
        unsafe_allow_html=True
    )


# ==================================================
# 4. OPMAAK
# ==================================================

st.markdown(
    """
    <style>

    .block-container {
    padding-top: 0.3rem;
    padding-bottom: 0.5rem;
    max-width: 1100px;
}

.stTabs {
    margin-top: -0.5rem;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    padding-top: 0.35rem;
    padding-bottom: 0.35rem;
}

div[data-testid="stCaptionContainer"] {
    margin-bottom: 0;
}
    h1, h2, h3 {
        color: #315c3b;
    }

    div[data-testid="stImage"] img {
        height: 180px;
        width: 100%;
        object-fit: cover;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 16px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #a9bda9;
        border-radius: 12px;
        padding: 0.55rem 0.8rem 0.45rem 0.8rem;
        background: rgba(120, 155, 120, 0.045);
        margin-bottom: 0.4rem;
    }

    .veld {
        padding: 0.08rem 0;
        line-height: 1.2;
    }

    .veld-label {
        display: block;
        color: #68756b;
        font-size: 0.72rem;
        margin-bottom: 0.04rem;
    }

    .veld-waarde {
        display: block;
        font-weight: 650;
        font-size: 0.92rem;
        overflow-wrap: anywhere;
    }

    .wandeling-scheiding {
        height: 6px;
        margin: 0.7rem 0 0.9rem 0;
        border-top: 1px solid #dce6dc;
        border-bottom: 2px solid #9eb49e;
        background: #f2f6f1;
        border-radius: 3px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# 5. BANNER
# ==================================================

banner_bestand = None

for bestand in [
    "kletsende_kieten_banner.png",
    "kletsende_kieten_banner.jpg"
]:
    if os.path.exists(bestand):
        banner_bestand = bestand
        break

if banner_bestand:

    st.markdown(
        f"""
        <style>
        div[data-testid="stImage"] img {{
            object-position:
            {data["banner_x"]}% {data["banner_y"]}%;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.image(banner_bestand, use_container_width=True)

else:
    st.info(
        "Er is nog geen bannerfoto toegevoegd. "
        "Je kunt die toevoegen via het tabblad Beheer."
    )


# ==================================================
# 6. WELKOMSTTEKST
# ==================================================

st.title("🥾 De Kletsende Kieten")

st.markdown(
    "**Gezellig samen zijn, fun maken en vooral genieten! 😄🥾**"
)

st.write(
    "Niets moet, alles mag. Gewoon samen wandelen, "
    "lachen en een leuke tijd hebben. ❤️"
)

st.markdown(
    '<p style="margin:0 0 20px 0; padding:0; font-size:13px; line-height:18px; color:gray;">Gemaakt door Katelijne Davit</p>',
    unsafe_allow_html=True
)


# ==================================================
# 7. TABS
# ==================================================

tab_wandelingen, tab_inschrijven, tab_kalender, tab_beheer = st.tabs(
    [
        "🥾 Wandelingen",
        "✏️ Inschrijven",
        "📅 Wandelkalender",
        "⚙️ Beheer"
    ]
)


# ==================================================
# TAB 1 - WANDELINGEN
# ==================================================

with tab_wandelingen:

    
    zoekterm = st.text_input(
        "🔎 Zoek een wandeling, plaats of datum",
        placeholder="Typ bijvoorbeeld Brugge of 12/11/2026"
    )

    wandelingen = sorted(
        data["walks"],
        key=wandeling_sorteren,
        reverse=True
    )

    if zoekterm:
        zoekterm_klein = zoekterm.lower()

        wandelingen = [
            wandeling
            for wandeling in wandelingen
            if zoekterm_klein in (
                wandeling.get("name", "") + " " +
                wandeling.get("location", "") + " " +
                wandeling.get("date", "") + " " +
                wandeling.get("description", "")
            ).lower()
        ]

    if not wandelingen:
        st.info("Er zijn momenteel geen wandelingen gevonden.")

    for index, wandeling in enumerate(wandelingen):

        walk_id = wandeling["id"]

        with st.container(border=True):

            st.subheader(
                "🥾 " + wandeling.get("name", "Wandeling")
            )

            # Alle kerngegevens naast elkaar.

            kolom_datum, kolom_uur, kolom_plaats, kolom_afstanden = (
                st.columns([1.25, 0.8, 2.2, 2.2])
            )

            with kolom_datum:
                toon_veld(
                    "DATUM",
                    wandeling.get("date", "")
                )

            with kolom_uur:
                toon_veld(
                    "VERTREK",
                    wandeling.get("time", "")
                )

            with kolom_plaats:
                toon_veld(
                    "VERTREKPLAATS",
                    wandeling.get("location", "")
                )

            with kolom_afstanden:
                toon_veld(
                    "MOGELIJKE AFSTANDEN",
                    afstandstekst(wandeling.get("distances", []))
                )

            if wandeling.get("description"):
                st.markdown(
                    f'<div style="margin-top:0.3rem;">'
                    f'{wandeling["description"]}</div>',
                    unsafe_allow_html=True
                )

            if wandeling.get("notes"):
                st.info(wandeling["notes"])

            maps_link = wandeling.get("maps_link", "")

            if not maps_link:
                maps_link = maak_maps_link(
                    wandeling.get("location", "")
                )

            if maps_link:
                st.markdown(
                    f"[📍 Bekijk het vertrekpunt op Google Maps]({maps_link})"
                )

            # Definitieve groepsafstand.

            afstanden = normaliseer_afstanden(
                wandeling.get("distances", [])
            )

            if afstanden:

                huidige_afstand = wandeling.get("group_distance", "")

                if huidige_afstand not in afstanden:
                    huidige_afstand = afstanden[0]

                gekozen_groepsafstand = st.radio(
                    "Definitieve groepsafstand",
                    afstanden,
                    index=afstanden.index(huidige_afstand),
                    key=f"group_distance_{walk_id}",
                    horizontal=True
                )

                if gekozen_groepsafstand != wandeling.get("group_distance", ""):
                    wandeling["group_distance"] = gekozen_groepsafstand
                    save_data(data)

            else:
                st.caption("Er zijn nog geen afstanden ingesteld.")

            # Deelnemers.

            st.markdown("**👥 Wie gaat er mee?**")

            inschrijvingen = [
                inschrijving
                for inschrijving in data["signups"]
                if inschrijving.get("walk_id") == walk_id
            ]

            if not inschrijvingen:
                st.caption(
                    "Er zijn nog geen deelnemers ingeschreven."
                )

            else:

                for inschrijving in inschrijvingen:

                    status = (
                        "✅ Gaat mee"
                        if inschrijving.get("coming", "Ja") == "Ja"
                        else "❌ Gaat niet mee"
                    )

                    betaald = (
                        "✅ Betaald"
                        if inschrijving.get("paid", "Nee") == "Ja"
                        else "⏳ Nog niet betaald"
                    )

                    afstand_deelnemer = afstandstekst(
                        inschrijving.get("distances", [])
                    )

                    naam_kolom, info_kolom = st.columns([1, 4])

                    with naam_kolom:
                        st.markdown(
                            f"**{inschrijving.get('person_name', 'Onbekend')}**"
                        )

                    with info_kolom:
                        st.caption(
                            f"{status}  ·  "
                            f"Afstand: {afstand_deelnemer}  ·  "
                            f"{betaald}"
                        )

        # Duidelijke scheiding tussen wandelingen.

        if index < len(wandelingen) - 1:

            st.markdown(
                '<div class="wandeling-scheiding"></div>',
                unsafe_allow_html=True
            )


# ==================================================
# TAB 2 - INSCHRIJVEN
# ==================================================

with tab_inschrijven:

    st.header("Inschrijven voor een wandeling")

    if not data["walks"]:

        st.info("Er zijn nog geen wandelingen toegevoegd.")

    else:

        wandelingen_inschrijven = sorted(
            data["walks"],
            key=wandeling_sorteren,
            reverse=True
        )

        wandeling_keuzes = unieke_wandeling_keuzes(
            wandelingen_inschrijven
        )

        gekozen_wandeling_naam = st.selectbox(
            "Voor welke wandeling wil je inschrijven?",
            list(wandeling_keuzes.keys())
        )

        gekozen_walk_id = wandeling_keuzes[
            gekozen_wandeling_naam
        ]

        gekozen_wandeling = zoek_wandeling(gekozen_walk_id)

        if gekozen_wandeling:

            afstanden = normaliseer_afstanden(
                gekozen_wandeling.get("distances", [])
            )

            st.write(
                "**Mogelijke afstanden:** "
                + afstandstekst(afstanden)
            )

            with st.form(
                "inschrijfformulier",
                clear_on_submit=True
            ):

                voornaam = st.text_input(
                    "Je voornaam",
                    placeholder="Vul je voornaam in"
                )

                gaat_mee = st.radio(
                    "Ga je mee wandelen?",
                    ["Ja", "Nee"],
                    horizontal=True
                )

                gekozen_afstand = ""

                if afstanden:

                    gekozen_afstand = st.radio(
                        "Welke afstand wil je wandelen?",
                        afstanden,
                        horizontal=True
                    )

                else:
                    st.warning(
                        "De organisator heeft nog geen afstanden toegevoegd."
                    )

                betaald = st.radio(
                    "Heb je betaald?",
                    ["Nee", "Ja"],
                    horizontal=True
                )

                verzenden = st.form_submit_button(
                    "💾 Inschrijving bewaren",
                    use_container_width=True
                )

                if verzenden:

                    if not voornaam.strip():
                        st.error("Vul je voornaam in.")

                    elif gaat_mee == "Ja" and not gekozen_afstand:
                        st.error("Kies een afstand.")

                    else:

                        nieuwe_inschrijving = {
                            "id": str(uuid.uuid4()),
                            "walk_id": gekozen_walk_id,
                            "walk_name": gekozen_wandeling.get(
                                "name", "Wandeling"
                            ),
                            "person_name": voornaam.strip(),
                            "distances": (
                                [gekozen_afstand]
                                if gekozen_afstand and gaat_mee == "Ja"
                                else []
                            ),
                            "coming": gaat_mee,
                            "paid": betaald
                        }

                        data["signups"].append(nieuwe_inschrijving)

                        save_data(data)

                        st.success("Je inschrijving is bewaard!")
                        st.rerun()

    st.divider()

    st.subheader("Een bestaande inschrijving aanpassen")

    if data["signups"]:

        inschrijving_keuzes = {}

        for inschrijving in data["signups"]:

            wandeling = zoek_wandeling(
                inschrijving.get("walk_id")
            )

            wandeling_naam = (
                wandeling.get("name", "Wandeling")
                if wandeling
                else inschrijving.get("walk_name", "Wandeling")
            )

            label = (
                f'{inschrijving.get("person_name", "Onbekend")} - '
                f'{wandeling_naam} '
                f'({inschrijving.get("id", "")[:6]})'
            )

            inschrijving_keuzes[label] = inschrijving.get("id")

        gekozen_inschrijving_label = st.selectbox(
            "Welke inschrijving wil je aanpassen?",
            list(inschrijving_keuzes.keys())
        )

        gekozen_inschrijving_id = inschrijving_keuzes[
            gekozen_inschrijving_label
        ]

        inschrijving = next(
            (
                item
                for item in data["signups"]
                if item.get("id") == gekozen_inschrijving_id
            ),
            None
        )

        if inschrijving:

            wandeling = zoek_wandeling(
                inschrijving.get("walk_id")
            )

            if wandeling:

                afstanden = normaliseer_afstanden(
                    wandeling.get("distances", [])
                )

                huidige_afstanden = normaliseer_afstanden(
                    inschrijving.get("distances", [])
                )

                with st.form("inschrijving_aanpassen"):

                    nieuwe_naam = st.text_input(
                        "Voornaam",
                        value=inschrijving.get("person_name", "")
                    )

                    nieuwe_aanwezigheid = st.radio(
                        "Ga je mee?",
                        ["Ja", "Nee"],
                        index=(
                            0
                            if inschrijving.get("coming", "Ja") == "Ja"
                            else 1
                        ),
                        horizontal=True
                    )

                    nieuwe_afstand = ""

                    if afstanden:

                        standaard_index = 0

                        if (
                            huidige_afstanden
                            and huidige_afstanden[0] in afstanden
                        ):
                            standaard_index = afstanden.index(
                                huidige_afstanden[0]
                            )

                        nieuwe_afstand = st.radio(
                            "Welke afstand?",
                            afstanden,
                            index=standaard_index,
                            horizontal=True
                        )

                    nieuwe_betaling = st.radio(
                        "Betaald?",
                        ["Nee", "Ja"],
                        index=(
                            1
                            if inschrijving.get("paid", "Nee") == "Ja"
                            else 0
                        ),
                        horizontal=True
                    )

                    aanpassen = st.form_submit_button(
                        "Wijzigingen bewaren"
                    )

                    if aanpassen:

                        if not nieuwe_naam.strip():
                            st.error("Vul je voornaam in.")

                        elif (
                            nieuwe_aanwezigheid == "Ja"
                            and not nieuwe_afstand
                        ):
                            st.error("Kies een afstand.")

                        else:

                            inschrijving["person_name"] = nieuwe_naam.strip()
                            inschrijving["coming"] = nieuwe_aanwezigheid

                            inschrijving["distances"] = (
                                [nieuwe_afstand]
                                if nieuwe_afstand
                                and nieuwe_aanwezigheid == "Ja"
                                else []
                            )

                            inschrijving["paid"] = nieuwe_betaling

                            save_data(data)

                            st.success(
                                "Je wijzigingen zijn bewaard."
                            )

                            st.rerun()

    else:
        st.info(
            "Er zijn nog geen inschrijvingen om aan te passen."
        )


# ==================================================
# TAB 3 - EXTERNE WANDELKALENDER
# ==================================================

with tab_kalender:

    st.header("📅 Wandelkalender")

    st.write(
        "Zin in een extra wandeluitstap? "
        "Bekijk de wandelkalender van Wandel.be "
        "en ontdek georganiseerde wandeltochten."
    )

    st.link_button(
        "🥾 Open de wandelkalender van Wandel.be",
        CALENDAR_URL,
        use_container_width=True
    )

    st.caption(
        "De kalender opent in een nieuw browsertabblad. "
        "Je blijft dus gewoon op De Kletsende Kieten."
    )


# ==================================================
# TAB 4 - BEHEER
# ==================================================

with tab_beheer:

    st.header("Beheer van het wandelplatform")

    st.warning(
        "Iedere bezoeker kan dit tabblad gebruiken. "
        "Er is bewust geen wachtwoord of persoonlijke code."
    )

    beheer_wandelingen, beheer_banner, beheer_deelnemers = st.tabs(
        [
            "Wandelingen beheren",
            "Banner aanpassen",
            "Deelnemers beheren"
        ]
    )

    # --------------------------------------------------
    # WANDELINGEN BEHEREN
    # --------------------------------------------------

    with beheer_wandelingen:

        st.subheader("➕ Nieuwe wandeling toevoegen")

        with st.form(
            "nieuwe_wandeling",
            clear_on_submit=True
        ):

            naam = st.text_input("Naam van de wandeling")

            datum = st.text_input(
                "Datum",
                placeholder="Bijvoorbeeld 15/11/2026"
            )

            uur = st.text_input(
                "Vertrekuur",
                value="09:00",
                placeholder="Bijvoorbeeld 09:00"
            )

            vertrekplaats = st.text_input(
                "Vertrekplaats en adres"
            )

            maps_link = st.text_input(
                "Google Maps-link (optioneel)",
                placeholder="Plak hier eventueel een Google Maps-link"
            )

            afstanden_tekst = st.text_input(
                "Afstanden",
                placeholder="Bijvoorbeeld 5 km, 8 km, 12 km"
            )

            beschrijving = st.text_area(
                "Beschrijving van de wandeling",
                placeholder="Vertel iets over de wandeling..."
            )

            praktische_info = st.text_area(
                "Extra praktische informatie (optioneel)",
                placeholder="Bijvoorbeeld: parking, lunchpakket, honden..."
            )

            toevoegen = st.form_submit_button(
                "➕ Wandeling toevoegen",
                use_container_width=True
            )

            if toevoegen:

                datum_geldig = datum_omzetten(datum)

                try:
                    datetime.strptime(uur, "%H:%M")
                    uur_geldig = True
                except ValueError:
                    uur_geldig = False

                afstanden = [
                    afstand.strip()
                    for afstand in afstanden_tekst.split(",")
                    if afstand.strip()
                ]

                if not naam.strip():
                    st.error("Vul een naam in.")

                elif datum_geldig is None:
                    st.error(
                        "Vul een geldige datum in, bijvoorbeeld 15/11/2026."
                    )

                elif not uur_geldig:
                    st.error(
                        "Vul een geldig uur in, bijvoorbeeld 09:00."
                    )

                elif not vertrekplaats.strip():
                    st.error("Vul een vertrekplaats in.")

                elif not afstanden:
                    st.error("Vul minstens één afstand in.")

                else:

                    nieuwe_wandeling = {
                        "id": str(uuid.uuid4()),
                        "name": naam.strip(),
                        "date": datum.strip(),
                        "time": uur.strip(),
                        "location": vertrekplaats.strip(),
                        "maps_link": (
                            maps_link.strip()
                            if maps_link.strip()
                            else maak_maps_link(vertrekplaats.strip())
                        ),
                        "distances": afstanden,
                        "group_distance": "",
                        "description": beschrijving.strip(),
                        "notes": praktische_info.strip()
                    }

                    data["walks"].append(nieuwe_wandeling)

                    save_data(data)

                    st.success("De wandeling is toegevoegd!")
                    st.rerun()

        st.divider()

        st.subheader("✏️ Bestaande wandeling aanpassen")

        if data["walks"]:

            wandelingen_beheer = sorted(
                data["walks"],
                key=wandeling_sorteren,
                reverse=True
            )

            bewerk_keuzes = unieke_wandeling_keuzes(
                wandelingen_beheer
            )

            gekozen_bewerk_label = st.selectbox(
                "Kies een wandeling",
                list(bewerk_keuzes.keys()),
                key="bewerk_wandeling_keuze"
            )

            bewerk_id = bewerk_keuzes[
                gekozen_bewerk_label
            ]

            wandeling = zoek_wandeling(bewerk_id)

            if wandeling:

                with st.form("wandeling_bewerken"):

                    nieuwe_naam = st.text_input(
                        "Naam",
                        value=wandeling.get("name", "")
                    )

                    nieuwe_datum = st.text_input(
                        "Datum",
                        value=wandeling.get("date", "")
                    )

                    nieuw_uur = st.text_input(
                        "Vertrekuur",
                        value=wandeling.get("time", "09:00")
                    )

                    nieuwe_vertrekplaats = st.text_input(
                        "Vertrekplaats",
                        value=wandeling.get("location", "")
                    )

                    nieuwe_maps_link = st.text_input(
                        "Google Maps-link",
                        value=wandeling.get("maps_link", "")
                    )

                    nieuwe_afstanden_tekst = st.text_input(
                        "Afstanden, gescheiden door komma's",
                        value=", ".join(
                            normaliseer_afstanden(
                                wandeling.get("distances", [])
                            )
                        )
                    )

                    nieuwe_beschrijving = st.text_area(
                        "Beschrijving",
                        value=wandeling.get("description", "")
                    )

                    nieuwe_info = st.text_area(
                        "Extra praktische informatie",
                        value=wandeling.get("notes", "")
                    )

                    bewaren_wandeling = st.form_submit_button(
                        "Wijzigingen bewaren"
                    )

                    if bewaren_wandeling:

                        datum_geldig = datum_omzetten(nieuwe_datum)

                        try:
                            datetime.strptime(nieuw_uur, "%H:%M")
                            uur_geldig = True
                        except ValueError:
                            uur_geldig = False

                        nieuwe_afstanden = [
                            afstand.strip()
                            for afstand in nieuwe_afstanden_tekst.split(",")
                            if afstand.strip()
                        ]

                        if not nieuwe_naam.strip():
                            st.error("Vul een naam in.")

                        elif datum_geldig is None:
                            st.error("De datum is niet geldig.")

                        elif not uur_geldig:
                            st.error("Het vertrekuur is niet geldig.")

                        elif not nieuwe_vertrekplaats.strip():
                            st.error("Vul een vertrekplaats in.")

                        elif not nieuwe_afstanden:
                            st.error("Vul minstens één afstand in.")

                        else:

                            wandeling["name"] = nieuwe_naam.strip()
                            wandeling["date"] = nieuwe_datum.strip()
                            wandeling["time"] = nieuw_uur.strip()
                            wandeling["location"] = nieuwe_vertrekplaats.strip()

                            wandeling["maps_link"] = (
                                nieuwe_maps_link.strip()
                                if nieuwe_maps_link.strip()
                                else maak_maps_link(nieuwe_vertrekplaats.strip())
                            )

                            wandeling["distances"] = nieuwe_afstanden

                            wandeling["description"] = (
                                nieuwe_beschrijving.strip()
                            )

                            wandeling["notes"] = nieuwe_info.strip()

                            if (
                                wandeling.get("group_distance")
                                not in nieuwe_afstanden
                            ):
                                wandeling["group_distance"] = ""

                            for inschrijving in data["signups"]:

                                if inschrijving.get("walk_id") == bewerk_id:

                                    inschrijving["distances"] = [
                                        afstand
                                        for afstand in normaliseer_afstanden(
                                            inschrijving.get("distances", [])
                                        )
                                        if afstand in nieuwe_afstanden
                                    ]

                            save_data(data)

                            st.success("De wandeling is aangepast.")
                            st.rerun()

            st.divider()

            st.subheader("🗑️ Wandeling verwijderen")

            verwijder_keuzes = unieke_wandeling_keuzes(
                wandelingen_beheer
            )

            te_verwijderen_label = st.selectbox(
                "Welke wandeling wil je verwijderen?",
                list(verwijder_keuzes.keys()),
                key="verwijder_wandeling_keuze"
            )

            bevestigen_verwijderen = st.checkbox(
                "Ik ben zeker dat ik deze wandeling wil verwijderen."
            )

            if st.button(
                "🗑️ Verwijder wandeling",
                disabled=not bevestigen_verwijderen
            ):

                te_verwijderen_id = verwijder_keuzes[
                    te_verwijderen_label
                ]

                data["walks"] = [
                    w
                    for w in data["walks"]
                    if w.get("id") != te_verwijderen_id
                ]

                verwijder_inschrijvingen(te_verwijderen_id)

                save_data(data)

                st.success(
                    "De wandeling en de bijhorende inschrijvingen zijn verwijderd."
                )

                st.rerun()

        else:
            st.info("Er zijn nog geen wandelingen toegevoegd.")

    # --------------------------------------------------
    # BANNER AANPASSEN
    # --------------------------------------------------

    with beheer_banner:

        st.subheader("🖼️ Bannerfoto aanpassen")

        nieuwe_banner = st.file_uploader(
            "Kies een bannerfoto",
            type=["png", "jpg", "jpeg"]
        )

        if nieuwe_banner is not None:

            if st.button("Bannerfoto bewaren"):

                extensie = nieuwe_banner.name.rsplit(".", 1)[-1].lower()

                if extensie == "jpeg":
                    extensie = "jpg"

                banner_bestand_nieuw = (
                    "kletsende_kieten_banner." + extensie
                )

                with open(banner_bestand_nieuw, "wb") as file:
                    file.write(nieuwe_banner.getbuffer())

                for bestand in [
                    "kletsende_kieten_banner.png",
                    "kletsende_kieten_banner.jpg"
                ]:

                    if (
                        bestand != banner_bestand_nieuw
                        and os.path.exists(bestand)
                    ):
                        os.remove(bestand)

                save_data(data)

                st.success("De nieuwe bannerfoto is bewaard.")
                st.rerun()

        bestaand_banner = None

        for bestand in [
            "kletsende_kieten_banner.png",
            "kletsende_kieten_banner.jpg"
        ]:

            if os.path.exists(bestand):
                bestaand_banner = bestand
                break

        if bestaand_banner:

            st.write("**Pas de positie van de foto aan.**")

            banner_x = st.slider(
                "Horizontale positie",
                min_value=0,
                max_value=100,
                value=int(data.get("banner_x", 50))
            )

            banner_y = st.slider(
                "Verticale positie",
                min_value=0,
                max_value=100,
                value=int(data.get("banner_y", 50))
            )

            if st.button("Positie van de banner bewaren"):

                data["banner_x"] = banner_x
                data["banner_y"] = banner_y

                save_data(data)

                st.success("De positie van de banner is bewaard.")
                st.rerun()

        else:
            st.info("Voeg eerst een bannerfoto toe.")

    # --------------------------------------------------
    # DEELNEMERS BEHEREN
    # --------------------------------------------------

    with beheer_deelnemers:

        st.subheader("👥 Overzicht deelnemers")

        if data["signups"]:

            for wandeling in sorted(
                data["walks"],
                key=wandeling_sorteren,
                reverse=True
            ):

                walk_id = wandeling.get("id")

                inschrijvingen = [
                    i
                    for i in data["signups"]
                    if i.get("walk_id") == walk_id
                ]

                if not inschrijvingen:
                    continue

                with st.expander(
                    f'{wandeling.get("name", "Wandeling")} - '
                    f'{wandeling.get("date", "")}'
                ):

                    for inschrijving in inschrijvingen:

                        st.write(
                            f'**{inschrijving.get("person_name", "Onbekend")}**'
                        )

                        st.write(
                            "Gaat mee: "
                            + inschrijving.get("coming", "Ja")
                        )

                        st.write(
                            "Afstand: "
                            + afstandstekst(
                                inschrijving.get("distances", [])
                            )
                        )

                        st.write(
                            "Betaald: "
                            + inschrijving.get("paid", "Nee")
                        )

                        if st.button(
                            "Verwijder deze inschrijving",
                            key=f'delete_signup_{inschrijving.get("id")}'
                        ):

                            te_verwijderen_id = inschrijving.get("id")

                            data["signups"] = [
                                i
                                for i in data["signups"]
                                if i.get("id") != te_verwijderen_id
                            ]

                            save_data(data)

                            st.success("De inschrijving is verwijderd.")
                            st.rerun()

                        st.divider()

        else:
            st.info("Er zijn nog geen deelnemers ingeschreven.")


# ==================================================
# EINDE
# ==================================================

st.divider()

st.caption(
    "🥾 De Kletsende Kieten – samen wandelen, lachen en genieten!"
)