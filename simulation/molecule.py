import math
from models.model_selector import select_model, instancier_modele

# ── Données moléculaires ─────────────────────────────────────────────────────
MOLECULE_DATA = {
    'ethanol':  {'Tc': 513.9, 'Pc': 6.14e6,  'omega': 0.644, 'V_liq': 58.1e-6,  'polaire': True,  'formule': 'C₂H₅OH'},
    'eau':      {'Tc': 647.1, 'Pc': 22.06e6, 'omega': 0.345, 'V_liq': 18.0e-6,  'polaire': True,  'formule': 'H₂O'},
    'benzene':  {'Tc': 562.2, 'Pc': 4.89e6,  'omega': 0.212, 'V_liq': 89.4e-6,  'polaire': False, 'formule': 'C₆H₆'},
    'toluene':  {'Tc': 591.8, 'Pc': 4.11e6,  'omega': 0.263, 'V_liq': 106.8e-6, 'polaire': False, 'formule': 'C₇H₈'},
    'acetone':  {'Tc': 508.1, 'Pc': 4.70e6,  'omega': 0.307, 'V_liq': 74.0e-6,  'polaire': True,  'formule': 'C₃H₆O'},
    'methanol': {'Tc': 512.6, 'Pc': 8.09e6,  'omega': 0.565, 'V_liq': 40.7e-6,  'polaire': True,  'formule': 'CH₃OH'},
}

# ── Paramètres Wilson réels (J/mol) ──────────────────────────────────────────
WILSON_PARAMS = {
    ('ethanol', 'eau'):     {'lambda_params': [[0, 1246.0], [591.2,  0]]},
    ('methanol', 'eau'):    {'lambda_params': [[0, 1025.0], [489.0,  0]]},
    ('acetone', 'eau'):     {'lambda_params': [[0, 1380.0], [642.0,  0]]},
}

# ── Paramètres NRTL réels ────────────────────────────────────────────────────
NRTL_PARAMS = {
    ('benzene', 'eau'):  {'tau_params': [[0, 3.82], [-2.15, 0]], 'alpha_params': [[0, 0.20], [0.20, 0]]},
    ('toluene', 'eau'):  {'tau_params': [[0, 4.10], [-2.30, 0]], 'alpha_params': [[0, 0.20], [0.20, 0]]},
}


class MoleculeTracker:
    """
    Suit le comportement d'une molécule dans un procédé de séparation.
    Calcule son état (phase, fugacité, coefficient d'activité) à chaque étage.
    """

    def __init__(self, composant_1, composant_2, T, P, fraction_alim=0.5, miscible=True):
        if composant_1 not in MOLECULE_DATA:
            raise ValueError(f"Composant '{composant_1}' inconnu. Disponibles : {list(MOLECULE_DATA.keys())}")
        if composant_2 not in MOLECULE_DATA:
            raise ValueError(f"Composant '{composant_2}' inconnu. Disponibles : {list(MOLECULE_DATA.keys())}")

        self.c1       = composant_1
        self.c2       = composant_2
        self.data1    = MOLECULE_DATA[composant_1]
        self.data2    = MOLECULE_DATA[composant_2]
        self.T        = T
        self.P        = P
        self.z        = fraction_alim
        self.miscible = miscible
        self.phase    = self._determiner_phase()

        polaire = self.data1['polaire'] or self.data2['polaire']
        self.nom_modele, self.raisons = select_model(
            self.phase, T, P, polaire=polaire, miscible=miscible
        )

    def _determiner_phase(self):
        """Estime la phase dominante selon T et Tc des composants."""
        Tc_moy = (self.data1['Tc'] + self.data2['Tc']) / 2
        Tr     = self.T / Tc_moy
        if Tr > 1.0:    return 'gaz'
        elif Tr < 0.85: return 'liquide'
        else:           return 'biphasique'

    def calculer_etat(self):
        """
        Calcule l'état complet de la molécule :
        - Facteur de compressibilité Z
        - Coefficients de fugacité φ
        - Coefficients d'activité γ (si liquide)
        - Constante d'équilibre K = y/x
        """
        resultats = {
            'composant_1':   self.c1,
            'composant_2':   self.c2,
            'temperature':   self.T,
            'pression':      self.P,
            'phase':         self.phase,
            'modele':        self.nom_modele,
            'justification': self.raisons['justification']
        }

        # ── Modèles EOS (gaz) ──────────────────────────────────────────
        if self.nom_modele in ('Van der Waals', 'Peng-Robinson'):
            for i, (nom, data) in enumerate([(self.c1, self.data1), (self.c2, self.data2)], 1):
                if self.nom_modele == 'Peng-Robinson':
                    params = {'Tc': data['Tc'], 'Pc': data['Pc'], 'omega': data['omega']}
                else:
                    params = {'Tc': data['Tc'], 'Pc': data['Pc']}

                modele       = instancier_modele(self.nom_modele, params)
                Z_v, Z_l     = modele.compressibility_factor(self.T, self.P)
                phi_v, phi_l = modele.fugacity_coefficient(self.T, self.P)

                resultats[f'Z_vapeur_c{i}']    = round(Z_v,   4)
                resultats[f'Z_liquide_c{i}']   = round(Z_l,   4)
                resultats[f'phi_vapeur_c{i}']  = round(phi_v, 4)
                resultats[f'phi_liquide_c{i}'] = round(phi_l, 4)
                K = phi_l / phi_v if phi_v > 0 else 1.0
                resultats[f'K_c{i}'] = round(K, 4)

        # ── Modèles d'activité (liquide) ───────────────────────────────
        elif self.nom_modele in ('Wilson', 'NRTL'):
            x   = [self.z, 1 - self.z]
            cle     = (self.c1, self.c2)
            cle_inv = (self.c2, self.c1)

            if self.nom_modele == 'Wilson':
                # Chercher paramètres réels, sinon utiliser génériques
                params_reels = WILSON_PARAMS.get(cle) or WILSON_PARAMS.get(cle_inv)
                params = {
                    'V_liquide':    [self.data1['V_liq'], self.data2['V_liq']],
                    'lambda_params': params_reels['lambda_params'] if params_reels
                                     else [[0, 500], [300, 0]]
                }
            else:  # NRTL
                params_reels = NRTL_PARAMS.get(cle) or NRTL_PARAMS.get(cle_inv)
                params = {
                    'tau_params':   params_reels['tau_params']   if params_reels else [[0, 1.2], [-0.8, 0]],
                    'alpha_params': params_reels['alpha_params'] if params_reels else [[0, 0.3], [0.3,  0]]
                }

            modele = instancier_modele(self.nom_modele, params)
            gamma  = modele.activity_coefficients(x, self.T)

            resultats['x1'] = round(x[0], 4)
            resultats['x2'] = round(x[1], 4)
            resultats[f'gamma_{self.c1}'] = round(gamma[0], 4)
            resultats[f'gamma_{self.c2}'] = round(gamma[1], 4)

            for i, (data, gam) in enumerate([(self.data1, gamma[0]), (self.data2, gamma[1])], 1):
                Psat = self._antoine_psat(data['Tc'], data['Pc'], data['omega'])
                K    = gam * Psat / self.P
                resultats[f'Psat_c{i}'] = round(Psat / 1000, 2)  # kPa
                resultats[f'K_c{i}']    = round(K, 4)

        return resultats

    def _antoine_psat(self, Tc, Pc, omega):
        """Estimation Psat via corrélation de Lee-Kesler (Pa)."""
        Tr = self.T / Tc
        if Tr >= 1.0:
            return Pc
        try:
            f0 = 5.92714 - 6.09648 / Tr - 1.28862 * math.log(Tr) + 0.169347 * Tr ** 6
            f1 = 15.2518 - 15.6875 / Tr - 13.4721 * math.log(Tr) + 0.43577 * Tr ** 6
            return math.exp(f0 + omega * f1) * Pc
        except (ValueError, OverflowError):
            return Pc

    def trajectoire_colonne(self, n_etages=10):
        """
        Simule la trajectoire de la molécule à travers n_etages.
        Retourne la liste des états (x, y, T) à chaque étage.
        """
        etages = []
        x = self.z

        for etage in range(1, n_etages + 1):
            T_etage = self.T - (etage - 1) * 2.0
            K1 = self._K_etage(self.data1, T_etage)
            K2 = self._K_etage(self.data2, T_etage)
            y1 = min(K1 * x, 1.0)
            y2 = 1.0 - y1
            x_new = x / (1 + (K1 - 1) * x) if K1 != 1 else x
            x_new = max(0.001, min(0.999, x_new))

            etages.append({
                'etage': etage,
                'T':     round(T_etage, 2),
                'x1':    round(x, 4),
                'y1':    round(y1, 4),
                'x2':    round(1 - x, 4),
                'y2':    round(y2, 4),
                'K1':    round(K1, 4),
                'K2':    round(K2, 4),
            })
            x = x_new

        return etages

    def _K_etage(self, data, T):
        """Calcule K = Psat/P à température T pour un composant."""
        Psat = self._antoine_psat(data['Tc'], data['Pc'], data['omega'])
        return Psat / self.P if self.P > 0 else 1.0