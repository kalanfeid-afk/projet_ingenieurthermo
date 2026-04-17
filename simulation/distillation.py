import math
from simulation.molecule import MOLECULE_DATA


def flash_rachford_rice(z, K, max_iter=100, tol=1e-8):
    """
    Résout l'équation de Rachford-Rice pour un flash biphasique.
    Σ z_i(K_i - 1) / (1 + V(K_i - 1)) = 0

    Paramètres
    ----------
    z : list — fractions molaires alimentation [z1, z2]
    K : list — constantes d'équilibre [K1, K2]

    Retourne
    --------
    V : float — fraction vapeur
    x : list  — compositions liquide
    y : list  — compositions vapeur
    """
    try:
        V_min = max(1 / (1 - max(K)), 0.0) + 1e-6
        V_max = min(1 / (1 - min(K)), 1.0) - 1e-6
        if V_min >= V_max:
            V_min, V_max = 0.001, 0.999
        V = (V_min + V_max) / 2

        for _ in range(max_iter):
            f  = sum(z[i] * (K[i] - 1) / (1 + V * (K[i] - 1)) for i in range(len(z)))
            df = -sum(z[i] * (K[i] - 1) ** 2 / (1 + V * (K[i] - 1)) ** 2 for i in range(len(z)))
            V_new = V - f / df if df != 0 else V
            V_new = max(V_min, min(V_max, V_new))
            if abs(V_new - V) < tol:
                break
            V = V_new

        x     = [z[i] / (1 + V * (K[i] - 1)) for i in range(len(z))]
        y     = [K[i] * x[i] for i in range(len(z))]
        sum_x = sum(x)
        sum_y = sum(y)
        x     = [xi / sum_x for xi in x]
        y     = [yi / sum_y for yi in y]

        return round(V, 6), [round(xi, 6) for xi in x], [round(yi, 6) for yi in y]

    except Exception:
        return 0.5, [z[0], z[1]], [z[0], z[1]]


class DistillationSimulator:
    """
    Simule une colonne de distillation à n plateaux théoriques.
    Méthode : calcul plateau par plateau (équilibre liquide-vapeur).
    """

    def __init__(self, composant_1, composant_2, T_feed, P,
                 z_feed=0.5, n_plateaux=10, taux_reflux=2.0):
        self.c1 = composant_1
        self.c2 = composant_2
        self.d1 = MOLECULE_DATA[composant_1]
        self.d2 = MOLECULE_DATA[composant_2]
        self.T  = T_feed
        self.P  = P
        self.z  = z_feed
        self.N  = n_plateaux
        self.R  = taux_reflux

    def _Psat(self, data, T):
        Tc, Pc, omega = data['Tc'], data['Pc'], data['omega']
        Tr = T / Tc
        if Tr >= 1.0:
            return Pc
        try:
            f0 = 5.92714 - 6.09648 / Tr - 1.28862 * math.log(Tr) + 0.169347 * Tr ** 6
            f1 = 15.2518 - 15.6875 / Tr - 13.4721 * math.log(Tr) + 0.43577 * Tr ** 6
            return math.exp(f0 + omega * f1) * Pc
        except (ValueError, OverflowError):
            return Pc

    def _K(self, data, T):
        Psat = self._Psat(data, T)
        return Psat / self.P if self.P > 0 else 1.0

    def temperature_bulle(self, x1, tol=1e-4, max_iter=50):
        """Température de bulle par Newton-Raphson."""
        T = self.T
        for _ in range(max_iter):
            K1 = self._K(self.d1, T)
            K2 = self._K(self.d2, T)
            f  = x1 * K1 + (1 - x1) * K2 - 1.0
            dT  = 0.1
            K1b = self._K(self.d1, T + dT)
            K2b = self._K(self.d2, T + dT)
            df  = (x1 * K1b + (1 - x1) * K2b - 1.0 - f) / dT
            if abs(df) < 1e-12:
                break
            T_new = T - f / df
            T_new = max(250.0, min(700.0, T_new))
            if abs(T_new - T) < tol:
                T = T_new
                break
            T = T_new
        return round(T, 3)

    def simuler(self):
        plateaux = []
        x1       = self.z

        for n in range(1, self.N + 1):
            T_plat = self.temperature_bulle(x1)
            K1     = self._K(self.d1, T_plat)
            K2     = self._K(self.d2, T_plat)

            V_frac, x_liq, y_vap = flash_rachford_rice(
                [x1, 1 - x1], [K1, K2]
            )

            alpha_12 = round(K1 / K2, 4) if K2 > 0 else None

            plateaux.append({
                'plateau':  n,
                'T':        T_plat,
                'x1':       round(x_liq[0], 4),
                'x2':       round(x_liq[1], 4),
                'y1':       round(y_vap[0], 4),
                'y2':       round(y_vap[1], 4),
                'V_frac':   round(V_frac,   4),
                'K1':       round(K1, 4),
                'K2':       round(K2, 4),
                'alpha_12': alpha_12,
            })

            x1 = max(0.001, min(0.999, x_liq[0]))

        distillat  = plateaux[-1]['y1']
        residu     = plateaux[0]['x1']
        separation = round((distillat - residu) / (self.z + 1e-9) * 100, 2)

        return {
            'composant_1':     self.c1,
            'composant_2':     self.c2,
            'n_plateaux':      self.N,
            'taux_reflux':     self.R,
            'z_alimentation':  self.z,
            'x_residu':        residu,
            'y_distillat':     distillat,
            'efficacite_sep':  separation,
            'profil_plateaux': plateaux,
        }