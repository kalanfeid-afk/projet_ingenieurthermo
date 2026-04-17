from functools import wraps
from flask import session, redirect, url_for, flash, request
from datetime import datetime


def login_required(f):
    """Décorateur : redirige vers login si non connecté."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Décorateur : accès réservé aux administrateurs."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter.', 'warning')
            return redirect(url_for('auth.login'))
        if not session.get('is_admin'):
            flash('Accès refusé. Droits administrateur requis.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def log_connection(user_id, request_obj):
    """Enregistre la connexion (IP, timestamp) en base."""
    try:
        from models.user import db
        from models.connection_log import ConnectionLog

        ip = (request_obj.headers.get('X-Forwarded-For', request_obj.remote_addr)
              or '0.0.0.0')
        ip = ip.split(',')[0].strip()  # Prend la première IP si proxy

        log = ConnectionLog(
            user_id=user_id,
            ip_address=ip,
            connected_at=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"[Warning] Impossible de logger la connexion : {e}")


def get_current_user():
    """Retourne l'utilisateur connecté depuis la session."""
    from models.user import User
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None