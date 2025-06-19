# MECPIP Inventory Streamlit Version
# Converted from Flask to Streamlit for Streamlit Cloud compatibility

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
import os

DB_NAME = "inventory.db"

# ========== Initialize Database ==========
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS computers (
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
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                computer_id INTEGER,
                user TEXT,
                department TEXT,
                date TEXT,
                FOREIGN KEY (computer_id) REFERENCES computers(id)
            )
        """)
        conn.commit()

# ========== Add Equipment Entry ==========
def add_equipment(data):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO computers (name, type, department, user, purchase_date, status, serial_number, antivirus, domain_joined)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", data)
        cid = c.lastrowid
        c.execute("""
            INSERT INTO movements (computer_id, user, department, date)
            VALUES (?, ?, ?, ?)""", (cid, data[3], data[2], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()

# ========== Load Data ==========
def load_data():
    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql_query("SELECT * FROM computers", conn)
        m = pd.read_sql_query("""
            SELECT c.name AS poste, m.user, m.department, m.date
            FROM movements m JOIN computers c ON m.computer_id = c.id
            ORDER BY m.date DESC
        """, conn)
    return df, m

# ========== Export PDF ==========
def export_pdf(data):
    class PDF(FPDF):
        def header(self):
            logo_path = os.path.join("static", "logo.jpg")
            if os.path.exists(logo_path):
                self.image(logo_path, 10, 8, 33)
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, "Inventaire Informatique - MECPIP", ln=1, align="C")
            self.set_font("Arial", "", 10)
            self.cell(0, 10, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1, align="C")
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

        def table(self, data):
            self.set_font("Arial", "B", 9)
            col_widths = [8, 28, 20, 25, 25, 20, 15, 28, 15, 15]
            headers = ["#", "Nom", "Type", "Département", "Utilisateur", "Date Achat", "Statut", "Numéro de série", "AV", "Domaine"]
            for i, header in enumerate(headers):
                self.cell(col_widths[i], 7, header, border=1, align="C")
            self.ln()
            self.set_font("Arial", "", 9)
            for _, row in data.iterrows():
                values = [row['id'], row['name'], row['type'], row['department'], row['user'], row['purchase_date'], row['status'], row['serial_number'], row['antivirus'], row['domain_joined']]
                for i in range(len(headers)):
                    self.cell(col_widths[i], 6, str(values[i])[:25], border=1)
                self.ln()

    pdf = PDF()
    pdf.add_page()
    pdf.table(data)
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

# ========== Main App ==========
init_db()
st.set_page_config(layout="wide")
st.title("📋 Inventaire Informatique - MECPIP")

# Formulaire d'ajout
with st.form("add_form"):
    st.subheader("Ajouter un équipement")
    cols = st.columns(4)
    name = cols[0].text_input("Nom du poste")
    type_ = cols[1].selectbox("Type", ["Laptop", "Desktop", "Imprimante", "Scanner", "Copieur", "Projecteur", "Écran", "Onduleur", "Serveur", "Switch", "Routeur", "Pare-Feu"])
    dept = cols[2].text_input("Département")
    user = cols[3].text_input("Utilisateur")

    cols2 = st.columns(4)
    date = cols2[0].date_input("Date d'achat")
    status = cols2[1].selectbox("Statut", ["Actif", "HS"])
    serial = cols2[2].text_input("Numéro de série")
    av = cols2[3].selectbox("Antivirus installé", ["Oui", "Non"])
    domain = st.selectbox("Intégré au domaine", ["Oui", "Non"])

    submitted = st.form_submit_button("Ajouter")
    if submitted:
        add_equipment((name, type_, dept, user, date.strftime('%Y-%m-%d'), status, serial, av, domain))
        st.success("Équipement ajouté avec succès.")

# Affichage
df, movements = load_data()

col1, col2, col3 = st.columns([1,1,2])
with col1:
    st.download_button("⬇️ Export Excel", data=df.to_excel(index=False), file_name="inventaire.xlsx")
with col2:
    pdf_data = export_pdf(df)
    st.download_button("⬇️ Export PDF", data=pdf_data, file_name="Inventaire_MECPIP.pdf")
with col3:
    st.write(" ")

st.subheader("📊 Statistiques")
col1, col2 = st.columns(2)
with col1:
    st.bar_chart(df['department'].value_counts())
with col2:
    st.plotly_chart(pd.DataFrame(df['type'].value_counts()).plot.pie(y='type', figsize=(5,5), legend=False).figure)

st.subheader("📌 Liste des équipements")
st.dataframe(df)

st.subheader("📎 Historique des mouvements")
st.dataframe(movements)
