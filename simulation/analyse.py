import math


def fenske(alpha_moy, x_distillat, x_residu):
    """
    Calcule le nombre minimum de plateaux (Fenske).
    alpha_moy   : sélectivité relative moyenne α₁₂
    x_distillat : fraction molaire composant léger en tête
    x_residu    : fraction molaire composant léger en fond
    """
    if alpha_moy is None or alpha_moy <= 1.0:
        return None
    if x_distillat is None or x_distillat >= 1.0:
        return None
    if x_residu is None or x_residu <= 0.0:
        return None

    try:
        Nmin = (math.log((x_distillat / (1 - x_distillat)) *
                         ((1 - x_residu) / x_residu))
                / math.log(alpha_moy))
        return round(Nmin, 2)
    except (ZeroDivisionError, ValueError):
        return None


def underwood(alpha, z_feed, q=1.0):
    """
    Calcule le reflux minimum (Underwood) pour un système binaire.
    alpha  : sélectivité relative α₁₂
    z_feed : fraction molaire alimentation composant léger
    q      : qualité alimentation (1 = liquide saturé)
    """
    if alpha is None or alpha <= 1.0:
        return None
    if z_feed is None or not (0 < z_feed < 1):
        return None

    try:
        from scipy.optimize import brentq

        def f(theta):
            return (alpha * z_feed / (alpha - theta)
                    + (1 - z_feed) / (1 - theta) - (1 - q))

        theta  = brentq(f, 1.0 + 1e-6, alpha - 1e-6)
        Lmin_D = alpha * (z_feed / (alpha - theta)) - 1
        return round(max(Lmin_D, 0), 3)
    except Exception:
        return None


def gilliland(Nmin, Rmin, R):
    """
    Corrélation de Gilliland pour estimer N à partir de Nmin et Rmin.
    Retourne le nombre de plateaux estimé.
    """
    if Nmin is None or Rmin is None:
        return None
    if R is None or R <= Rmin:
        return None

    try:
        X = (R - Rmin) / (R + 1)
        if X <= 0:
            return None
        Y = 1 - math.exp((1 + 54.4 * X) / (11 + 117.2 * X) * (X - 1) / X ** 0.5)
        N = (Nmin + Y) / (1 - Y)
        return round(N, 1)
    except (ZeroDivisionError, ValueError):
        return None


def recommandations(profil):
    """
    Génère des recommandations automatiques selon les résultats de simulation.
    Retourne une liste de dicts : {type, titre, message}
    """
    conseils  = []
    plateaux  = profil.get('profil_plateaux', [])

    if not plateaux:
        return conseils

    # ── Sélectivité relative ──────────────────────────────────────────
    alpha_vals = [p['alpha_12'] for p in plateaux if p.get('alpha_12') is not None]
    alpha_moy  = sum(alpha_vals) / len(alpha_vals) if alpha_vals else None

    if alpha_moy is not None:
        if alpha_moy < 1.5:
            conseils.append({
                'type':    'warning',
                'titre':   'Sélectivité faible',
                'message': (f'α₁₂ moyen = {alpha_moy:.2f}. '
                            'La séparation sera difficile. '
                            'Augmentez le nombre de plateaux ou le taux de reflux.')
            })
        elif alpha_moy > 5:
            conseils.append({
                'type':    'success',
                'titre':   'Bonne sélectivité',
                'message': (f'α₁₂ moyen = {alpha_moy:.2f}. '
                            'La séparation est favorable. '
                            'Vous pouvez réduire le nombre de plateaux pour économiser de l\'énergie.')
            })

    # ── Efficacité de séparation ──────────────────────────────────────
    eff = profil.get('efficacite_sep')
    if eff is not None:
        if eff < 50:
            conseils.append({
                'type':    'danger',
                'titre':   'Efficacité insuffisante',
                'message': (f'Séparation à {eff}%. '
                            'Augmentez le taux de reflux ou le nombre de plateaux.')
            })
        elif eff > 90:
            conseils.append({
                'type':    'success',
                'titre':   'Excellente séparation',
                'message': (f'Séparation à {eff}%. '
                            'Les conditions opératoires sont optimales.')
            })

    # ── Fraction vapeur moyenne ───────────────────────────────────────
    V_vals = [p['V_frac'] for p in plateaux if p.get('V_frac') is not None]
    if V_vals:
        V_moy = sum(V_vals) / len(V_vals)
        if V_moy > 0.8:
            conseils.append({
                'type':    'warning',
                'titre':   'Fraction vapeur élevée',
                'message': (f'V_frac moyen = {V_moy:.2f}. '
                            'Réduisez la température ou augmentez la pression.')
            })

    # ── Nmin / N_estime ───────────────────────────────────────────────
    Nmin    = profil.get('Nmin')
    N_estime = profil.get('N_estime')
    N_reel   = profil.get('n_plateaux')

    if Nmin is not None and N_reel is not None:
        if N_reel < Nmin:
            conseils.append({
                'type':    'danger',
                'titre':   'Nombre de plateaux insuffisant',
                'message': (f'Nmin = {Nmin} plateaux requis, '
                            f'vous en avez {N_reel}. '
                            'La séparation ne peut pas être atteinte.')
            })
        elif N_estime is not None and N_reel >= N_estime * 1.5:
            conseils.append({
                'type':    'info',
                'titre':   'Surdimensionnement possible',
                'message': (f'Nmin estimé = {N_estime} plateaux, '
                            f'vous en utilisez {N_reel}. '
                            'Vous pouvez réduire le nombre de plateaux.')
            })

    return conseils