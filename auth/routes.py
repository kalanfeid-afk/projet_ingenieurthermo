from flask import render_template, redirect, url_for, flash, session, request
from datetime import datetime
from . import auth_bp
from models.user import db, User
from .utils import login_required, log_connection


# ─── INSCRIPTION ──────────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        # Validations
        if not username or not email or not password:
            flash('Tous les champs sont obligatoires.', 'danger')
            return render_template('auth/register.html')

        if password != confirm:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Un compte avec cet email existe déjà.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur est déjà pris.", 'danger')
            return render_template('auth/register.html')

        # Création de l'utilisateur
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Compte créé avec succès ! Vous pouvez vous connecter.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# ─── CONNEXION ────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Email ou mot de passe incorrect.', 'danger')
            return render_template('auth/login.html')

        # Ouvrir la session
        session.permanent = True
        session['user_id']   = user.id
        session['username']  = user.username
        session['is_admin']  = user.is_admin
        session['login_time'] = datetime.utcnow().isoformat()

        # Mettre à jour last_login
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Logger la connexion (IP, timestamp)
        log_connection(user.id, request)

        flash(f'Bienvenue, {user.username} !', 'success')

        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.dashboard'))

    return render_template('auth/login.html')


# ─── DÉCONNEXION ──────────────────────────────────────────────────────────────

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.login'))