import math

R = 8.314  # J/(mol·K)

class VanDerWaals:
    """
    Équation d'état de Van der Waals
    (P + a/V²)(V - b) = RT
    """
    def __init__(self, Tc, Pc):
        self.Tc = Tc  # Température critique (K)
        self.Pc = Pc  # Pression critique (Pa)
        self.a = 27 * R**2 * Tc**2 / (64 * Pc)
        self.b = R * Tc / (8 * Pc)

    def pressure(self, T, V):
        """Calcule la pression (Pa)"""
        return R * T / (V - self.b) - self.a / V**2

    def compressibility_factor(self, T, P):
        """
        Résout Z³ - (1 + B')Z² + A'Z - A'B' = 0
        A' = aP/(RT)², B' = bP/(RT)
        """
        A = self.a * P / (R * T)**2
        B = self.b * P / (R * T)
        coeffs = [1, -(1 + B), A, -A * B]
        roots = self._solve_cubic(coeffs)
        real_roots = [r.real for r in roots if abs(r.imag) < 1e-6 and r.real > B]
        return max(real_roots), min(real_roots)  # (Z_gaz, Z_liquide)

    def fugacity_coefficient(self, T, P):
        Z_v, Z_l = self.compressibility_factor(T, P)
        A = self.a * P / (R * T)**2
        B = self.b * P / (R * T)

        def ln_phi(Z):
            return Z - 1 - math.log(Z - B) - A / Z

        return math.exp(ln_phi(Z_v)), math.exp(ln_phi(Z_l))

    @staticmethod
    def _solve_cubic(coeffs):
        import numpy as np
        return np.roots(coeffs)

    def __repr__(self):
        return f"VanDerWaals(a={self.a:.4f}, b={self.b:.6f})"


class PengRobinson:
    """
    Équation d'état de Peng-Robinson (1976)
    P = RT/(V-b) - a·α / (V(V+b) + b(V-b))
    """
    def __init__(self, Tc, Pc, omega):
        self.Tc = Tc
        self.Pc = Pc
        self.omega = omega  # Facteur acentrique
        self.a = 0.45724 * R**2 * Tc**2 / Pc
        self.b = 0.07780 * R * Tc / Pc
        self.kappa = 0.37464 + 1.54226 * omega - 0.26992 * omega**2

    def alpha(self, T):
        Tr = T / self.Tc
        return (1 + self.kappa * (1 - math.sqrt(Tr)))**2

    def pressure(self, T, V):
        a_T = self.a * self.alpha(T)
        return (R * T / (V - self.b)
                - a_T / (V * (V + self.b) + self.b * (V - self.b)))

    def compressibility_factor(self, T, P):
        a_T = self.a * self.alpha(T)
        A = a_T * P / (R * T)**2
        B = self.b * P / (R * T)
        # Z³ - (1-B)Z² + (A-3B²-2B)Z - (AB-B²-B³) = 0
        coeffs = [
            1,
            -(1 - B),
            A - 3*B**2 - 2*B,
            -(A*B - B**2 - B**3)
        ]
        roots = self._solve_cubic(coeffs)
        real_roots = [r.real for r in roots if abs(r.imag) < 1e-6 and r.real > B]
        if len(real_roots) == 1:
            return real_roots[0], real_roots[0]
        return max(real_roots), min(real_roots)

    def fugacity_coefficient(self, T, P):
        a_T = self.a * self.alpha(T)
        A = a_T * P / (R * T)**2
        B = self.b * P / (R * T)
        Z_v, Z_l = self.compressibility_factor(T, P)
        sqrt2 = math.sqrt(2)

        def ln_phi(Z):
            return (Z - 1
                    - math.log(Z - B)
                    - A / (2 * sqrt2 * B)
                    * math.log((Z + (1 + sqrt2) * B) / (Z + (1 - sqrt2) * B)))

        return math.exp(ln_phi(Z_v)), math.exp(ln_phi(Z_l))

    def vapor_pressure(self, T):
        """Estimation pression de vapeur via corrélation (Pa)"""
        Tr = T / self.Tc
        ln_Pr = 5.92714 - 6.09648/Tr - 1.28862*math.log(Tr) + 0.169347*Tr**6
        ln_Pr += self.omega * (15.2518 - 15.6875/Tr - 13.4721*math.log(Tr) + 0.43577*Tr**6)
        return math.exp(ln_Pr) * self.Pc

    @staticmethod
    def _solve_cubic(coeffs):
        import numpy as np
        return np.roots(coeffs)

    def __repr__(self):
        return f"PengRobinson(Tc={self.Tc}K, Pc={self.Pc}Pa, ω={self.omega})"