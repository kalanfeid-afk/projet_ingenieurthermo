from flask import Blueprint, request, jsonify, session
from auth.utils import login_required
from simulation.molecule import MoleculeTracker
from simulation.distillation import DistillationSimulator
from simulation.analyse import recommandations, fenske, underwood, gilliland
from models.user import db
from models.simulation_session import SimulationSession

sim_bp = Blueprint('simulation', __name__, url_prefix='/api')


@sim_bp.route('/simulate', methods=['POST'])
@login_required
def simulate():
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'Aucune donnée reçue.'}), 400

    try:
        # ── Lecture des paramètres ────────────────────────────────────
        c1       = data.get('composant_1', '')
        c2       = data.get('composant_2', '')
        T        = float(data.get('temperature', 351))
        P        = float(data.get('pression', 101325))
        z        = float(data.get('fraction_alim', 0.5))
        n_plat   = int(data.get('n_plateaux', 10))
        miscible = bool(data.get('miscible', True))
        R        = float(data.get('taux_reflux', 2.0))

        # ── Validation de base ────────────────────────────────────────
        if not c1 or not c2:
            return jsonify({'success': False, 'error': 'Composants manquants.'}), 400
        if T <= 0 or P <= 0:
            return jsonify({'success': False, 'error': 'T et P doivent être positifs.'}), 400
        if not (0 < z < 1):
            return jsonify({'success': False, 'error': 'La fraction molaire doit être entre 0 et 1.'}), 400

        # ── Suivi molécule ────────────────────────────────────────────
        tracker = MoleculeTracker(c1, c2, T, P, z, miscible)
        etat    = tracker.calculer_etat()
        traj    = tracker.trajectoire_colonne(n_plat)

        # ── Simulation distillation ───────────────────────────────────
        distil  = DistillationSimulator(c1, c2, T, P, z, n_plat, R)
        profil  = distil.simuler()

        # ── Calculs d'analyse (Fenske / Underwood / Gilliland) ────────
        alpha_vals = [
            p['alpha_12'] for p in profil['profil_plateaux']
            if p.get('alpha_12') is not None   # is not None — évite d'exclure 0
        ]
        alpha_moy = sum(alpha_vals) / len(alpha_vals) if alpha_vals else None

        if alpha_moy is not None and alpha_moy > 1.0:
            Nmin  = fenske(alpha_moy, profil['y_distillat'], profil['x_residu'])
            Rmin  = underwood(alpha_moy, profil['z_alimentation'])
            N_est = gilliland(Nmin, Rmin, profil.get('taux_reflux', R))
        else:
            Nmin  = None
            Rmin  = None
            N_est = None

        profil['Nmin']      = Nmin
        profil['Rmin']      = Rmin
        profil['N_estime']  = N_est
        profil['alpha_moy'] = round(alpha_moy, 4) if alpha_moy else None

        # ── Recommandations automatiques ──────────────────────────────
        conseils = recommandations(profil)

        # ── Sauvegarde en base de données ─────────────────────────────
        sim_session = SimulationSession(
            user_id       = session['user_id'],
            component_1   = c1,
            component_2   = c2,
            temperature   = T,
            pressure      = P,
            feed_fraction = z,
            phase         = etat['phase'],
            model_used    = etat['modele']
        )
        sim_session.set_results({'etat': etat, 'profil': profil})
        db.session.add(sim_session)
        db.session.commit()

        # ── Réponse JSON ──────────────────────────────────────────────
        return jsonify({
            'success':         True,
            'etat':            etat,
            'trajectoire':     traj,
            'distillation':    profil,
            'recommandations': conseils,
            'session_id':      sim_session.id
        })

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erreur serveur : {str(e)}'}), 500


@sim_bp.route('/molecules', methods=['GET'])
def get_molecules():
    """Retourne la liste des molécules disponibles."""
    from simulation.molecule import MOLECULE_DATA
    return jsonify({
        'molecules': [
            {'nom': nom, 'formule': d['formule'], 'polaire': d['polaire']}
            for nom, d in MOLECULE_DATA.items()
        ]
    })


@sim_bp.route('/history', methods=['GET'])
@login_required
def history():
    """Retourne l'historique des simulations de l'utilisateur."""
    sessions = (SimulationSession.query
                .filter_by(user_id=session['user_id'])
                .order_by(SimulationSession.created_at.desc())
                .limit(20).all())
    return jsonify({'sessions': [s.to_dict() for s in sessions]})