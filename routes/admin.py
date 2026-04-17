from flask import Blueprint, render_template, jsonify
from auth.utils import admin_required
from models.user import db, User
from models.connection_log import ConnectionLog
from models.simulation_session import SimulationSession
from models.db_utils import (get_all_users, get_user_count,
                              get_connections_by_country,
                              get_simulation_count,
                              get_recent_connections,
                              get_model_usage_stats,
                              delete_user)
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')


@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    users       = get_all_users()
    countries   = get_connections_by_country()
    model_stats = get_model_usage_stats()
    connections = get_recent_connections(30)
    recent_sims = (SimulationSession.query
                   .order_by(SimulationSession.created_at.desc())
                   .limit(30).all())

    # Enrichir connexions avec username
    conn_list = []
    for c in connections:
        conn_list.append({
            **c.to_dict(),
            'username': c.user.username if c.user else '—'
        })

    # Enrichir simulations avec username
    sim_list = []
    for s in recent_sims:
        d = s.to_dict()
        d['username'] = s.user.username if s.user else '—'
        sim_list.append(d)

    return jsonify({
        'users_count':        get_user_count(),
        'simulations_count':  get_simulation_count(),
        'connections_count':  ConnectionLog.query.count(),
        'users':              [u.to_dict() for u in users],
        'countries':          [{'country': c[0], 'count': c[1]} for c in countries],
        'model_stats':        [{'model': m[0], 'count': m[1]} for m in model_stats],
        'recent_connections': conn_list,
        'recent_simulations': sim_list,
    })


@admin_bp.route('/api/delete_user/<int:user_id>', methods=['DELETE'])
@admin_required
def api_delete_user(user_id):
    from flask import session
    if user_id == session.get('user_id'):
        return jsonify({'success': False, 'error': 'Impossible de se supprimer soi-même.'})
    success = delete_user(user_id)
    return jsonify({'success': success})