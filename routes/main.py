from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from auth.utils import login_required
from models.simulation_session import SimulationSession

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session.get('username'))

@main_bp.route('/simulation')
@login_required
def simulation():
    return render_template('simulation.html')

@main_bp.route('/api/history')
@login_required
def history():
    sessions = (SimulationSession.query
                .filter_by(user_id=session['user_id'])
                .order_by(SimulationSession.created_at.desc())
                .limit(20).all())
    return jsonify({'sessions': [s.to_dict() for s in sessions]})