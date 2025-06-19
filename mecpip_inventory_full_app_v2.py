# MECPIP Inventory Full App (CORRIGÉ) - Single File Version
# Image background, extended device types, domain/AV flags, assignment tracking


from flask import Flask, request, redirect, url_for, render_template_string, session, send_file
import sqlite3
import pandas as pd
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clef_secrete_mecpip_2025'

# ==================== INIT DB ====================
def init_db():
    with sqlite3.connect("inventory.db") as conn:
        c = conn.cursor()
        # Table principale des équipements
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
        # Historique des affectations
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

# ==================== PARAMS ====================
ADMIN_USER = 'admin'
ADMIN_PASS = 'password123'


# ==================== TEMPLATES ====================

login_template = """
<!DOCTYPE html>
<html lang='fr'>
<head>
    <meta charset='UTF-8'>
    <title>Connexion MECPIP</title>
    <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>
</head>
<body style="background: url('/static/bg.jpg') no-repeat center center fixed; background-size: cover;">
    <div class='container d-flex justify-content-center align-items-center' style='height:100vh;'>
        <div class='card shadow p-4' style='min-width:350px; background-color: rgba(255,255,255,0.9); border-radius: 15px;'>
            <h4 class='text-center mb-3'>Connexion Administrateur</h4>
            {% if error %}<div class='alert alert-danger'>{{ error }}</div>{% endif %}
            <form method='post'>
                <input type='text' name='username' class='form-control mb-3' placeholder='Nom utilisateur' required>
                <input type='password' name='password' class='form-control mb-3' placeholder='Mot de passe' required>
                <button class='btn btn-primary w-100'>Connexion</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

dashboard_template = """
<!DOCTYPE html>
<html lang='fr'>
<head>
    <meta charset='UTF-8'>
    <title>Inventaire Informatique - MECPIP</title>
    <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>
    <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
    <style>
        
        .bg-overlay {
            background-color: rgba(255,255,255,0.92);
            padding: 2rem;
            border-radius: 12px;
        }
    </style>
</head>
<body>
<div class='container mt-4 bg-overlay'>
    <div class='d-flex justify-content-between align-items-center mb-4'>
        <h3><img src='/static/logo.jpg' width='150'/>Département Informatique - Inventaire</h3>
        <a href='/logout' class='btn btn-danger btn-sm'>Déconnexion</a>
    </div>

    <form class='row g-2 mb-4' method='post' action='/add'>
        <div class='col-md-2'><input type='text' name='name' class='form-control' placeholder='Nom du poste' required></div>
        <div class='col-md-2'>
            <select name='type' class='form-control'>
                <option>Laptop</option><option>Desktop</option><option>Imprimante</option><option>Scanner</option>
                <option>Copieur</option><option>Projecteur</option><option>Écran</option><option>Onduleur</option>
                <option>Serveur</option><option>Switch</option><option>Routeur</option><option>Pare-Feu</option>
            </select>
        </div>
        <div class='col-md-2'><input type='text' name='department' class='form-control' placeholder='Département' required></div>
        <div class='col-md-2'><input type='text' name='user' class='form-control' placeholder='Utilisateur' required></div>
        <div class='col-md-2'><input type='date' name='purchase_date' class='form-control' required></div>
        <div class='col-md-2'><input type='text' name='serial_number' class='form-control' placeholder='Numéro de série'></div>
        <div class='col-md-1'><select name='status' class='form-control'><option>Actif</option><option>HS</option></select></div>
        <div class='col-md-2'><label class='form-label'>Antivirus installé</label><select name='antivirus' class='form-control'><option>Oui</option><option>Non</option></select></div>
        <div class='col-md-2'><label class='form-label'>Intégré au domaine</label><select name='domain_joined' class='form-control'><option>Oui</option><option>Non</option></select></div>
        <div class='col-md-1'><button class='btn btn-success w-100'>Ajouter</button></div>
    </form>

    <div class='row mb-4'>
        <div class='col-md-6'><canvas id='deptChart'></canvas></div>
        <div class='col-md-6'><canvas id='typeChart'></canvas></div>
    </div>

    <div class='d-flex justify-content-end mb-2'>
        <a href='/export' class='btn btn-outline-primary btn-sm me-2'>Exporter Excel</a><a href='/export_pdf' class='btn btn-outline-success btn-sm'>Exporter PDF</a>
    </div>

    <h5 class='mt-4'>Liste des équipements</h5>
    <table class='table table-bordered table-striped'>
        <thead class='table-dark'><tr><th>#</th><th>Nom</th><th>Type</th><th>Département</th><th>Utilisateur</th><th>Achat</th><th>Statut</th><th>Numéro de série</th><th>Antivirus</th><th>Domaine</th><th>Actions</th></tr></thead>
        <tbody>
        {% for row in rows %}
        <tr>
            <td>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ row[2] }}</td><td>{{ row[3] }}</td>
            <td>{{ row[4] }}</td><td>{{ row[5] }}</td><td>{{ row[6] }}</td><td>{{ row[7] }}</td>
            <td>{{ row[8] }}</td><td>{{ row[9] }}</td><td><a href='/edit/{{ row[0] }}' class='btn btn-sm btn-warning'>Modifier</a> <a href='/delete/{{ row[0] }}' class='btn btn-sm btn-danger' onclick="return confirm('Confirmer la suppression ?')">Supprimer</a></td>
        </tr>
        {% endfor %}
        </tbody>
    </table>

    <h5 class='mt-5'>Historique des affectations</h5>
    <table class='table table-sm table-bordered'>
        <thead class='table-secondary'><tr><th>Poste</th><th>Utilisateur</th><th>Département</th><th>Date</th></tr></thead>
        <tbody>
        {% for m in movements %}
        <tr><td>{{ m[0] }}</td><td>{{ m[1] }}</td><td>{{ m[2] }}</td><td>{{ m[3] }}</td></tr>
        {% endfor %}
        </tbody>
    </table>
</div>

<script>
const deptChart = new Chart(document.getElementById('deptChart'), {
    type: 'bar',
    data: { labels: {{ dept_labels }}, datasets: [{ label: 'Par département', data: {{ dept_data }}, backgroundColor: 'rgba(54,162,235,0.6)' }] }
});
const typeChart = new Chart(document.getElementById('typeChart'), {
    type: 'pie',
    data: { labels: {{ type_labels }}, datasets: [{ label: 'Types', data: {{ type_data }}, backgroundColor: ['#36A2EB','#FF6384','#FFCE56','#4BC0C0','#9966FF','#FF9F40'] }] }
});
</script>
</body>
</html>
"""

# ==================== ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            error = "Identifiants incorrects."
    return render_template_string(login_template, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    with sqlite3.connect("inventory.db") as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM computers ORDER BY id DESC")
        rows = c.fetchall()
        df = pd.read_sql_query("SELECT * FROM computers", conn)
        m = conn.cursor()
        m.execute("""
            SELECT c.name, mv.user, mv.department, mv.date
            FROM movements mv
            JOIN computers c ON mv.computer_id = c.id
            ORDER BY mv.date DESC
        """)
        movements = m.fetchall()

    dept_data = df['department'].value_counts()
    type_data = df['type'].value_counts()

    return render_template_string(
        dashboard_template,
        rows=rows,
        dept_labels=list(dept_data.index),
        dept_data=list(dept_data.values),
        type_labels=list(type_data.index),
        type_data=list(type_data.values),
        movements=movements
    )

@app.route('/add', methods=['POST'])
def add():
    data = (
        request.form['name'],
        request.form['type'],
        request.form['department'],
        request.form['user'],
        request.form['purchase_date'],
        request.form['status'],
        request.form['serial_number'],
        request.form['antivirus'],
        request.form['domain_joined']
    )
    with sqlite3.connect("inventory.db") as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO computers (name, type, department, user, purchase_date, status, serial_number, antivirus, domain_joined)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", data)
        conn.commit()
        # Get ID and insert movement
        cid = c.lastrowid
        c.execute("""
            INSERT INTO movements (computer_id, user, department, date)
            VALUES (?, ?, ?, ?)""", (cid, data[3], data[2], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/export')
def export():
    with sqlite3.connect("inventory.db") as conn:
        df = pd.read_sql_query("SELECT * FROM computers", conn)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    filename = f"mecpip_inventory_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return send_file(output, download_name=filename, as_attachment=True)


@app.route('/edit/<int:cid>', methods=['GET', 'POST'])
def edit(cid):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    with sqlite3.connect("inventory.db") as conn:
        c = conn.cursor()
        if request.method == 'POST':
            data = (
                request.form['name'],
                request.form['type'],
                request.form['department'],
                request.form['user'],
                request.form['purchase_date'],
                request.form['status'],
                request.form['serial_number'],
                request.form['antivirus'],
                request.form['domain_joined'],
                cid
            )
            c.execute("""
                UPDATE computers SET name=?, type=?, department=?, user=?, purchase_date=?, status=?, serial_number=?, antivirus=?, domain_joined=? WHERE id=?
            """, data)
            conn.commit()
            return redirect(url_for('dashboard'))
        else:
            c.execute("SELECT * FROM computers WHERE id=?", (cid,))
            item = c.fetchone()
            if not item:
                return "Introuvable", 404
    return f"""
    <form method='post' style='margin:2rem; max-width:800px;'>
        <div class='row g-2'>
            <div class='col-md-4'><label>Nom du poste</label><input type='text' name='name' class='form-control' value='{0}' required></div>
            <div class='col-md-4'><label>Type</label>
                <select name='type' class='form-control'>
                    <option {1}>Laptop</option><option {2}>Desktop</option>
                    <option {3}>Imprimante</option><option {4}>Scanner</option>
                    <option {5}>Copieur</option><option {6}>Projecteur</option>
                    <option {7}>Écran</option><option {8}>Onduleur</option>
                    <option {9}>Serveur</option><option {10}>Switch</option>
                    <option {11}>Routeur</option><option {12}>Pare-Feu</option>
                </select>
            </div>
            <div class='col-md-4'><label>Département</label><input type='text' name='department' class='form-control' value='{13}' required></div>
            <div class='col-md-4'><label>Utilisateur</label><input type='text' name='user' class='form-control' value='{14}' required></div>
            <div class='col-md-4'><label>Date Date achat</label><input type='date' name='purchase_date' class='form-control' value='{15}' required></div>
            <div class='col-md-4'><label>Numéro de série</label><input type='text' name='serial_number' class='form-control' value='{16}'></div>
            <div class='col-md-2'><label>Statut</label><select name='status' class='form-control'><option {17}>Actif</option><option {18}>HS</option></select></div>
            <div class='col-md-2'><label>Antivirus</label><select name='antivirus' class='form-control'><option {19}>Oui</option><option {20}>Non</option></select></div>
            <div class='col-md-2'><label>Domaine</label><select name='domain_joined' class='form-control'><option {21}>Oui</option><option {22}>Non</option></select></div>
        </div>
        <div class='mt-3'>
            <button class='btn btn-primary'>Enregistrer</button>
            <a href='/' class='btn btn-secondary'>Annuler</a>
        </div>
    </form>
""".format(
        item[1],  # name
        'selected' if item[2]=='Laptop' else '',
        'selected' if item[2]=='Desktop' else '',
        'selected' if item[2]=='Imprimante' else '',
        'selected' if item[2]=='Scanner' else '',
        'selected' if item[2]=='Copieur' else '',
        'selected' if item[2]=='Projecteur' else '',
        'selected' if item[2]=='Écran' else '',
        'selected' if item[2]=='Onduleur' else '',
        'selected' if item[2]=='Serveur' else '',
        'selected' if item[2]=='Switch' else '',
        'selected' if item[2]=='Routeur' else '',
        'selected' if item[2]=='Pare-Feu' else '',
        item[3],  # department
        item[4],  # user
        item[5],  # purchase_date
        item[7],  # serial_number
        'selected' if item[6]=='Actif' else '',
        'selected' if item[6]=='HS' else '',
        'selected' if item[8]=='Oui' else '',
        'selected' if item[8]=='Non' else '',
        'selected' if item[9]=='Oui' else '',
        'selected' if item[9]=='Non' else ''
    )

@app.route('/delete/<int:cid>')
def delete(cid):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    with sqlite3.connect("inventory.db") as conn:
        c = conn.cursor()
        c.execute("DELETE FROM computers WHERE id=?", (cid,))
        conn.commit()
    return redirect(url_for('dashboard'))



@app.route('/export_pdf')
def export_pdf():
    from fpdf import FPDF
    import os

    class PDF(FPDF):
        def header(self):
            logo_path = os.path.join("static", "logo.jpg")
            if os.path.exists(logo_path):
                self.image(logo_path, 10, 8, 33)
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, "Inventaire Informatique - MECPIP", ln=1, align="C")
            self.set_font("Arial", "", 10)
            self.cell(0, 10, f"Date de génération : {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1, align="C")
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
            for row in data:
                for i in range(len(headers)):
                    self.cell(col_widths[i], 6, str(row[i])[:25], border=1)
                self.ln()

    with sqlite3.connect("inventory.db") as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, type, department, user, purchase_date, status, serial_number, antivirus, domain_joined FROM computers ORDER BY id")
        rows = c.fetchall()

    pdf = PDF()
    pdf.add_page()
    pdf.table(rows)
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return send_file(output, download_name="Inventaire_MECPIP.pdf", as_attachment=True)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
