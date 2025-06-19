import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
import plotly.express as px

st.set_page_config(page_title="Inventaire MECPIP", layout="wide")

# Initialisation de la base de données
conn = sqlite3.connect("inventory.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS computers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    type TEXT,
    department TEXT,
    user TEXT,
    purchase_date TEXT,
    status TEXT,
    serial_number TEXT,
    antivirus TEXT,
    domain_joined TEXT
)''')
conn.commit()

def insert_data(name, type_, department, user, purchase_date, status, serial_number, antivirus, domain_joined):
    c.execute("""
        INSERT INTO computers (name, type, department, user, purchase_date, status, serial_number, antivirus, domain_joined)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, type_, department, user, purchase_date, status, serial_number, antivirus, domain_joined))
    conn.commit()

def get_data():
    return pd.read_sql_query("SELECT * FROM computers", conn)

# Fonction export PDF
def export_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Inventaire MECPIP", ln=True, align="C")
    pdf.set_font("Arial", size=10)
    pdf.ln(10)

    for col in df.columns[1:]:
        pdf.cell(30, 10, str(col), 1)
    pdf.ln()

    for _, row in df.iterrows():
        for val in row[1:]:
            pdf.cell(30, 10, str(val)[:15], 1)
        pdf.ln()

    return BytesIO(pdf.output(dest="S").encode("latin1"))

# Sidebar
st.sidebar.image("static/logo.jpg", width=150)
st.sidebar.title("📊 Inventaire MECPIP")
menu = st.sidebar.radio("Navigation", ["Dashboard", "Ajouter un équipement"])

# Dashboard
if menu == "Dashboard":
    df = get_data()
    
    st.sidebar.header("Filtres")
    filtre_dept = st.sidebar.multiselect("Filtrer par département", options=df["department"].unique())
    if filtre_dept:
        df = df[df["department"].isin(filtre_dept)]

    st.subheader("Liste des équipements")
    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("⬇️ Export Excel", data=df.to_excel(index=False, engine='openpyxl'), file_name="inventaire.xlsx")

    with col2:
        st.download_button("⬇️ Export PDF", data=export_pdf(df), file_name="inventaire.pdf", mime="application/pdf")

    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.pie(df, names="type", title="Répartition par type"))
        with col2:
            st.plotly_chart(px.histogram(df, x="department", title="Équipements par département"))

# Formulaire d'ajout
if menu == "Ajouter un équipement":
    with st.form("ajout_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            nom = st.text_input("Nom")
            type_ = st.selectbox("Type", ["Laptop", "Desktop", "Imprimante", "Scanner", "Copieur", "Projecteur", "Écran", "Onduleur", "Serveur", "Switch", "Routeur", "Pare-Feu"])
            departement = st.text_input("Département")
        with col2:
            utilisateur = st.text_input("Utilisateur")
            date_achat = st.date_input("Date de Mise en Service")
            statut = st.selectbox("Statut", ["Actif", "HS"])
        with col3:
            serial = st.text_input("N° Série")
            antivirus = st.selectbox("Antivirus installé", ["Oui", "Non"])
            domaine = st.selectbox("Intégré au domaine", ["Oui", "Non"])

        submitted = st.form_submit_button("Enregistrer")
        if submitted:
            insert_data(nom, type_, departement, utilisateur, str(date_achat), statut, serial, antivirus, domaine)
            st.success("✅ Équipement ajouté avec succès.")
