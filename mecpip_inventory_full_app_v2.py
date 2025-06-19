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

if menu == "Ajouter un équipement":
    st.markdown("## ➕ Ajouter un nouvel équipement")
    with st.form("add_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("Nom du poste")
            type_ = st.selectbox("Type", ["Laptop", "Desktop", "Imprimante", "Scanner", "Copieur", "Projecteur", "Écran", "Onduleur", "Serveur", "Switch", "Routeur", "Pare-Feu"])
            status = st.selectbox("Statut", ["Actif", "HS"])
        with col2:
            department = st.text_input("Département")
            user = st.text_input("Utilisateur")
            serial_number = st.text_input("Numéro de série")
        with col3:
            purchase_date = st.date_input("Date d'achat")
            antivirus = st.radio("Antivirus installé", ["Oui", "Non"])
            domain_joined = st.radio("Intégré au domaine", ["Oui", "Non"])

        submitted = st.form_submit_button("Enregistrer")
        if submitted:
            insert_data(name, type_, department, user, str(purchase_date), status, serial_number, antivirus, domain_joined)
            st.success("✅ Équipement enregistré avec succès.")

if menu == "Dashboard":
    st.markdown("# 📋 Tableau de bord de l'inventaire")

    dept_filter = st.selectbox("Filtrer par département", ["Tous"] + [row[0] for row in c.execute("SELECT DISTINCT department FROM computers").fetchall()])
    df = get_filtered_data(dept_filter)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.dataframe(df, use_container_width=True)
    with col2:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)
        st.download_button("⬇️ Export Excel", data=buffer.getvalue(), file_name="inventaire.xlsx")
        st.download_button("⬇️ Export PDF", data=export_pdf(df), file_name="inventaire.pdf")

    if not df.empty:
        st.markdown("## 📊 Graphique par Type de Matériel")
        pie_chart = px.pie(df, names='type', title='Répartition par type')
        st.plotly_chart(pie_chart, use_container_width=True)
