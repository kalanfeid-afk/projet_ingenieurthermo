from datetime import datetime
from models.user import db

class ConnectionLog(db.Model):
    __tablename__ = 'connection_logs'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ip_address   = db.Column(db.String(45))   # IPv4 ou IPv6
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='connections')

    def __repr__(self):
        return f"<ConnectionLog user={self.user_id} ip={self.ip_address}>"