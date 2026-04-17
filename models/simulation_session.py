from datetime import datetime
import json
from models.user import db


class SimulationSession(db.Model):
    __tablename__ = 'simulation_sessions'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    # Paramètres d'entrée
    component_1  = db.Column(db.String(100))
    component_2  = db.Column(db.String(100))
    temperature  = db.Column(db.Float)           # Kelvin
    pressure     = db.Column(db.Float)           # Pascal
    feed_fraction= db.Column(db.Float)           # fraction molaire composant 1
    phase        = db.Column(db.String(20))      # 'gaz', 'liquide', 'biphasique'

    # Modèle sélectionné
    model_used   = db.Column(db.String(50))      # 'Peng-Robinson', 'Wilson', etc.

    # Résultats (stockés en JSON)
    results_json = db.Column(db.Text, nullable=True)

    def set_results(self, results_dict):
        self.results_json = json.dumps(results_dict)

    def get_results(self):
        if self.results_json:
            return json.loads(self.results_json)
        return {}

    def to_dict(self):
        return {
            'id':           self.id,
            'user_id':      self.user_id,
            'created_at':   self.created_at.isoformat(),
            'component_1':  self.component_1,
            'component_2':  self.component_2,
            'temperature':  self.temperature,
            'pressure':     self.pressure,
            'feed_fraction':self.feed_fraction,
            'phase':        self.phase,
            'model_used':   self.model_used,
            'results':      self.get_results()
        }

    def __repr__(self):
        return f"<SimulationSession id={self.id} model={self.model_used}>"