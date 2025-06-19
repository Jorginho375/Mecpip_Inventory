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

def get_filtered_data(dept):
    if dept and dept != "Tous":
        return pd.read_sql_query("SELECT * FROM computers WHERE department = ?", conn, params=(dept,))
    return pd.read_sql_query("SELECT * FROM computers", conn)

def export_pdf(df):
    class PDF(FPDF):
        def header(self):
            self.image("static/logo.jpg", 10, 8, 25)
            self.set_font("Arial", 'B', 14)
            self.cell(0, 10, "INVENTAIRE INFORMATIQUE - MECPIP", ln=True, align="C")
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

        def render_table(self, df):
            self.set_font("Arial", size=9)
            col_widths = [25, 20, 25, 25, 20, 20, 30, 15, 15]
            headers = ["Nom", "Type", "Département", "Utilisateur", "Achat", "Statut", "N° Série", "AV", "Domaine"]
            for i, header in enumerate(headers):
                self.cell(col_widths[i], 8, header, 1)
            self.ln()
            for index, row in df.iterrows():
                row_data = row[1:]
                for i, item in enumerate(row_data):
                    self.cell(col_widths[i], 6, str(item)[:25], 1)
                self.ln()

    pdf = PDF()
    pdf.add_page()
    pdf.render_table(df)
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

# Sidebar
st.sidebar.image("static/logo.jpg", width=150)
st.sidebar.title("📊 Inventaire MECPIP")
menu = st.sidebar.radio("Navigation", ["Dashboard", "Ajouter un équipement"])

# Formulaire d'ajout
with st.expander("Ajouter un équipement"):
    with st.form("ajout_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            nom = st.text_input("Nom")
            type_ = st.selectbox("Type", ["Laptop", "Desktop", "Imprimante", "Scanner", "Copieur", "Projecteur", "Écran", "Onduleur", "Serveur", "Switch", "Routeur", "Pare-Feu"])
            departement = st.text_input("Département")
        with col2:
            utilisateur = st.text_input("Utilisateur")
            date_achat = st.date_input("Date Achat")
            statut = st.selectbox("Statut", ["Actif", "HS"])
        with col3:
            serial = st.text_input("N° Série")
            antivirus = st.selectbox("Antivirus installé", ["Oui", "Non"])
            domaine = st.selectbox("Intégré au domaine", ["Oui", "Non"])

        submitted = st.form_submit_button("Enregistrer")
        if submitted:
            df.loc[len(df)] = [nom, type_, departement, utilisateur, date_achat, statut, serial, antivirus, domaine]
            st.success("Équipement ajouté avec succès")

# Filtres
st.sidebar.header("Filtres")
filtre_dept = st.sidebar.multiselect("Filtrer par département", options=df["Departement"].unique())
if filtre_dept:
    filtered_df = df[df["Departement"].isin(filtre_dept)]
else:
    filtered_df = df

# Affichage
st.subheader("Liste des équipements")
st.dataframe(filtered_df, use_container_width=True)

# Graphiques
st.subheader("Statistiques")
if not filtered_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        fig_type = px.pie(filtered_df, names="Type", title="Répartition par type")
        st.plotly_chart(fig_type)
    with col2:
        fig_dept = px.histogram(filtered_df, x="Departement", title="Nombre par département")
        st.plotly_chart(fig_dept)

# Export Excel
excel_buffer = BytesIO()
filtered_df.to_excel(excel_buffer, index=False, engine="openpyxl")
excel_buffer.seek(0)
st.download_button("⬇️ Export Excel", data=excel_buffer, file_name="inventaire.xlsx")

# Export PDF
def export_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Inventaire MECPIP", ln=True, align="C")

    pdf.set_font("Arial", size=10)
    pdf.ln(10)

    # En-tête
    for col in df.columns:
        pdf.cell(30, 10, str(col), 1)
    pdf.ln()

    # Contenu
    for _, row in df.iterrows():
        for val in row:
            pdf.cell(30, 10, str(val)[:15], 1)
        pdf.ln()

    pdf_output = pdf.output(dest='S').encode("latin1")
    return BytesIO(pdf_output)

st.download_button("⬇️ Export PDF", data=export_pdf(filtered_df), file_name="inventaire.pdf", mime="application/pdf")
