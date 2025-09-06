from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
from models import get_db, init_db
from train_model import predict_with_models, retrain_models_if_missing

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-this-secret")
DB_PATH = os.path.join(app.root_path, 'data', 'emails.db')

init_db(DB_PATH)
retrain_models_if_missing(DB_PATH, app.root_path)


def is_admin():
    return session.get('admin_logged_in')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/check', methods=['POST'])
def check_message():
    text = request.form.get('message', '').strip()
    if not text:
        flash('Please provide message text', 'warning')
        return redirect(url_for('index'))
    results = predict_with_models(text, DB_PATH, app.root_path)
    votes = [1 if v['label'] == 'spam' else 0 for v in results['models'].values()]
    spam_votes = sum(votes)
    final_label = 'spam' if spam_votes >= 2 else 'inbox'
    results['final'] = final_label
    return render_template('result.html', text=text, results=results)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        conn = get_db(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT password_hash FROM admin WHERE username=?', (user,))
        row = cur.fetchone()
        if row and row['password_hash'] == pwd:
            session['admin_logged_in'] = True
            session['admin_user'] = user
            flash('Logged in', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('index'))


@app.route('/admin')
def admin_dashboard():
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, text, label FROM emails ORDER BY id DESC LIMIT 500')
    rows = cur.fetchall()
    return render_template('admin_dashboard.html', rows=rows)


@app.route('/admin/add', methods=['GET', 'POST'])
def admin_add():
    if not is_admin():
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        label = request.form.get('label', 'ham')
        if text:
            conn = get_db(DB_PATH)
            cur = conn.cursor()
            cur.execute('INSERT INTO emails (text, label) VALUES (?, ?)', (text, label))
            conn.commit()
            flash('Added', 'success')
            return redirect(url_for('admin_dashboard'))
    return render_template('admin_edit.html', row=None)


@app.route('/admin/edit/<int:email_id>', methods=['GET', 'POST'])
def admin_edit(email_id):
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db(DB_PATH)
    cur = conn.cursor()
    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        label = request.form.get('label', 'ham')
        cur.execute('UPDATE emails SET text=?, label=? WHERE id=?', (text, label, email_id))
        conn.commit()
        flash('Saved', 'success')
        return redirect(url_for('admin_dashboard'))
    cur.execute('SELECT id, text, label FROM emails WHERE id=?', (email_id,))
    row = cur.fetchone()
    return render_template('admin_edit.html', row=row)


@app.route('/admin/delete/<int:email_id>', methods=['POST'])
def admin_delete(email_id):
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db(DB_PATH)
    cur = conn.cursor()
    cur.execute('DELETE FROM emails WHERE id=?', (email_id,))
    conn.commit()
    flash('Deleted', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/api', methods=['GET', 'POST'])
def admin_api_keys():
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db(DB_PATH)
    cur = conn.cursor()
    if request.method == 'POST':
        api_url = request.form.get('api_url', '').strip()
        api_token = request.form.get('api_token', '').strip()
        cur.execute('UPDATE admin SET api_url=?, api_token=? WHERE username=?',
                    (api_url, api_token, session.get('admin_user')))
        conn.commit()
        flash('API info saved', 'success')
    cur.execute('SELECT api_url, api_token FROM admin WHERE username=?', (session.get('admin_user'),))
    row = cur.fetchone()
    return render_template('api_keys.html', row=row)


@app.route('/admin/api/send-test', methods=['POST'])
def admin_api_send_test():
    if not is_admin():
        return jsonify({'error': 'not authorized'}), 403
    return jsonify({'status': 'ok', 'message': 'Would send payload to configured API'})


if __name__ == '__main__':
    app.run(debug=True)
