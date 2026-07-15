import os
import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

APP_TITLE = "Fixool Site OS Light"
DB_PATH = Path(os.environ.get("FIXOOL_DB_PATH", Path(__file__).with_name("fixool_site_os.db")))
STATI_ATTIVITA = ["Da fare", "In corso", "Bloccata", "Completata", "Verificata"]
STATI_TICKET = ["Aperto", "In gestione", "Bloccante", "Risolto", "Chiuso"]
PRIORITA = ["Bassa", "Media", "Alta", "Critica"]
TIPI_TICKET = [
    "Avanzamento",
    "Blocco",
    "Richiesta decisione",
    "Richiesta materiale",
    "Richiesta altro artigiano",
    "Difetto / non conformità",
    "Extra lavoro",
    "Rischio ritardo",
    "Completamento attività",
]
FASI_STANDARD = [
    "Sopralluogo / setup",
    "Demolizioni",
    "Murature / tracce",
    "Impianto idraulico",
    "Impianto elettrico",
    "Cartongesso",
    "Massetti / sottofondi",
    "Pavimenti / rivestimenti",
    "Serramenti / porte",
    "Tinteggiatura",
    "Sanitari / rubinetterie",
    "Finiture",
    "Pulizia / consegna",
]


TEMPLATE_CANTIERI = {
    "Bagno completo": [
        ("Sopralluogo / setup", "Sopralluogo tecnico e conferma scelte bagno", "Verifica misure, layout, vincoli e conferme cliente", "Capo cantiere", "Alta", 0, 0),
        ("Demolizioni", "Demolizione bagno", "Rimozione sanitari, rivestimenti, pavimento e smaltimento", "Muratore", "Alta", 2, 0),
        ("Murature / tracce", "Apertura tracce bagno", "Tracce per punti acqua, scarichi, prese e termoarredo", "Muratore", "Alta", 4, 0),
        ("Impianto idraulico", "Predisposizione impianto idraulico", "Punti lavabo, doccia, wc, bidet e termoarredo", "Idraulico", "Alta", 6, 0),
        ("Impianto elettrico", "Predisposizione punti elettrici bagno", "Prese, interruttori, specchio, aspirazione e luci", "Elettricista", "Media", 6, 0),
        ("Murature / tracce", "Chiusura tracce", "Chiusura tracce dopo verifica impianti", "Muratore", "Alta", 8, 0),
        ("Massetti / sottofondi", "Impermeabilizzazione e sottofondo", "Preparazione fondo per posa pavimenti/rivestimenti", "Muratore", "Media", 10, 0),
        ("Pavimenti / rivestimenti", "Posa rivestimenti bagno", "Posa rivestimenti secondo scelte cliente", "Pavimentista", "Media", 14, 0),
        ("Pavimenti / rivestimenti", "Posa pavimento bagno", "Posa pavimento e fughe", "Pavimentista", "Media", 16, 0),
        ("Sanitari / rubinetterie", "Installazione sanitari e rubinetterie", "Montaggio sanitari, box/doccia e rubinetterie", "Idraulico", "Alta", 19, 0),
        ("Impianto elettrico", "Installazione placche/luci bagno", "Montaggio placche, luci e verifica elettrica", "Elettricista", "Media", 20, 0),
        ("Pulizia / consegna", "Collaudo e consegna bagno", "Verifica perdite, pulizia e consegna al cliente", "Capo cantiere", "Alta", 22, 0),
    ],
    "Cucina": [
        ("Sopralluogo / setup", "Conferma layout cucina e impianti", "Verifica progetto cucina, quote, scarichi, prese e vincoli", "Capo cantiere", "Alta", 0, 0),
        ("Demolizioni", "Demolizione/rimozione cucina esistente", "Rimozione elementi, rivestimenti e preparazione area", "Muratore", "Alta", 2, 0),
        ("Murature / tracce", "Apertura tracce cucina", "Tracce per acqua, gas/elettrico e prese dedicate", "Muratore", "Alta", 4, 0),
        ("Impianto idraulico", "Predisposizione acqua/scarichi cucina", "Punti lavello, lavastoviglie e scarichi", "Idraulico", "Alta", 6, 0),
        ("Impianto elettrico", "Predisposizione prese e punti cucina", "Prese dedicate, forno, piano, frigo, luci sottopensile", "Elettricista", "Alta", 6, 0),
        ("Murature / tracce", "Chiusura tracce cucina", "Chiusura tracce dopo verifica impianti", "Muratore", "Alta", 8, 0),
        ("Pavimenti / rivestimenti", "Posa rivestimento cucina", "Posa rivestimento/paraschizzi", "Pavimentista", "Media", 11, 0),
        ("Tinteggiatura", "Riprese e tinteggiatura cucina", "Riprese muri e tinteggiatura zona cucina", "Tinteggiatore", "Media", 13, 0),
        ("Finiture", "Supporto montaggio cucina", "Verifica quote e supporto alle installazioni", "Capo cantiere", "Media", 15, 0),
        ("Pulizia / consegna", "Collaudo impianti cucina", "Verifica elettrica/idraulica e consegna area", "Capo cantiere", "Alta", 16, 0),
    ],
    "Appartamento completo": [
        ("Sopralluogo / setup", "Setup cantiere e piano lavori", "Allestimento, protezioni, piano sicurezza e conferme operative", "Capo cantiere", "Alta", 0, 0),
        ("Demolizioni", "Demolizioni e smaltimento", "Demolizioni interne, rimozioni e smaltimento materiali", "Muratore", "Alta", 5, 0),
        ("Murature / tracce", "Tracce e opere murarie principali", "Tracce, spostamenti e predisposizioni murarie", "Muratore", "Alta", 10, 0),
        ("Impianto idraulico", "Impianto idraulico", "Predisposizione bagno/cucina e verifiche", "Idraulico", "Alta", 15, 0),
        ("Impianto elettrico", "Impianto elettrico", "Quadro, linee, prese, luci e predisposizioni", "Elettricista", "Alta", 15, 0),
        ("Cartongesso", "Cartongessi e controsoffitti", "Strutture, velette, botole e predisposizioni", "Cartongessista", "Media", 22, 0),
        ("Massetti / sottofondi", "Massetti e sottofondi", "Preparazione piani di posa", "Muratore", "Alta", 26, 0),
        ("Pavimenti / rivestimenti", "Posa pavimenti e rivestimenti", "Posa pavimentazioni e rivestimenti principali", "Pavimentista", "Alta", 35, 0),
        ("Serramenti / porte", "Installazione porte/serramenti", "Montaggi porte interne e rifiniture collegate", "Serramentista", "Media", 40, 0),
        ("Tinteggiatura", "Tinteggiatura finale", "Preparazione pareti e tinteggiatura", "Tinteggiatore", "Alta", 45, 0),
        ("Sanitari / rubinetterie", "Montaggi finali impianti", "Sanitari, placche, luci, rubinetterie e collaudi", "Idraulico/Elettricista", "Alta", 49, 0),
        ("Pulizia / consegna", "Pulizia finale e consegna", "Pulizia, punch list, verifiche e consegna cliente", "Capo cantiere", "Alta", 52, 0),
    ],
    "Ristrutturazione leggera": [
        ("Sopralluogo / setup", "Setup e protezioni", "Protezione aree, conferme operative e piano lavori", "Capo cantiere", "Alta", 0, 0),
        ("Demolizioni", "Rimozioni leggere", "Rimozioni puntuali e preparazione superfici", "Muratore", "Media", 2, 0),
        ("Impianto elettrico", "Adeguamenti elettrici", "Piccoli spostamenti prese/luci e verifiche", "Elettricista", "Media", 5, 0),
        ("Murature / tracce", "Riprese murarie", "Riprese, rasature e sistemazioni puntuali", "Muratore", "Media", 7, 0),
        ("Pavimenti / rivestimenti", "Posa/ripresa finiture", "Interventi su pavimenti/rivestimenti o battiscopa", "Pavimentista", "Media", 10, 0),
        ("Tinteggiatura", "Tinteggiatura", "Preparazione e tinteggiatura aree coinvolte", "Tinteggiatore", "Alta", 13, 0),
        ("Finiture", "Finiture e ritocchi", "Ritocchi, montaggi e verifica dettagli", "Capo cantiere", "Media", 15, 0),
        ("Pulizia / consegna", "Pulizia e consegna", "Pulizia finale e consegna cliente", "Capo cantiere", "Alta", 16, 0),
    ],
}

st.set_page_config(page_title=APP_TITLE, page_icon="🏗️", layout="wide")



def apply_ui_styles():
    """Light visual layer for the capo cantiere interface."""
    st.markdown(
        """
        <style>
        .fixool-hero {
            background: linear-gradient(135deg, #141E30 0%, #243B55 100%);
            padding: 22px 26px;
            border-radius: 18px;
            color: white;
            margin-bottom: 18px;
            box-shadow: 0 8px 28px rgba(0,0,0,0.12);
        }
        .fixool-hero h1 {margin: 0; font-size: 2.0rem; line-height: 1.15;}
        .fixool-hero p {margin: 8px 0 0 0; font-size: 1.02rem; opacity: .9;}
        .fixool-card {
            background: #ffffff;
            border: 1px solid rgba(49, 51, 63, 0.10);
            border-radius: 16px;
            padding: 16px 18px;
            margin-bottom: 12px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.05);
        }
        .fixool-card-title {font-size: .82rem; color: #6b7280; text-transform: uppercase; letter-spacing: .04em; margin-bottom: 4px;}
        .fixool-card-value {font-size: 1.9rem; font-weight: 750; color: #111827; line-height: 1.1;}
        .fixool-card-note {font-size: .9rem; color: #4b5563; margin-top: 5px;}
        .fixool-section-title {font-size: 1.25rem; font-weight: 750; margin: 12px 0 8px 0;}
        .fixool-pill {display:inline-block; padding:4px 9px; border-radius:999px; font-size:.78rem; font-weight:650; margin-right:6px;}
        .pill-red {background:#fee2e2; color:#991b1b;}
        .pill-yellow {background:#fef3c7; color:#92400e;}
        .pill-green {background:#dcfce7; color:#166534;}
        .pill-blue {background:#dbeafe; color:#1e40af;}
        .pill-gray {background:#f3f4f6; color:#374151;}
        .task-card {border-left: 6px solid #e5e7eb; padding: 14px 16px; border-radius: 14px; background:#fff; margin-bottom:10px; box-shadow:0 2px 10px rgba(0,0,0,.04);}
        .task-card.high {border-left-color:#f59e0b;}
        .task-card.critical {border-left-color:#dc2626;}
        .task-title {font-weight:750; font-size:1.02rem; color:#111827; margin-bottom:3px;}
        .task-meta {font-size:.88rem; color:#4b5563;}
        .small-muted {color:#6b7280; font-size:.9rem;}
        @media (max-width: 700px) {
            .fixool-hero {padding:18px 18px; border-radius:14px;}
            .fixool-hero h1 {font-size:1.55rem;}
            .fixool-card-value {font-size:1.55rem;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



def get_app_secret(key: str, default: str = "") -> str:
    """Read a secret from Streamlit secrets, then environment, then default."""
    try:
        value = st.secrets.get(key, None)
        if value is not None:
            return str(value)
    except Exception:
        pass
    return os.environ.get(key, default)


def require_password() -> bool:
    """Very light access gate for the MVP.

    For Streamlit Cloud set APP_PASSWORD in App secrets.
    For local tests you can use the default password: fixool2026.
    This is not a full user-management system; it is only a simple pilot gate.
    """
    app_password = get_app_secret("APP_PASSWORD", "fixool2026")
    if not app_password:
        return True

    if st.session_state.get("fixool_authenticated"):
        return True

    st.title("🏗️ Fixool Site OS Light")
    st.subheader("Accesso pilota")
    st.caption("Inserisci la password condivisa dal team Fixool.")
    with st.form("login_form"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Entra")
    if submitted:
        if password == app_password:
            st.session_state["fixool_authenticated"] = True
            st.rerun()
        else:
            st.error("Password non corretta.")
    return False


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def execute(sql, params=()):
    with connect() as conn:
        conn.execute(sql, params)
        conn.commit()


def query_df(sql, params=()):
    with connect() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def init_db():
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cantieri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                indirizzo TEXT,
                cliente TEXT,
                capo_cantiere TEXT,
                stato TEXT DEFAULT 'Attivo',
                data_inizio TEXT,
                data_fine_prevista TEXT,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS artigiani (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                ruolo TEXT,
                telefono TEXT,
                email TEXT,
                note TEXT,
                attivo INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS attivita (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cantiere_id INTEGER NOT NULL,
                fase TEXT,
                titolo TEXT NOT NULL,
                descrizione TEXT,
                assegnato_a TEXT,
                dipende_da_id INTEGER,
                stato TEXT DEFAULT 'Da fare',
                priorita TEXT DEFAULT 'Media',
                scadenza TEXT,
                percentuale INTEGER DEFAULT 0,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                closed_at TEXT,
                FOREIGN KEY(cantiere_id) REFERENCES cantieri(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cantiere_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                titolo TEXT NOT NULL,
                descrizione TEXT,
                aperto_da TEXT,
                responsabile TEXT,
                priorita TEXT DEFAULT 'Media',
                stato TEXT DEFAULT 'Aperto',
                impatto TEXT,
                scadenza TEXT,
                attivita_id INTEGER,
                foto_link TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                closed_at TEXT,
                FOREIGN KEY(cantiere_id) REFERENCES cantieri(id),
                FOREIGN KEY(attivita_id) REFERENCES attivita(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS aggiornamenti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cantiere_id INTEGER NOT NULL,
                autore TEXT,
                testo TEXT NOT NULL,
                categoria TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(cantiere_id) REFERENCES cantieri(id)
            )
            """
        )
        conn.commit()


def seed_demo_data():
    cantieri = query_df("SELECT * FROM cantieri")
    if len(cantieri) > 0:
        return
    today = date.today()
    execute(
        """INSERT INTO cantieri(nome, indirizzo, cliente, capo_cantiere, stato, data_inizio, data_fine_prevista, note)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "Demo - Appartamento Via Roma",
            "Via Roma 12, Milano",
            "Cliente Demo",
            "Marco - capo cantiere",
            "Attivo",
            str(today),
            str(today + timedelta(days=45)),
            "Cantiere demo per test del modello Fixool Site OS Light.",
        ),
    )
    execute("INSERT INTO artigiani(nome, ruolo, telefono, email, note) VALUES (?, ?, ?, ?, ?)", ("Luca Muratore", "Muratore", "", "", "Squadra opere murarie"))
    execute("INSERT INTO artigiani(nome, ruolo, telefono, email, note) VALUES (?, ?, ?, ?, ?)", ("Paolo Idraulico", "Idraulico", "", "", "Impianti bagno/cucina"))
    execute("INSERT INTO artigiani(nome, ruolo, telefono, email, note) VALUES (?, ?, ?, ?, ?)", ("Sergio Elettricista", "Elettricista", "", "", "Impianto elettrico"))
    execute("INSERT INTO artigiani(nome, ruolo, telefono, email, note) VALUES (?, ?, ?, ?, ?)", ("Andrea Pavimentista", "Pavimentista", "", "", "Pavimenti e rivestimenti"))
    cantiere_id = int(query_df("SELECT id FROM cantieri LIMIT 1").iloc[0]["id"])
    attivita_demo = [
        ("Demolizioni", "Completare demolizione bagno", "Rimuovere sanitari, rivestimenti e pavimento bagno", "Luca Muratore", None, "In corso", "Alta", today + timedelta(days=2), 60),
        ("Murature / tracce", "Aprire tracce impianti bagno", "Tracce per idraulico ed elettricista", "Luca Muratore", 1, "Da fare", "Alta", today + timedelta(days=4), 0),
        ("Impianto idraulico", "Predisporre punti acqua bagno", "Punti lavabo, doccia, wc e termoarredo", "Paolo Idraulico", 2, "Da fare", "Alta", today + timedelta(days=7), 0),
        ("Impianto elettrico", "Verificare punti luce zona giorno", "Confermare posizione prese e interruttori", "Sergio Elettricista", None, "Da fare", "Media", today + timedelta(days=5), 0),
        ("Pavimenti / rivestimenti", "Posa rivestimenti bagno", "Partire solo dopo chiusura impianti e massetto asciutto", "Andrea Pavimentista", 3, "Da fare", "Media", today + timedelta(days=15), 0),
    ]
    for fase, titolo, desc, assegnato, dip, stato, prio, scad, pct in attivita_demo:
        execute(
            """INSERT INTO attivita(cantiere_id, fase, titolo, descrizione, assegnato_a, dipende_da_id, stato, priorita, scadenza, percentuale)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (cantiere_id, fase, titolo, desc, assegnato, dip, stato, prio, str(scad), pct),
        )
    execute(
        """INSERT INTO ticket(cantiere_id, tipo, titolo, descrizione, aperto_da, responsabile, priorita, stato, impatto, scadenza)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            cantiere_id,
            "Richiesta decisione",
            "Confermare posizione termoarredo bagno",
            "Serve conferma prima di chiudere le tracce e procedere con predisposizione idraulica.",
            "Paolo Idraulico",
            "Capo cantiere",
            "Alta",
            "Aperto",
            "Rischio slittamento pavimentista di 1 giorno",
            str(today + timedelta(days=1)),
        ),
    )


def get_cantieri_options():
    df = query_df("SELECT id, nome FROM cantieri ORDER BY created_at DESC")
    return {f"{row['id']} - {row['nome']}": int(row["id"]) for _, row in df.iterrows()}


def get_artigiani_names(include_empty=True):
    df = query_df("SELECT nome FROM artigiani WHERE attivo = 1 ORDER BY nome")
    names = df["nome"].tolist() if len(df) else []
    return ([""] if include_empty else []) + names


def get_attivita_options(cantiere_id):
    df = query_df("SELECT id, titolo FROM attivita WHERE cantiere_id = ? ORDER BY id DESC", (cantiere_id,))
    return {"Nessuna": None, **{f"{int(row['id'])} - {row['titolo']}": int(row["id"]) for _, row in df.iterrows()}}


def suggest_from_message(text: str):
    raw = (text or "").lower()
    tipo = "Avanzamento"
    priorita = "Media"
    stato = "Aperto"
    impatto = ""
    if any(k in raw for k in ["blocc", "non posso", "fermo", "manca", "impossibile", "non riesco"]):
        tipo = "Blocco"
        priorita = "Alta"
        stato = "Bloccante"
        impatto = "Possibile ritardo se non gestito entro 24 ore."
    if any(k in raw for k in ["urgente", "subito", "oggi", "domani mattina"]):
        priorita = "Critica" if tipo == "Blocco" else "Alta"
    if any(k in raw for k in ["materiale", "piastrel", "sanitari", "rubinet", "massetto", "porta", "fornitura"]):
        tipo = "Richiesta materiale" if tipo != "Blocco" else tipo
        impatto = impatto or "Verificare disponibilità materiale per evitare fermo cantiere."
    if any(k in raw for k in ["conferma", "decidere", "scelta", "cliente", "autorizzazione"]):
        tipo = "Richiesta decisione" if tipo != "Blocco" else tipo
        impatto = impatto or "Serve decisione per proseguire senza rilavorazioni."
    if any(k in raw for k in ["finito", "completato", "chiuso", "terminato"]):
        tipo = "Completamento attività"
        priorita = "Media"
        stato = "Aperto"
        impatto = "Verificare e aggiornare avanzamento attività."
    title = text.strip().split(".")[0][:80] if text.strip() else "Nuova segnalazione cantiere"
    return tipo, priorita, stato, impatto, title


def update_closed_at(table, row_id, status):
    closed_status = {
        "attivita": ["Completata", "Verificata"],
        "ticket": ["Risolto", "Chiuso"],
    }
    if status in closed_status.get(table, []):
        execute(f"UPDATE {table} SET closed_at = COALESCE(closed_at, CURRENT_TIMESTAMP) WHERE id = ?", (row_id,))
    else:
        execute(f"UPDATE {table} SET closed_at = NULL WHERE id = ?", (row_id,))


def kpi_cards(cantiere_id=None):
    params = () if cantiere_id is None else (cantiere_id,)
    where = "" if cantiere_id is None else "WHERE cantiere_id = ?"
    att = query_df(f"SELECT * FROM attivita {where}", params)
    tic = query_df(f"SELECT * FROM ticket {where}", params)
    total_att = len(att)
    completate = int(att["stato"].isin(["Completata", "Verificata"]).sum()) if total_att else 0
    bloccate = int(att["stato"].eq("Bloccata").sum()) if total_att else 0
    ticket_aperti = int((~tic["stato"].isin(["Risolto", "Chiuso"])).sum()) if len(tic) else 0
    ticket_bloccanti = int(tic["stato"].eq("Bloccante").sum()) if len(tic) else 0
    overdue = 0
    if total_att:
        scad = pd.to_datetime(att["scadenza"], errors="coerce")
        overdue = int(((scad.dt.date < date.today()) & ~att["stato"].isin(["Completata", "Verificata"])).sum())
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Attività totali", total_att)
    col2.metric("Completate", completate, f"{round(completate / total_att * 100, 0) if total_att else 0}%")
    col3.metric("Attività bloccate", bloccate)
    col4.metric("Ticket aperti", ticket_aperti)
    col5.metric("Scadute", overdue)
    if ticket_bloccanti:
        st.warning(f"Attenzione: ci sono {ticket_bloccanti} ticket bloccanti aperti.")



def render_attivita_table(att_df, title=None):
    """Render activities with a graphical progress bar."""
    if title:
        st.subheader(title)
    if att_df is None or len(att_df) == 0:
        st.info("Nessuna attività presente per il filtro selezionato.")
        return

    display_df = att_df.copy()
    if "percentuale" in display_df.columns:
        display_df["percentuale"] = pd.to_numeric(display_df["percentuale"], errors="coerce").fillna(0).clip(0, 100).astype(int)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "percentuale": st.column_config.ProgressColumn(
                "Avanzamento",
                help="Percentuale di avanzamento del task",
                min_value=0,
                max_value=100,
                format="%d%%",
            )
        },
    )


def progress_from_status(stato, percentuale):
    """Keep progress coherent with terminal statuses while preserving manual control."""
    try:
        pct = int(percentuale or 0)
    except Exception:
        pct = 0
    pct = max(0, min(100, pct))
    if stato in ["Completata", "Verificata"]:
        return 100
    return pct


def compute_cantiere_progress(cantiere_id):
    """Calculate overall site progress as the average progress of its activities.

    The MVP uses a simple and transparent rule: each task has the same weight.
    Completed or verified tasks are forced to 100%; all other tasks use the
    manual percentage set by the capo cantiere.
    """
    att = query_df("SELECT stato, percentuale FROM attivita WHERE cantiere_id = ?", (cantiere_id,))
    if att is None or len(att) == 0:
        return 0, 0, 0, 0, 0
    pct_values = []
    for _, row in att.iterrows():
        pct_values.append(progress_from_status(row.get("stato"), row.get("percentuale")))
    overall = int(round(sum(pct_values) / len(pct_values))) if pct_values else 0
    completate = int(att["stato"].isin(["Completata", "Verificata"]).sum())
    bloccate = int(att["stato"].eq("Bloccata").sum())
    in_corso = int(att["stato"].eq("In corso").sum())
    return overall, len(att), completate, in_corso, bloccate


def cantiere_progress_label(percentuale):
    try:
        pct = int(percentuale or 0)
    except Exception:
        pct = 0
    if pct >= 100:
        return "Completato"
    if pct >= 80:
        return "Fase finale"
    if pct >= 50:
        return "Avanzamento intermedio"
    if pct >= 20:
        return "Avviato"
    return "In partenza"


def text_progress_bar(percentuale, blocks=10):
    """Copyable progress bar for WhatsApp/email/client reports."""
    try:
        pct = max(0, min(100, int(percentuale or 0)))
    except Exception:
        pct = 0
    filled = round(pct / 100 * blocks)
    return "█" * filled + "░" * (blocks - filled)


def render_cantiere_progress(cantiere_id, title="Avanzamento generale cantiere"):
    """Render a graphical overall progress bar for a single site."""
    pct, total, completate, in_corso, bloccate = compute_cantiere_progress(cantiere_id)
    st.subheader(title)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avanzamento", f"{pct}%")
    col2.metric("Attività totali", total)
    col3.metric("Completate", completate)
    col4.metric("Bloccate", bloccate)
    st.progress(pct)
    st.caption(f"Stato sintetico: {cantiere_progress_label(pct)}. Calcolo basato sulla media delle percentuali di avanzamento delle attività del cantiere.")
    if bloccate:
        st.warning(f"Ci sono {bloccate} attività bloccate: verificare impatto su tempi e sequenza lavori.")
    return pct, total, completate, in_corso, bloccate


def get_cantieri_progress_df(cantiere_id=None):
    """Return progress summary for one or all sites, suitable for a dataframe with ProgressColumn."""
    where = "" if cantiere_id is None else "WHERE id = ?"
    params = () if cantiere_id is None else (cantiere_id,)
    cantieri = query_df(f"SELECT id, nome, cliente, capo_cantiere, stato FROM cantieri {where} ORDER BY created_at DESC", params)
    rows = []
    for _, c in cantieri.iterrows():
        pct, total, completate, in_corso, bloccate = compute_cantiere_progress(int(c["id"]))
        rows.append({
            "id": int(c["id"]),
            "cantiere": c["nome"],
            "cliente": c.get("cliente") or "",
            "capo_cantiere": c.get("capo_cantiere") or "",
            "stato": c.get("stato") or "",
            "avanzamento": pct,
            "attività_totali": total,
            "completate": completate,
            "in_corso": in_corso,
            "bloccate": bloccate,
            "sintesi": cantiere_progress_label(pct),
        })
    return pd.DataFrame(rows)



def assess_cantiere_risk(cantiere_id):
    """Compute an operational risk level for the site.

    Transparent scoring for the MVP:
    - critical open tickets weigh more than high priority
    - blocking tickets/activities and overdue activities increase risk
    - open customer decisions/material requests increase coordination risk
    """
    att = query_df("SELECT * FROM attivita WHERE cantiere_id = ?", (cantiere_id,))
    tic = query_df("SELECT * FROM ticket WHERE cantiere_id = ?", (cantiere_id,))
    open_tic = tic[~tic["stato"].isin(["Risolto", "Chiuso"])] if len(tic) else pd.DataFrame()
    overdue = 0
    if len(att):
        scad = pd.to_datetime(att["scadenza"], errors="coerce")
        overdue = int(((scad.dt.date < date.today()) & ~att["stato"].isin(["Completata", "Verificata"])).sum())
    att_bloccate = int(att["stato"].eq("Bloccata").sum()) if len(att) else 0
    ticket_bloccanti = int(open_tic["stato"].eq("Bloccante").sum()) if len(open_tic) else 0
    critical = int(open_tic["priorita"].eq("Critica").sum()) if len(open_tic) else 0
    high = int(open_tic["priorita"].eq("Alta").sum()) if len(open_tic) else 0
    decisioni = int(open_tic["tipo"].isin(["Richiesta decisione", "Richiesta materiale"]).sum()) if len(open_tic) else 0
    risk_tickets = int(open_tic["tipo"].isin(["Blocco", "Rischio ritardo"]).sum()) if len(open_tic) else 0
    score = (critical * 4) + (ticket_bloccanti * 3) + (att_bloccate * 3) + (overdue * 2) + (risk_tickets * 2) + high + decisioni
    if score >= 9:
        level = "Rosso"
        sintesi = "Rischio operativo alto"
        azione = "Serve intervento immediato del capo cantiere/Fixool sui blocchi aperti."
    elif score >= 4:
        level = "Giallo"
        sintesi = "Attenzione operativa"
        azione = "Monitorare ticket, decisioni e attività critiche entro la giornata."
    else:
        level = "Verde"
        sintesi = "Cantiere sotto controllo"
        azione = "Continuare aggiornamento attività e report giornaliero."
    motivi = []
    if critical:
        motivi.append(f"{critical} ticket critici")
    if ticket_bloccanti:
        motivi.append(f"{ticket_bloccanti} ticket bloccanti")
    if att_bloccate:
        motivi.append(f"{att_bloccate} attività bloccate")
    if overdue:
        motivi.append(f"{overdue} attività scadute")
    if decisioni:
        motivi.append(f"{decisioni} decisioni/materiali da confermare")
    if not motivi:
        motivi.append("nessun blocco rilevante aperto")
    return {
        "livello": level,
        "score": score,
        "sintesi": sintesi,
        "azione": azione,
        "motivi": motivi,
        "critical": critical,
        "ticket_bloccanti": ticket_bloccanti,
        "attivita_bloccate": att_bloccate,
        "scadute": overdue,
        "decisioni": decisioni,
    }


def render_cantiere_risk(cantiere_id, title="Rischio operativo cantiere"):
    risk = assess_cantiere_risk(cantiere_id)
    st.subheader(title)
    col1, col2, col3 = st.columns(3)
    col1.metric("Semaforo", risk["livello"])
    col2.metric("Score rischio", risk["score"])
    col3.metric("Decisioni/materiali", risk["decisioni"])
    msg = f"{risk['sintesi']} — {', '.join(risk['motivi'])}. {risk['azione']}"
    if risk["livello"] == "Rosso":
        st.error(msg)
    elif risk["livello"] == "Giallo":
        st.warning(msg)
    else:
        st.success(msg)
    return risk


def get_next_activities(cantiere_id, max_items=5):
    return query_df(
        """
        SELECT titolo, assegnato_a, stato, scadenza, percentuale
        FROM attivita
        WHERE cantiere_id = ? AND stato NOT IN ('Completata','Verificata')
        ORDER BY scadenza, id
        LIMIT ?
        """,
        (cantiere_id, max_items),
    )


def insert_template_activities(cantiere_id, template_name, start_date):
    tasks = TEMPLATE_CANTIERI.get(template_name, [])
    inserted = 0
    for fase, titolo, desc, ruolo, prio, offset_days, pct in tasks:
        execute(
            """INSERT INTO attivita(cantiere_id, fase, titolo, descrizione, assegnato_a, dipende_da_id, stato, priorita, scadenza, percentuale, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                cantiere_id,
                fase,
                titolo,
                desc,
                ruolo,
                None,
                "Da fare",
                prio,
                str(start_date + timedelta(days=int(offset_days))),
                int(pct),
                f"Creato da template: {template_name}",
            ),
        )
        inserted += 1
    return inserted


def page_template_cantiere():
    st.header("Template progetto / cantiere")
    st.caption("Crea rapidamente le attività standard di un cantiere Fixool. Serve a rendere il metodo replicabile e ridurre dimenticanze operative.")
    cantieri_map = get_cantieri_options()
    if not cantieri_map:
        st.info("Crea prima un progetto nella sezione Progetti.")
        return
    selected = st.selectbox("Cantiere", list(cantieri_map.keys()), key="template_cantiere")
    cantiere_id = cantieri_map[selected]
    template_name = st.selectbox("Template da applicare", list(TEMPLATE_CANTIERI.keys()))
    start_date = st.date_input("Data partenza attività template", value=date.today())
    preview = pd.DataFrame(
        TEMPLATE_CANTIERI[template_name],
        columns=["fase", "titolo", "descrizione", "ruolo_suggerito", "priorità", "giorno", "avanzamento"],
    )
    st.subheader("Anteprima attività che verranno create")
    st.dataframe(preview, use_container_width=True, hide_index=True)
    st.info("Le attività verranno aggiunte al cantiere selezionato. Le dipendenze restano da rifinire manualmente nella sezione Attività.")
    if st.button("Crea attività da template", type="primary"):
        inserted = insert_template_activities(cantiere_id, template_name, start_date)
        st.success(f"Create {inserted} attività dal template '{template_name}'.")
        st.rerun()

def page_dashboard():
    st.header("Dashboard operativa")
    cantieri_map = get_cantieri_options()
    all_option = "Tutti i cantieri"
    options = [all_option] + list(cantieri_map.keys())
    selected = st.selectbox("Vista", options)
    cantiere_id = None if selected == all_option else cantieri_map[selected]
    kpi_cards(cantiere_id)

    if cantiere_id is not None:
        render_cantiere_progress(cantiere_id)
        render_cantiere_risk(cantiere_id)
    else:
        st.subheader("Avanzamento generale per cantiere")
        progress_df = get_cantieri_progress_df()
        if len(progress_df):
            st.dataframe(
                progress_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "avanzamento": st.column_config.ProgressColumn(
                        "Avanzamento",
                        help="Avanzamento medio delle attività del cantiere",
                        min_value=0,
                        max_value=100,
                        format="%d%%",
                    )
                },
            )
        else:
            st.info("Non ci sono ancora cantieri inseriti.")

    st.subheader("Ticket aperti / bloccanti")
    params = () if cantiere_id is None else (cantiere_id,)
    where = "WHERE t.stato NOT IN ('Risolto','Chiuso')" if cantiere_id is None else "WHERE t.cantiere_id = ? AND t.stato NOT IN ('Risolto','Chiuso')"
    tickets = query_df(
        f"""
        SELECT t.id, c.nome AS cantiere, t.tipo, t.titolo, t.responsabile, t.priorita, t.stato, t.scadenza, t.impatto
        FROM ticket t
        JOIN cantieri c ON c.id = t.cantiere_id
        {where}
        ORDER BY CASE t.priorita WHEN 'Critica' THEN 1 WHEN 'Alta' THEN 2 WHEN 'Media' THEN 3 ELSE 4 END, t.scadenza
        """,
        params,
    )
    st.dataframe(tickets, use_container_width=True, hide_index=True)

    st.subheader("Attività per stato")
    params = () if cantiere_id is None else (cantiere_id,)
    where = "" if cantiere_id is None else "WHERE cantiere_id = ?"
    att = query_df(f"SELECT stato, COUNT(*) AS numero FROM attivita {where} GROUP BY stato", params)
    if len(att):
        st.bar_chart(att.set_index("stato"))
    else:
        st.info("Non ci sono ancora attività inserite.")

    att_where = "" if cantiere_id is None else "WHERE a.cantiere_id = ?"
    att_progress = query_df(
        f"""
        SELECT a.id, c.nome AS cantiere, a.fase, a.titolo, a.assegnato_a, a.stato, a.priorita, a.scadenza, a.percentuale
        FROM attivita a
        JOIN cantieri c ON c.id = a.cantiere_id
        {att_where}
        ORDER BY a.scadenza, a.id
        """,
        params,
    )
    render_attivita_table(att_progress, "Avanzamento attività")

    st.subheader("Prossime attività in scadenza")
    prossime_where = "" if cantiere_id is None else "AND a.cantiere_id = ?"
    prossime = query_df(
        f"""
        SELECT a.id, c.nome AS cantiere, a.fase, a.titolo, a.assegnato_a, a.stato, a.priorita, a.scadenza, a.percentuale
        FROM attivita a JOIN cantieri c ON c.id = a.cantiere_id
        WHERE a.stato NOT IN ('Completata','Verificata') {prossime_where}
        ORDER BY a.scadenza LIMIT 20
        """,
        params,
    )
    render_attivita_table(prossime)


def page_cantieri():
    st.header("Anagrafica progetti / cantieri")
    with st.expander("Crea nuovo cantiere", expanded=True):
        with st.form("new_cantiere"):
            col1, col2 = st.columns(2)
            nome = col1.text_input("Nome cantiere *", placeholder="Es. Appartamento Via Garibaldi")
            cliente = col2.text_input("Cliente")
            indirizzo = col1.text_input("Indirizzo")
            capo = col2.text_input("Capo cantiere")
            data_inizio = col1.date_input("Data inizio", value=date.today())
            data_fine = col2.date_input("Data fine prevista", value=date.today() + timedelta(days=45))
            stato = col1.selectbox("Stato", ["Attivo", "In pausa", "Completato", "Archiviato"])
            note = st.text_area("Note")
            submitted = st.form_submit_button("Salva cantiere")
        if submitted:
            if not nome.strip():
                st.error("Inserisci almeno il nome del cantiere.")
            else:
                execute(
                    """INSERT INTO cantieri(nome, indirizzo, cliente, capo_cantiere, stato, data_inizio, data_fine_prevista, note)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (nome.strip(), indirizzo, cliente, capo, stato, str(data_inizio), str(data_fine), note),
                )
                st.success("Cantiere creato.")
                st.rerun()

    st.subheader("Elenco progetti / cantieri")
    df = query_df("SELECT id, nome, cliente, indirizzo, capo_cantiere, stato, data_inizio, data_fine_prevista FROM cantieri ORDER BY created_at DESC")
    st.dataframe(df, use_container_width=True, hide_index=True)


def page_artigiani():
    st.header("Artigiani e squadre")
    with st.expander("Aggiungi artigiano / squadra", expanded=True):
        with st.form("new_artigiano"):
            col1, col2 = st.columns(2)
            nome = col1.text_input("Nome *")
            ruolo = col2.text_input("Ruolo", placeholder="Muratore, idraulico, elettricista...")
            telefono = col1.text_input("Telefono")
            email = col2.text_input("Email")
            note = st.text_area("Note")
            submitted = st.form_submit_button("Salva artigiano")
        if submitted:
            if not nome.strip():
                st.error("Inserisci almeno il nome.")
            else:
                execute(
                    "INSERT INTO artigiani(nome, ruolo, telefono, email, note) VALUES (?, ?, ?, ?, ?)",
                    (nome.strip(), ruolo, telefono, email, note),
                )
                st.success("Artigiano creato.")
                st.rerun()
    df = query_df("SELECT id, nome, ruolo, telefono, email, note FROM artigiani WHERE attivo = 1 ORDER BY nome")
    st.dataframe(df, use_container_width=True, hide_index=True)


def page_attivita():
    st.header("Attività di progetto / cantiere")
    cantieri_map = get_cantieri_options()
    if not cantieri_map:
        st.info("Crea prima un progetto/cantiere.")
        return
    selected = st.selectbox("Cantiere", list(cantieri_map.keys()))
    cantiere_id = cantieri_map[selected]
    kpi_cards(cantiere_id)
    render_cantiere_progress(cantiere_id)

    tab1, tab2 = st.tabs(["Nuova attività", "Aggiorna / monitora attività"])
    with tab1:
        with st.form("new_attivita"):
            col1, col2 = st.columns(2)
            fase = col1.selectbox("Fase", FASI_STANDARD)
            titolo = col2.text_input("Titolo attività *")
            descrizione = st.text_area("Descrizione")
            col3, col4 = st.columns(2)
            assegnato = col3.selectbox("Assegnata a", get_artigiani_names())
            dip_options = get_attivita_options(cantiere_id)
            dip_label = col4.selectbox("Dipende da", list(dip_options.keys()))
            col5, col6, col7 = st.columns(3)
            stato = col5.selectbox("Stato", STATI_ATTIVITA)
            priorita = col6.selectbox("Priorità", PRIORITA, index=1)
            scadenza = col7.date_input("Scadenza", value=date.today() + timedelta(days=7))
            percentuale = st.slider("Avanzamento %", 0, 100, 0, step=5)
            note = st.text_area("Note operative")
            submitted = st.form_submit_button("Salva attività")
        if submitted:
            if not titolo.strip():
                st.error("Inserisci il titolo dell'attività.")
            else:
                percentuale_finale = progress_from_status(stato, percentuale)
                execute(
                    """INSERT INTO attivita(cantiere_id, fase, titolo, descrizione, assegnato_a, dipende_da_id, stato, priorita, scadenza, percentuale, note)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (cantiere_id, fase, titolo.strip(), descrizione, assegnato, dip_options[dip_label], stato, priorita, str(scadenza), percentuale_finale, note),
                )
                st.success("Attività creata.")
                st.rerun()

    with tab2:
        att_df = query_df(
            "SELECT id, fase, titolo, assegnato_a, stato, priorita, scadenza, percentuale, note FROM attivita WHERE cantiere_id = ? ORDER BY scadenza, id",
            (cantiere_id,),
        )
        render_attivita_table(att_df)
        if len(att_df):
            act_label = st.selectbox("Seleziona attività da aggiornare", [f"{row.id} - {row.titolo}" for row in att_df.itertuples()])
            act_id = int(act_label.split(" - ")[0])
            row = query_df("SELECT * FROM attivita WHERE id = ?", (act_id,)).iloc[0]
            pct_attuale = max(0, min(100, int(row["percentuale"] or 0)))
            st.markdown("**Avanzamento grafico del task selezionato**")
            st.progress(pct_attuale)
            st.caption(f"Avanzamento attuale: {pct_attuale}%")
            with st.form("update_attivita"):
                col1, col2, col3 = st.columns(3)
                nuovo_stato = col1.selectbox("Nuovo stato", STATI_ATTIVITA, index=STATI_ATTIVITA.index(row["stato"]) if row["stato"] in STATI_ATTIVITA else 0)
                nuova_prio = col2.selectbox("Priorità", PRIORITA, index=PRIORITA.index(row["priorita"]) if row["priorita"] in PRIORITA else 1)
                nuova_pct = col3.slider("Avanzamento %", 0, 100, int(row["percentuale"] or 0), step=5)
                nuove_note = st.text_area("Note", value=row["note"] or "")
                submitted = st.form_submit_button("Aggiorna attività")
            if submitted:
                nuova_pct_finale = progress_from_status(nuovo_stato, nuova_pct)
                execute("UPDATE attivita SET stato = ?, priorita = ?, percentuale = ?, note = ? WHERE id = ?", (nuovo_stato, nuova_prio, nuova_pct_finale, nuove_note, act_id))
                update_closed_at("attivita", act_id, nuovo_stato)
                st.success("Attività aggiornata.")
                st.rerun()


def page_ticket():
    st.header("Ticket, blocchi e richieste")
    cantieri_map = get_cantieri_options()
    if not cantieri_map:
        st.info("Crea prima un progetto/cantiere.")
        return
    selected = st.selectbox("Cantiere", list(cantieri_map.keys()), key="ticket_cantiere")
    cantiere_id = cantieri_map[selected]

    tab1, tab2, tab3 = st.tabs(["Assistente smistamento", "Nuovo ticket manuale", "Gestione ticket"])

    with tab1:
        st.caption("Incolla un messaggio ricevuto da WhatsApp o dal campo. L'assistente propone tipo, priorità e impatto. È una logica leggera, pensata per il primo test; in seguito può diventare un vero agente AI.")
        autore = st.selectbox("Chi ha scritto", get_artigiani_names(), key="autore_assistente")
        testo = st.text_area("Messaggio ricevuto", height=120, placeholder="Es. Ho finito le tracce, ma manca conferma posizione termoarredo. Domani non posso chiudere.")
        if st.button("Analizza messaggio"):
            tipo, priorita, stato, impatto, title = suggest_from_message(testo)
            st.session_state["suggested_ticket"] = {
                "tipo": tipo,
                "priorita": priorita,
                "stato": stato,
                "impatto": impatto,
                "titolo": title,
                "descrizione": testo,
                "autore": autore,
            }
        suggested = st.session_state.get("suggested_ticket")
        if suggested:
            st.success("Proposta ticket generata.")
            col1, col2, col3 = st.columns(3)
            col1.info(f"Tipo: {suggested['tipo']}")
            col2.info(f"Priorità: {suggested['priorita']}")
            col3.info(f"Stato: {suggested['stato']}")
            with st.form("confirm_suggested"):
                titolo = st.text_input("Titolo", value=suggested["titolo"])
                descrizione = st.text_area("Descrizione", value=suggested["descrizione"])
                col4, col5 = st.columns(2)
                responsabile = col4.selectbox("Responsabile", ["Capo cantiere", "Fixool", "Cliente"] + get_artigiani_names(include_empty=False))
                scadenza = col5.date_input("Scadenza", value=date.today() + timedelta(days=1))
                impatto = st.text_area("Impatto", value=suggested["impatto"])
                submitted = st.form_submit_button("Crea ticket da messaggio")
            if submitted:
                execute(
                    """INSERT INTO aggiornamenti(cantiere_id, autore, testo, categoria) VALUES (?, ?, ?, ?)""",
                    (cantiere_id, suggested["autore"], suggested["descrizione"], suggested["tipo"]),
                )
                execute(
                    """INSERT INTO ticket(cantiere_id, tipo, titolo, descrizione, aperto_da, responsabile, priorita, stato, impatto, scadenza)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (cantiere_id, suggested["tipo"], titolo, descrizione, suggested["autore"], responsabile, suggested["priorita"], suggested["stato"], impatto, str(scadenza)),
                )
                st.session_state.pop("suggested_ticket", None)
                st.success("Ticket creato.")
                st.rerun()

    with tab2:
        with st.form("new_ticket"):
            col1, col2 = st.columns(2)
            tipo = col1.selectbox("Tipo", TIPI_TICKET)
            titolo = col2.text_input("Titolo ticket *")
            descrizione = st.text_area("Descrizione")
            col3, col4 = st.columns(2)
            aperto_da = col3.selectbox("Aperto da", get_artigiani_names())
            responsabile = col4.selectbox("Responsabile", ["Capo cantiere", "Fixool", "Cliente"] + get_artigiani_names(include_empty=False))
            col5, col6, col7 = st.columns(3)
            priorita = col5.selectbox("Priorità", PRIORITA, index=1)
            stato = col6.selectbox("Stato", STATI_TICKET)
            scadenza = col7.date_input("Scadenza", value=date.today() + timedelta(days=1))
            att_options = get_attivita_options(cantiere_id)
            att_label = st.selectbox("Collega ad attività", list(att_options.keys()))
            impatto = st.text_area("Impatto su tempi / costi / qualità")
            foto_link = st.text_input("Link foto/documento", placeholder="Opzionale: link a foto, Drive, cartella cantiere...")
            submitted = st.form_submit_button("Salva ticket")
        if submitted:
            if not titolo.strip():
                st.error("Inserisci il titolo del ticket.")
            else:
                execute(
                    """INSERT INTO ticket(cantiere_id, tipo, titolo, descrizione, aperto_da, responsabile, priorita, stato, impatto, scadenza, attivita_id, foto_link)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (cantiere_id, tipo, titolo.strip(), descrizione, aperto_da, responsabile, priorita, stato, impatto, str(scadenza), att_options[att_label], foto_link),
                )
                st.success("Ticket creato.")
                st.rerun()

    with tab3:
        tic_df = query_df(
            """
            SELECT id, tipo, titolo, aperto_da, responsabile, priorita, stato, scadenza, impatto
            FROM ticket WHERE cantiere_id = ?
            ORDER BY CASE priorita WHEN 'Critica' THEN 1 WHEN 'Alta' THEN 2 WHEN 'Media' THEN 3 ELSE 4 END, scadenza
            """,
            (cantiere_id,),
        )
        st.dataframe(tic_df, use_container_width=True, hide_index=True)
        if len(tic_df):
            ticket_label = st.selectbox("Seleziona ticket da aggiornare", [f"{row.id} - {row.titolo}" for row in tic_df.itertuples()])
            ticket_id = int(ticket_label.split(" - ")[0])
            row = query_df("SELECT * FROM ticket WHERE id = ?", (ticket_id,)).iloc[0]
            with st.form("update_ticket"):
                col1, col2, col3 = st.columns(3)
                nuovo_stato = col1.selectbox("Nuovo stato", STATI_TICKET, index=STATI_TICKET.index(row["stato"]) if row["stato"] in STATI_TICKET else 0)
                nuova_prio = col2.selectbox("Priorità", PRIORITA, index=PRIORITA.index(row["priorita"]) if row["priorita"] in PRIORITA else 1)
                nuovo_resp = col3.text_input("Responsabile", value=row["responsabile"] or "")
                nuovo_impatto = st.text_area("Impatto / note chiusura", value=row["impatto"] or "")
                submitted = st.form_submit_button("Aggiorna ticket")
            if submitted:
                execute("UPDATE ticket SET stato = ?, priorita = ?, responsabile = ?, impatto = ? WHERE id = ?", (nuovo_stato, nuova_prio, nuovo_resp, nuovo_impatto, ticket_id))
                update_closed_at("ticket", ticket_id, nuovo_stato)
                st.success("Ticket aggiornato.")
                st.rerun()


def make_daily_report(cantiere_id):
    cantiere = query_df("SELECT * FROM cantieri WHERE id = ?", (cantiere_id,)).iloc[0]
    att = query_df("SELECT * FROM attivita WHERE cantiere_id = ? ORDER BY scadenza", (cantiere_id,))
    tic = query_df("SELECT * FROM ticket WHERE cantiere_id = ? ORDER BY priorita, scadenza", (cantiere_id,))
    completate = att[att["stato"].isin(["Completata", "Verificata"])] if len(att) else pd.DataFrame()
    in_corso = att[att["stato"].eq("In corso")] if len(att) else pd.DataFrame()
    bloccate = att[att["stato"].eq("Bloccata")] if len(att) else pd.DataFrame()
    ticket_aperti = tic[~tic["stato"].isin(["Risolto", "Chiuso"])] if len(tic) else pd.DataFrame()
    ticket_blocchi = ticket_aperti[ticket_aperti["tipo"].isin(["Blocco", "Richiesta decisione", "Richiesta materiale", "Rischio ritardo"])] if len(ticket_aperti) else pd.DataFrame()
    avanzamento, totale_attivita, totale_completate, totale_in_corso, totale_bloccate = compute_cantiere_progress(cantiere_id)
    barra_avanzamento = text_progress_bar(avanzamento)
    stato_sintetico = cantiere_progress_label(avanzamento)
    rischio = assess_cantiere_risk(cantiere_id)
    prossime = get_next_activities(cantiere_id, 5)

    def bullet(df, col="titolo", max_items=6):
        if df is None or len(df) == 0:
            return "- Nessuno"
        lines = []
        for _, row in df.head(max_items).iterrows():
            if "percentuale" in df.columns:
                try:
                    pct = int(row.get("percentuale") or 0)
                    lines.append(f"- {row[col]} ({pct}%)")
                except Exception:
                    lines.append(f"- {row[col]}")
            else:
                lines.append(f"- {row[col]}")
        return "\n".join(lines)


    report = f"""REPORT GIORNALIERO FIXOOL - {date.today().strftime('%d/%m/%Y')}

Cantiere: {cantiere['nome']}
Cliente: {cantiere['cliente'] or '-'}
Capo cantiere: {cantiere['capo_cantiere'] or '-'}

AVANZAMENTO GENERALE CANTIERE: {avanzamento}%
{barra_avanzamento} {avanzamento}% - {stato_sintetico}
Attività totali: {totale_attivita} | Completate: {totale_completate} | In corso: {totale_in_corso} | Bloccate: {totale_bloccate}

RISCHIO OPERATIVO: {rischio['livello']} - {rischio['sintesi']}
Motivi: {', '.join(rischio['motivi'])}
Azione suggerita: {rischio['azione']}

1) ATTIVITÀ COMPLETATE / VERIFICATE
{bullet(completate)}

2) ATTIVITÀ IN CORSO
{bullet(in_corso)}

3) ATTIVITÀ BLOCCATE
{bullet(bloccate)}

4) TICKET APERTI CRITICI / OPERATIVI
{bullet(ticket_blocchi)}

5) DECISIONI / AZIONI RICHIESTE
{bullet(ticket_aperti[ticket_aperti['tipo'].eq('Richiesta decisione')] if len(ticket_aperti) else pd.DataFrame())}

6) RISCHIO TEMPI
- Ticket aperti: {len(ticket_aperti)}
- Blocchi o rischi aperti: {len(ticket_blocchi)}
- Attività bloccate: {len(bloccate)}

7) PROSSIME ATTIVITÀ DA PRESIDIARE
{bullet(prossime, max_items=5)}

Sintesi Fixool:
Il cantiere è da monitorare con priorità sui blocchi aperti e sulle decisioni richieste. Aggiornare responsabili e scadenze entro la prossima finestra operativa.
"""
    client_report = f"""Aggiornamento cantiere - {date.today().strftime('%d/%m/%Y')}

Cantiere: {cantiere['nome']}

Avanzamento generale: {avanzamento}%
{barra_avanzamento} {avanzamento}% - {stato_sintetico}

Stato operativo: {rischio['livello']} - {rischio['sintesi']}

Attività completate/verificate:
{bullet(completate, max_items=4)}

Attività in corso:
{bullet(in_corso, max_items=4)}

Prossimi passaggi previsti:
{bullet(prossime, max_items=4)}

Punti da confermare / monitorare:
{bullet(ticket_aperti[ticket_aperti['tipo'].isin(['Richiesta decisione', 'Richiesta materiale'])] if len(ticket_aperti) else pd.DataFrame(), max_items=4)}

Fixool sta presidiando le attività aperte per mantenere il corretto avanzamento del cantiere. Eventuali decisioni richieste verranno condivise in modo puntuale.
"""
    return report, client_report


def page_report():
    st.header("Report progetto / cantiere")
    cantieri_map = get_cantieri_options()
    if not cantieri_map:
        st.info("Crea prima un progetto/cantiere.")
        return
    selected = st.selectbox("Cantiere", list(cantieri_map.keys()), key="report_cantiere")
    cantiere_id = cantieri_map[selected]
    render_cantiere_progress(cantiere_id, title="Barra avanzamento generale - cantiere selezionato")
    render_cantiere_risk(cantiere_id, title="Semaforo rischio operativo")
    report, client_report = make_daily_report(cantiere_id)
    tab1, tab2 = st.tabs(["Report interno", "Versione cliente"])
    with tab1:
        st.text_area("Copia e incolla su WhatsApp / email interna", value=report, height=520)
    with tab2:
        st.text_area("Versione pulita per cliente", value=client_report, height=420)



def _html_escape(value):
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _priority_class(priority):
    if priority == "Critica":
        return "pill-red"
    if priority == "Alta":
        return "pill-yellow"
    if priority == "Media":
        return "pill-blue"
    return "pill-gray"


def _risk_class(level):
    return "pill-red" if level == "Rosso" else "pill-yellow" if level == "Giallo" else "pill-green"


def render_capo_card(title, value, note=""):
    st.markdown(
        f"""
        <div class="fixool-card">
          <div class="fixool-card-title">{_html_escape(title)}</div>
          <div class="fixool-card-value">{_html_escape(value)}</div>
          <div class="fixool-card-note">{_html_escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_task_card(row, kind="task"):
    prio = row.get("priorita") or "Media"
    card_class = "critical" if prio == "Critica" else "high" if prio == "Alta" else ""
    titolo = _html_escape(row.get("titolo"))
    assegnato = _html_escape(row.get("assegnato_a") or row.get("responsabile") or "Da assegnare")
    stato = _html_escape(row.get("stato") or "-")
    scadenza = _html_escape(row.get("scadenza") or "-")
    fase = _html_escape(row.get("fase") or row.get("tipo") or "")
    pct = row.get("percentuale", None)
    pct_text = f" · {int(pct or 0)}%" if pct is not None else ""
    pill = _priority_class(prio)
    st.markdown(
        f"""
        <div class="task-card {card_class}">
          <div class="task-title">{titolo}</div>
          <div class="task-meta">
            <span class="fixool-pill {pill}">{_html_escape(prio)}</span>
            <span class="fixool-pill pill-gray">{stato}</span>
            {fase} · {assegnato} · scad. {scadenza}{pct_text}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_capo_cantiere():
    st.markdown(
        """
        <div class="fixool-hero">
          <h1>👷 Vista capo cantiere</h1>
          <p>Una schermata operativa unica: cosa controllare oggi, cosa aggiornare subito, cosa comunicare al cliente.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cantieri_map = get_cantieri_options()
    if not cantieri_map:
        st.info("Crea prima un progetto/cantiere nella sezione Progetti.")
        return
    selected = st.selectbox("Progetto / cantiere da governare", list(cantieri_map.keys()), key="capo_cantiere_main")
    cantiere_id = cantieri_map[selected]
    cantiere = query_df("SELECT * FROM cantieri WHERE id = ?", (cantiere_id,)).iloc[0]

    pct, total, completate, in_corso, bloccate = compute_cantiere_progress(cantiere_id)
    risk = assess_cantiere_risk(cantiere_id)
    open_tickets = query_df("SELECT * FROM ticket WHERE cantiere_id = ? AND stato NOT IN ('Risolto','Chiuso')", (cantiere_id,))
    critical_tickets = open_tickets[(open_tickets["stato"].eq("Bloccante")) | (open_tickets["priorita"].isin(["Alta", "Critica"]))] if len(open_tickets) else pd.DataFrame()

    st.markdown(f"### {cantiere['nome']}")
    st.caption(f"Cliente: {cantiere['cliente'] or '-'} · Capo cantiere: {cantiere['capo_cantiere'] or '-'} · Stato: {cantiere['stato'] or '-'}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_capo_card("Avanzamento", f"{pct}%", cantiere_progress_label(pct))
    with c2:
        render_capo_card("Rischio", risk["livello"], risk["sintesi"])
    with c3:
        render_capo_card("Attività aperte", total - completate, f"{in_corso} in corso · {bloccate} bloccate")
    with c4:
        render_capo_card("Ticket aperti", len(open_tickets), f"{len(critical_tickets)} urgenti/bloccanti")

    st.progress(pct / 100, text=f"Avanzamento generale cantiere: {pct}% - {cantiere_progress_label(pct)}")
    risk_pill = _risk_class(risk["livello"])
    st.markdown(
        f"<span class='fixool-pill {risk_pill}'>Rischio {risk['livello']}</span> <span class='small-muted'>{_html_escape(', '.join(risk['motivi']))}. {_html_escape(risk['azione'])}</span>",
        unsafe_allow_html=True,
    )

    tab_oggi, tab_aggiorna, tab_blocchi, tab_report = st.tabs(["🔥 Oggi", "⚡ Aggiorna rapido", "🚧 Blocchi", "📩 Report cliente"])

    with tab_oggi:
        st.markdown("<div class='fixool-section-title'>Priorità operative di oggi</div>", unsafe_allow_html=True)
        urgent_tasks = query_df(
            """
            SELECT id, fase, titolo, assegnato_a, stato, priorita, scadenza, percentuale
            FROM attivita
            WHERE cantiere_id = ? AND stato NOT IN ('Completata','Verificata')
            ORDER BY CASE priorita WHEN 'Critica' THEN 1 WHEN 'Alta' THEN 2 WHEN 'Media' THEN 3 ELSE 4 END, scadenza, id
            LIMIT 8
            """,
            (cantiere_id,),
        )
        if len(urgent_tasks) == 0:
            st.success("Nessuna attività aperta: il cantiere risulta completato o da pianificare.")
        else:
            for _, row in urgent_tasks.iterrows():
                render_task_card(row)
        st.markdown("<div class='fixool-section-title'>Blocchi da sbloccare</div>", unsafe_allow_html=True)
        blocchi = query_df(
            """
            SELECT id, tipo, titolo, responsabile, stato, priorita, scadenza, impatto
            FROM ticket
            WHERE cantiere_id = ? AND stato NOT IN ('Risolto','Chiuso')
            ORDER BY CASE priorita WHEN 'Critica' THEN 1 WHEN 'Alta' THEN 2 WHEN 'Media' THEN 3 ELSE 4 END, scadenza, id
            LIMIT 6
            """,
            (cantiere_id,),
        )
        if len(blocchi) == 0:
            st.success("Nessun blocco aperto.")
        else:
            for _, row in blocchi.iterrows():
                render_task_card(row, kind="ticket")

    with tab_aggiorna:
        st.markdown("<div class='fixool-section-title'>Aggiorna una attività in 30 secondi</div>", unsafe_allow_html=True)
        act_df = query_df(
            "SELECT id, titolo, stato, priorita, percentuale, note FROM attivita WHERE cantiere_id = ? ORDER BY scadenza, id",
            (cantiere_id,),
        )
        if len(act_df):
            act_label = st.selectbox("Attività", [f"{int(r.id)} - {r.titolo}" for r in act_df.itertuples()], key="capo_update_activity")
            act_id = int(act_label.split(" - ")[0])
            act_row = act_df[act_df["id"].eq(act_id)].iloc[0]
            with st.form("capo_fast_update_activity"):
                col1, col2, col3 = st.columns(3)
                nuovo_stato = col1.selectbox("Stato", STATI_ATTIVITA, index=STATI_ATTIVITA.index(act_row["stato"]) if act_row["stato"] in STATI_ATTIVITA else 0)
                nuova_prio = col2.selectbox("Priorità", PRIORITA, index=PRIORITA.index(act_row["priorita"]) if act_row["priorita"] in PRIORITA else 1)
                nuova_pct = col3.slider("Avanzamento %", 0, 100, int(act_row["percentuale"] or 0), step=5)
                nota = st.text_area("Nota rapida", placeholder="Es. completato lato idraulico, manca verifica capo cantiere")
                submitted = st.form_submit_button("Aggiorna attività", type="primary")
            if submitted:
                nuova_pct = progress_from_status(nuovo_stato, nuova_pct)
                old_note = act_row["note"] or ""
                new_note = old_note
                if nota.strip():
                    new_note = (old_note + "\n" if old_note else "") + f"[{datetime.now().strftime('%d/%m %H:%M')}] {nota.strip()}"
                execute("UPDATE attivita SET stato = ?, priorita = ?, percentuale = ?, note = ? WHERE id = ?", (nuovo_stato, nuova_prio, nuova_pct, new_note, act_id))
                update_closed_at("attivita", act_id, nuovo_stato)
                st.success("Attività aggiornata.")
                st.rerun()
        else:
            st.info("Non ci sono attività da aggiornare.")

        st.markdown("<div class='fixool-section-title'>Apri un blocco / richiesta</div>", unsafe_allow_html=True)
        with st.form("capo_fast_ticket"):
            col1, col2 = st.columns(2)
            tipo = col1.selectbox("Tipo", ["Blocco", "Richiesta decisione", "Richiesta materiale", "Rischio ritardo", "Difetto / non conformità"])
            priorita = col2.selectbox("Priorità", ["Alta", "Critica", "Media", "Bassa"])
            titolo = st.text_input("Titolo breve", placeholder="Es. Confermare posizione termoarredo")
            descrizione = st.text_area("Descrizione", placeholder="Scrivi cosa blocca il cantiere e cosa serve per sbloccarlo")
            col3, col4 = st.columns(2)
            responsabile = col3.text_input("Responsabile", placeholder="Capo cantiere / cliente / artigiano")
            scadenza = col4.date_input("Scadenza", value=date.today() + timedelta(days=1))
            impatto = st.text_input("Impatto", placeholder="Es. rischio slittamento pavimentista di 1 giorno")
            submitted = st.form_submit_button("Crea ticket", type="primary")
        if submitted:
            if not titolo.strip():
                st.error("Inserisci almeno il titolo del ticket.")
            else:
                stato = "Bloccante" if tipo == "Blocco" or priorita == "Critica" else "Aperto"
                execute(
                    """INSERT INTO ticket(cantiere_id, tipo, titolo, descrizione, aperto_da, responsabile, priorita, stato, impatto, scadenza)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (cantiere_id, tipo, titolo.strip(), descrizione, "Capo cantiere", responsabile, priorita, stato, impatto, str(scadenza)),
                )
                st.success("Ticket creato.")
                st.rerun()

    with tab_blocchi:
        st.markdown("<div class='fixool-section-title'>Gestione rapida blocchi aperti</div>", unsafe_allow_html=True)
        tic_df = query_df(
            """
            SELECT id, tipo, titolo, responsabile, priorita, stato, scadenza, impatto
            FROM ticket
            WHERE cantiere_id = ? AND stato NOT IN ('Risolto','Chiuso')
            ORDER BY CASE priorita WHEN 'Critica' THEN 1 WHEN 'Alta' THEN 2 WHEN 'Media' THEN 3 ELSE 4 END, scadenza, id
            """,
            (cantiere_id,),
        )
        if len(tic_df) == 0:
            st.success("Non ci sono blocchi/ticket aperti.")
        else:
            st.dataframe(tic_df, use_container_width=True, hide_index=True)
            ticket_label = st.selectbox("Ticket da aggiornare", [f"{int(r.id)} - {r.titolo}" for r in tic_df.itertuples()], key="capo_update_ticket")
            ticket_id = int(ticket_label.split(" - ")[0])
            row = tic_df[tic_df["id"].eq(ticket_id)].iloc[0]
            with st.form("capo_fast_update_ticket"):
                col1, col2, col3 = st.columns(3)
                nuovo_stato = col1.selectbox("Stato", STATI_TICKET, index=STATI_TICKET.index(row["stato"]) if row["stato"] in STATI_TICKET else 0)
                nuova_prio = col2.selectbox("Priorità", PRIORITA, index=PRIORITA.index(row["priorita"]) if row["priorita"] in PRIORITA else 1)
                nuovo_resp = col3.text_input("Responsabile", value=row["responsabile"] or "")
                nuovo_impatto = st.text_area("Impatto / nota", value=row["impatto"] or "")
                submitted = st.form_submit_button("Aggiorna ticket", type="primary")
            if submitted:
                execute("UPDATE ticket SET stato = ?, priorita = ?, responsabile = ?, impatto = ? WHERE id = ?", (nuovo_stato, nuova_prio, nuovo_resp, nuovo_impatto, ticket_id))
                update_closed_at("ticket", ticket_id, nuovo_stato)
                st.success("Ticket aggiornato.")
                st.rerun()

    with tab_report:
        st.markdown("<div class='fixool-section-title'>Report cliente pronto da copiare</div>", unsafe_allow_html=True)
        report, client_report = make_daily_report(cantiere_id)
        st.text_area("Versione cliente", value=client_report, height=360)
        st.caption("Usa questa versione per WhatsApp/email al cliente. È volutamente pulita: avanzamento, prossimi step e punti da confermare.")


def page_progetti():
    st.header("Progetti")
    st.caption(
        "Area unica per gestire il singolo progetto/cantiere: anagrafica, template operativo, attività, ticket e report. "
        "L'obiettivo è avere un unico punto di governo per capo cantiere e direzione Fixool."
    )
    area = st.radio(
        "Area progetto",
        [
            "Anagrafica progetto",
            "Template operativo",
            "Attività",
            "Ticket / Assistente",
            "Report interno / cliente",
        ],
        horizontal=True,
    )
    st.markdown("---")
    if area == "Anagrafica progetto":
        page_cantieri()
    elif area == "Template operativo":
        page_template_cantiere()
    elif area == "Attività":
        page_attivita()
    elif area == "Ticket / Assistente":
        page_ticket()
    elif area == "Report interno / cliente":
        page_report()


def page_export():
    st.header("Export dati")
    st.caption("Esporta i dati del pilota per analisi, backup o condivisione.")
    if DB_PATH.exists():
        st.download_button("Scarica backup database completo (.db)", data=DB_PATH.read_bytes(), file_name="fixool_site_os_backup.db", mime="application/octet-stream")
    st.markdown("---")
    tables = ["cantieri", "artigiani", "attivita", "ticket", "aggiornamenti"]
    for table in tables:
        df = query_df(f"SELECT * FROM {table}")
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(f"Scarica {table}.csv", data=csv, file_name=f"fixool_{table}.csv", mime="text/csv")
        with st.expander(f"Anteprima {table}"):
            st.dataframe(df, use_container_width=True, hide_index=True)


def page_settings():
    st.header("Impostazioni pilota")
    st.warning("Usare con attenzione: queste azioni modificano il database locale.")
    uploaded_db = st.file_uploader("Ripristina backup database (.db)", type=["db", "sqlite", "sqlite3"])
    if uploaded_db is not None and st.button("Carica backup e sostituisci database attuale"):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        DB_PATH.write_bytes(uploaded_db.getbuffer())
        st.success("Backup ripristinato. Ricarico l'app.")
        st.rerun()
    st.markdown("---")
    if st.button("Carica dati demo", type="secondary"):
        seed_demo_data()
        st.success("Dati demo caricati se il database era vuoto.")
        st.rerun()
    if st.button("Svuota database locale", type="primary"):
        with connect() as conn:
            for table in ["aggiornamenti", "ticket", "attivita", "artigiani", "cantieri"]:
                conn.execute(f"DELETE FROM {table}")
            conn.commit()
        st.success("Database svuotato.")
        st.rerun()


def main():
    if not require_password():
        return
    init_db()
    apply_ui_styles()
    if "initialized" not in st.session_state:
        seed_demo_data()
        st.session_state["initialized"] = True
    st.sidebar.title("🏗️ Fixool Site OS Light")
    st.sidebar.caption("MVP cloud-ready per coordinamento cantieri - Patch V7")
    st.sidebar.caption(f"Database: {DB_PATH.name}")
    page = st.sidebar.radio(
        "Menu",
        [
            "Capo cantiere",
            "Dashboard",
            "Progetti",
            "Artigiani / Squadre",
            "Export",
            "Impostazioni",
        ],
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Metodo Fixool**")
    st.sidebar.markdown("1. Ogni problema diventa ticket\n2. Ogni ticket ha responsabile\n3. Ogni blocco ha impatto\n4. Ogni giorno si produce un report")

    if page == "Capo cantiere":
        page_capo_cantiere()
    elif page == "Dashboard":
        page_dashboard()
    elif page == "Progetti":
        page_progetti()
    elif page == "Artigiani / Squadre":
        page_artigiani()
    elif page == "Export":
        page_export()
    elif page == "Impostazioni":
        page_settings()


if __name__ == "__main__":
    main()
