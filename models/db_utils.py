from models.user import db, User
from models.connection_log import ConnectionLog
from models.simulation_session import SimulationSession
from sqlalchemy import func


def get_all_users():
    return User.query.order_by(User.created_at.desc()).all()


def get_user_count():
    return User.query.count()


def get_connections_by_country():
    """Retourne le nombre de connexions par pays."""
    return (db.session.query(
                ConnectionLog.country,
                func.count(ConnectionLog.id).label('total'))
            .group_by(ConnectionLog.country)
            .order_by(func.count(ConnectionLog.id).desc())
            .all())


def get_simulation_count():
    return SimulationSession.query.count()


def get_recent_connections(limit=20):
    return (ConnectionLog.query
            .order_by(ConnectionLog.connected_at.desc())
            .limit(limit).all())


def get_model_usage_stats():
    """Statistiques d'utilisation des modèles thermodynamiques."""
    return (db.session.query(
                SimulationSession.model_used,
                func.count(SimulationSession.id).label('total'))
            .group_by(SimulationSession.model_used)
            .order_by(func.count(SimulationSession.id).desc())
            .all())


def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return True
    return False