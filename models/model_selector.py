from .eos_models import VanDerWaals, PengRobinson
from .thermo_models import Wilson, NRTL


# ─────────────────────────────────────────────
#  Règles de sélection automatique du modèle
# ─────────────────────────────────────────────
#
#  Phase gazeuse / haute pression  → EOS (VdW ou PR)
#  Phase liquide / coefficients γ  → Wilson ou NRTL
#
#  Priorité :
#    1. Pression élevée (> 10 bar)  + gaz     → Peng-Robinson
#    2. Pression modérée            + gaz     → Van der Waals
#    3. Système polaire miscible    + liquide → Wilson
#    4. Système partiellement miscible        → NRTL
#    5. Défaut                                → Peng-Robinson


def select_model(phase, T, P, polaire=False, miscible=True):
    """
    Sélectionne automatiquement le modèle thermodynamique adapté.

    Paramètres
    ----------
    phase    : str  — 'gaz', 'liquide', ou 'biphasique'
    T        : float — Température (K)
    P        : float — Pression (Pa)
    polaire  : bool  — True si au moins un composant est polaire
    miscible : bool  — True si les composants sont miscibles

    Retourne
    --------
    str : nom du modèle recommandé
    dict: critères ayant mené à la décision
    """
    P_bar = P / 1e5  # conversion Pa → bar
    raisons = {}

    # ── Cas 1 : Phase gazeuse haute pression ──────────────────────────
    if phase == 'gaz' and P_bar > 10:
        raisons['modele'] = 'Peng-Robinson'
        raisons['justification'] = (
            f"Phase gazeuse à haute pression ({P_bar:.1f} bar). "
            "Peng-Robinson offre une meilleure précision que Van der Waals "
            "pour les gaz réels sous pression."
        )
        return 'Peng-Robinson', raisons

    # ── Cas 2 : Phase gazeuse basse/moyenne pression ──────────────────
    if phase == 'gaz' and P_bar <= 10:
        raisons['modele'] = 'Van der Waals'
        raisons['justification'] = (
            f"Phase gazeuse à pression modérée ({P_bar:.1f} bar). "
            "Van der Waals est suffisant pour modéliser les déviations "
            "au comportement idéal."
        )
        return 'Van der Waals', raisons

    # ── Cas 3 : Phase liquide — miscible et polaire ────────────────────
    if phase in ('liquide', 'biphasique') and polaire and miscible:
        raisons['modele'] = 'Wilson'
        raisons['justification'] = (
            "Système liquide polaire et miscible (ex: éthanol-eau). "
            "Le modèle de Wilson est recommandé pour les mélanges "
            "polaires entièrement miscibles."
        )
        return 'Wilson', raisons

    # ── Cas 4 : Phase liquide — partiellement miscible ─────────────────
    if phase in ('liquide', 'biphasique') and not miscible:
        raisons['modele'] = 'NRTL'
        raisons['justification'] = (
            "Système partiellement miscible ou présentant une séparation "
            "de phase liquide-liquide. NRTL (Non-Random Two-Liquid) est "
            "conçu pour ces systèmes."
        )
        return 'NRTL', raisons

    # ── Cas 5 : Défaut ─────────────────────────────────────────────────
    raisons['modele'] = 'Peng-Robinson'
    raisons['justification'] = (
        "Modèle par défaut. Peng-Robinson est robuste et applicable "
        "à un large éventail de conditions."
    )
    return 'Peng-Robinson', raisons


def instancier_modele(nom_modele, params):
    """
    Instancie le modèle thermodynamique à partir de son nom.

    Paramètres
    ----------
    nom_modele : str  — 'Van der Waals', 'Peng-Robinson', 'Wilson', 'NRTL'
    params     : dict — paramètres du modèle (voir exemples ci-dessous)

    Exemples params
    ---------------
    Van der Waals  : {'Tc': 304.2, 'Pc': 7.38e6}
    Peng-Robinson  : {'Tc': 304.2, 'Pc': 7.38e6, 'omega': 0.239}
    Wilson         : {'V_liquide': [58.1e-6, 18.0e-6], 'lambda_params': [[0,500],[300,0]]}
    NRTL           : {'tau_params': [[0,1.2],[-0.8,0]], 'alpha_params': [[0,0.3],[0.3,0]]}
    """
    if nom_modele == 'Van der Waals':
        return VanDerWaals(params['Tc'], params['Pc'])

    elif nom_modele == 'Peng-Robinson':
        return PengRobinson(params['Tc'], params['Pc'], params['omega'])

    elif nom_modele == 'Wilson':
        return Wilson(params['V_liquide'], params['lambda_params'])

    elif nom_modele == 'NRTL':
        return NRTL(params['tau_params'], params['alpha_params'])

    else:
        raise ValueError(f"Modèle inconnu : '{nom_modele}'. "
                         "Choisir parmi : Van der Waals, Peng-Robinson, Wilson, NRTL")