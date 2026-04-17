import math

R = 8.314  # J/(mol·K)


class Wilson:
    """
    Modèle de Wilson pour coefficients d'activité en phase liquide.
    Idéal pour mélanges polaires miscibles (ex: éthanol-eau).
    ln(γ_i) = -ln(Σ x_j·Λ_ij) + 1 - Σ_k [x_k·Λ_ki / Σ_j x_j·Λ_kj]
    """
    def __init__(self, V_liquide, lambda_params):
        """
        V_liquide : liste des volumes molaires liquides [V1, V2, ...] (m³/mol)
        lambda_params : matrice des paramètres d'interaction (aij en J/mol)
                        lambda_params[i][j] = aij
        """
        self.V = V_liquide
        self.a = lambda_params
        self.n = len(V_liquide)

    def _Lambda(self, T):
        """Calcule la matrice Lambda(T)"""
        n = self.n
        L = [[0.0]*n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i == j:
                    L[i][j] = 1.0
                else:
                    L[i][j] = (self.V[j] / self.V[i]) * math.exp(-self.a[i][j] / (R * T))
        return L

    def activity_coefficients(self, x, T):
        """
        x : liste des fractions molaires [x1, x2, ...]
        T : température (K)
        Retourne : liste des coefficients d'activité [γ1, γ2, ...]
        """
        n = self.n
        L = self._Lambda(T)
        gamma = []

        for i in range(n):
            # Terme 1 : -ln(Σ x_j * Λ_ij)
            sum1 = sum(x[j] * L[i][j] for j in range(n))
            term1 = -math.log(sum1)

            # Terme 2 : 1 - Σ_k [x_k * Λ_ki / Σ_j x_j * Λ_kj]
            term2 = 0.0
            for k in range(n):
                sum_k = sum(x[j] * L[k][j] for j in range(n))
                term2 += x[k] * L[k][i] / sum_k

            ln_gamma = term1 + 1 - term2
            gamma.append(math.exp(ln_gamma))

        return gamma

    def __repr__(self):
        return f"Wilson(n_composants={self.n})"


class NRTL:
    """
    Modèle NRTL (Non-Random Two-Liquid) — Renon & Prausnitz (1968)
    Adapté aux mélanges partiellement miscibles et systèmes eau-solvant.
    ln(γ_i) = [Σ_j τ_ji·G_ji·x_j / Σ_k G_ki·x_k]
               + Σ_j [x_j·G_ij / Σ_k G_kj·x_k]
               × [τ_ij - Σ_m x_m·τ_mj·G_mj / Σ_k G_kj·x_k]
    """
    def __init__(self, tau_params, alpha_params):
        """
        tau_params  : matrice τij (paramètres d'énergie d'interaction)
                      tau_params[i][j] = (gij - gjj) / RT  — adimensionnel ou en J/mol
        alpha_params: matrice αij (non-randomness), typiquement 0.2–0.47
        """
        self.tau = tau_params   # peut être matrice de valeurs à T donné
        self.alpha = alpha_params
        self.n = len(tau_params)

    def _G(self, T=None):
        """
        Calcule la matrice G_ij = exp(-α_ij · τ_ij)
        Si tau est en J/mol, passer T pour recalculer τ = a/RT
        """
        n = self.n
        G = [[0.0]*n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                tau_ij = self.tau[i][j]
                G[i][j] = math.exp(-self.alpha[i][j] * tau_ij)
        return G

    def activity_coefficients(self, x, T=None):
        """
        x : liste des fractions molaires
        T : température (K), optionnel si tau déjà adimensionnel
        Retourne : liste des γi
        """
        n = self.n
        G = self._G(T)
        tau = self.tau
        gamma = []

        for i in range(n):
            # Terme A : Σ_j τ_ji·G_ji·x_j / Σ_k G_ki·x_k
            num_A = sum(tau[j][i] * G[j][i] * x[j] for j in range(n))
            den_A = sum(G[k][i] * x[k] for k in range(n))
            term_A = num_A / den_A

            # Terme B : Σ_j [x_j·G_ij/Σ_k G_kj·x_k] × [τ_ij - num_mj/den_mj]
            term_B = 0.0
            for j in range(n):
                den_j = sum(G[k][j] * x[k] for k in range(n))
                num_mj = sum(x[m] * tau[m][j] * G[m][j] for m in range(n))
                term_B += (x[j] * G[i][j] / den_j) * (tau[i][j] - num_mj / den_j)

            ln_gamma = term_A + term_B
            gamma.append(math.exp(ln_gamma))

        return gamma

    def __repr__(self):
        return f"NRTL(n_composants={self.n})"