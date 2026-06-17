import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

APP_TITLE = "Fixool Site OS Light"
DB_PATH = Path(__file__).with_name("fixool_site_os.db")
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

st.set_page_config(page_title=APP_TITLE, page_icon="🏗️", layout="wide")


def connect():
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
    ticket_aperti = int(~tic["stato"].isin(["Risolto", "Chiuso"]).sum()) if len(tic) else 0
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


def page_dashboard():
    st.header("Dashboard operativa")
    cantieri_map = get_cantieri_options()
    all_option = "Tutti i cantieri"
    options = [all_option] + list(cantieri_map.keys())
    selected = st.selectbox("Vista", options)
    cantiere_id = None if selected == all_option else cantieri_map[selected]
    kpi_cards(cantiere_id)

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

    st.subheader("Prossime attività in scadenza")
    prossime = query_df(
        f"""
        SELECT a.id, c.nome AS cantiere, a.fase, a.titolo, a.assegnato_a, a.stato, a.priorita, a.scadenza
        FROM attivita a JOIN cantieri c ON c.id = a.cantiere_id
        {where + (' AND ' if where else 'WHERE ')} a.stato NOT IN ('Completata','Verificata')
        ORDER BY a.scadenza LIMIT 20
        """,
        params,
    )
    st.dataframe(prossime, use_container_width=True, hide_index=True)


def page_cantieri():
    st.header("Cantieri")
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

    st.subheader("Elenco cantieri")
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
    st.header("Attività di cantiere")
    cantieri_map = get_cantieri_options()
    if not cantieri_map:
        st.info("Crea prima un cantiere.")
        return
    selected = st.selectbox("Cantiere", list(cantieri_map.keys()))
    cantiere_id = cantieri_map[selected]
    kpi_cards(cantiere_id)

    tab1, tab2 = st.tabs(["Nuova attività", "Aggiorna attività"])
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
                execute(
                    """INSERT INTO attivita(cantiere_id, fase, titolo, descrizione, assegnato_a, dipende_da_id, stato, priorita, scadenza, percentuale, note)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (cantiere_id, fase, titolo.strip(), descrizione, assegnato, dip_options[dip_label], stato, priorita, str(scadenza), percentuale, note),
                )
                st.success("Attività creata.")
                st.rerun()

    with tab2:
        att_df = query_df(
            "SELECT id, fase, titolo, assegnato_a, stato, priorita, scadenza, percentuale, note FROM attivita WHERE cantiere_id = ? ORDER BY scadenza, id",
            (cantiere_id,),
        )
        st.dataframe(att_df, use_container_width=True, hide_index=True)
        if len(att_df):
            act_label = st.selectbox("Seleziona attività da aggiornare", [f"{row.id} - {row.titolo}" for row in att_df.itertuples()])
            act_id = int(act_label.split(" - ")[0])
            row = query_df("SELECT * FROM attivita WHERE id = ?", (act_id,)).iloc[0]
            with st.form("update_attivita"):
                col1, col2, col3 = st.columns(3)
                nuovo_stato = col1.selectbox("Nuovo stato", STATI_ATTIVITA, index=STATI_ATTIVITA.index(row["stato"]) if row["stato"] in STATI_ATTIVITA else 0)
                nuova_prio = col2.selectbox("Priorità", PRIORITA, index=PRIORITA.index(row["priorita"]) if row["priorita"] in PRIORITA else 1)
                nuova_pct = col3.slider("Avanzamento %", 0, 100, int(row["percentuale"] or 0), step=5)
                nuove_note = st.text_area("Note", value=row["note"] or "")
                submitted = st.form_submit_button("Aggiorna attività")
            if submitted:
                execute("UPDATE attivita SET stato = ?, priorita = ?, percentuale = ?, note = ? WHERE id = ?", (nuovo_stato, nuova_prio, nuova_pct, nuove_note, act_id))
                update_closed_at("attivita", act_id, nuovo_stato)
                st.success("Attività aggiornata.")
                st.rerun()


def page_ticket():
    st.header("Ticket, blocchi e richieste")
    cantieri_map = get_cantieri_options()
    if not cantieri_map:
        st.info("Crea prima un cantiere.")
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

    def bullet(df, col="titolo", max_items=6):
        if df is None or len(df) == 0:
            return "- Nessuno"
        return "\n".join([f"- {row[col]}" for _, row in df.head(max_items).iterrows()])

    report = f"""REPORT GIORNALIERO FIXOOL - {date.today().strftime('%d/%m/%Y')}

Cantiere: {cantiere['nome']}
Cliente: {cantiere['cliente'] or '-'}
Capo cantiere: {cantiere['capo_cantiere'] or '-'}

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

Sintesi Fixool:
Il cantiere è da monitorare con priorità sui blocchi aperti e sulle decisioni richieste. Aggiornare responsabili e scadenze entro la prossima finestra operativa.
"""
    client_report = f"""Aggiornamento cantiere - {date.today().strftime('%d/%m/%Y')}

Cantiere: {cantiere['nome']}

Avanzamento principale:
{bullet(completate, max_items=4)}

Attività in corso:
{bullet(in_corso, max_items=4)}

Punti da confermare / monitorare:
{bullet(ticket_aperti[ticket_aperti['tipo'].isin(['Richiesta decisione', 'Richiesta materiale'])] if len(ticket_aperti) else pd.DataFrame(), max_items=4)}

Fixool sta presidiando le attività aperte per mantenere il corretto avanzamento del cantiere.
"""
    return report, client_report


def page_report():
    st.header("Report giornaliero")
    cantieri_map = get_cantieri_options()
    if not cantieri_map:
        st.info("Crea prima un cantiere.")
        return
    selected = st.selectbox("Cantiere", list(cantieri_map.keys()), key="report_cantiere")
    cantiere_id = cantieri_map[selected]
    report, client_report = make_daily_report(cantiere_id)
    tab1, tab2 = st.tabs(["Report interno", "Versione cliente"])
    with tab1:
        st.text_area("Copia e incolla su WhatsApp / email interna", value=report, height=520)
    with tab2:
        st.text_area("Versione pulita per cliente", value=client_report, height=420)


def page_export():
    st.header("Export dati")
    st.caption("Esporta i dati del pilota per analisi, backup o condivisione.")
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
    init_db()
    if "initialized" not in st.session_state:
        seed_demo_data()
        st.session_state["initialized"] = True
    st.sidebar.title("🏗️ Fixool Site OS Light")
    st.sidebar.caption("MVP per coordinamento cantieri")
    page = st.sidebar.radio(
        "Menu",
        [
            "Dashboard",
            "Cantieri",
            "Artigiani",
            "Attività",
            "Ticket / Assistente",
            "Report giornaliero",
            "Export",
            "Impostazioni",
        ],
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Metodo Fixool**")
    st.sidebar.markdown("1. Ogni problema diventa ticket\n2. Ogni ticket ha responsabile\n3. Ogni blocco ha impatto\n4. Ogni giorno si produce un report")

    if page == "Dashboard":
        page_dashboard()
    elif page == "Cantieri":
        page_cantieri()
    elif page == "Artigiani":
        page_artigiani()
    elif page == "Attività":
        page_attivita()
    elif page == "Ticket / Assistente":
        page_ticket()
    elif page == "Report giornaliero":
        page_report()
    elif page == "Export":
        page_export()
    elif page == "Impostazioni":
        page_settings()


if __name__ == "__main__":
    main()
