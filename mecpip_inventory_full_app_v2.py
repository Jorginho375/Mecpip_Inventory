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
<body style='background:#f5f5f5'>
    <div class='container d-flex justify-content-center align-items-center' style='height:100vh;'>
        <div class='card shadow p-4' style='min-width:350px;'>
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
        body {
            background: url('/static/bg.jpg') no-repeat center center fixed;
            background-size: cover;
        }
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
        <h3><img src='https://upload.wikimedia.org/wikipedia/commons/8/80/No-image-found.jpg' width='60'/> MECPIP - Gestion du Parc</h3>
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
        <div class='col-md-2'><input type='text' name='serial_number' class='form-control' placeholder='N° Série'></div>
        <div class='col-md-1'><select name='status' class='form-control'><option>Actif</option><option>HS</option></select></div>
        <div class='col-md-1'><select name='antivirus' class='form-control'><option>Oui</option><option>Non</option></select></div>
        <div class='col-md-1'><select name='domain_joined' class='form-control'><option>Oui</option><option>Non</option></select></div>
        <div class='col-md-1'><button class='btn btn-success w-100'>Ajouter</button></div>
    </form>

    <div class='row mb-4'>
        <div class='col-md-6'><canvas id='deptChart'></canvas></div>
        <div class='col-md-6'><canvas id='typeChart'></canvas></div>
    </div>

    <div class='d-flex justify-content-end mb-2'>
        <a href='/export' class='btn btn-outline-primary btn-sm'>Exporter Excel</a>
    </div>

    <h5 class='mt-4'>Liste des équipements</h5>
    <table class='table table-bordered table-striped'>
        <thead class='table-dark'><tr><th>#</th><th>Nom</th><th>Type</th><th>Département</th><th>Utilisateur</th><th>Achat</th><th>Statut</th><th>N° Série</th><th>Antivirus</th><th>Domaine</th></tr></thead>
        <tbody>
        {% for row in rows %}
        <tr>
            <td>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ row[2] }}</td><td>{{ row[3] }}</td>
            <td>{{ row[4] }}</td><td>{{ row[5] }}</td><td>{{ row[6] }}</td><td>{{ row[7] }}</td>
            <td>{{ row[8] }}</td><td>{{ row[9] }}</td>
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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
