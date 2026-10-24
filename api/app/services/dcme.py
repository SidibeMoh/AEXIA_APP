"""
AEXIA™ v3.2 — DCME (Dynamic Causal Multi-scale Explanation)
============================================================
Implémentation algorithmique des équations du framework.
Génère un jeu de données synthétique (Crédit Bancaire), construit le DAG,
et calcule la décomposition causale (Directe + Médiée) pour une instance.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import networkx as nx
from sklearn.ensemble import RandomForestClassifier
from itertools import combinations
import math

# ==========================================
# 1. GÉNÉRATION DES DONNÉES SYNTHÉTIQUES
# ==========================================
def generate_synthetic_data(n_samples: int = 1000) -> pd.DataFrame:
    """Génère un jeu de données de prêt bancaire avec un biais intégré."""
    np.random.seed(42)
    
    # Variables exogènes
    age = np.random.randint(20, 65, n_samples)
    gender = np.random.choice([0, 1], n_samples) # 0: Femme, 1: Homme
    
    # Le salaire dépend de l'âge et du sexe (Biais structurel)
    # Les hommes gagnent en moyenne 10k de plus
    salary = 20000 + (age * 500) + (gender * 10000) + np.random.normal(0, 5000, n_samples)
    salary = np.clip(salary, 15000, None)
    
    # La décision de prêt dépend du salaire, de l'âge, et directement du sexe (Biais direct)
    # On simule un modèle qui favorise les hommes
    logit = -10 + (salary / 10000) + (age / 10) + (gender * 1.5) 
    prob = 1 / (1 + np.exp(-logit))
    loan_approved = (np.random.rand(n_samples) < prob).astype(int)
    
    df = pd.DataFrame({
        'Age': age,
        'Gender': gender,
        'Salary': salary,
        'Loan_Approved': loan_approved
    })
    return df

# ==========================================
# 2. LE GRAPHE CAUSAL (DAG)
# ==========================================
def build_causal_graph() -> nx.DiGraph:
    """Construit le Graphe Acyclique Dirigé (DAG) selon les hypothèses."""
    G = nx.DiGraph()
    G.add_edges_from([
        ('Age', 'Salary'),
        ('Gender', 'Salary'),       # Effet du sexe sur le salaire
        ('Age', 'Loan_Approved'),
        ('Salary', 'Loan_Approved'), # Effet médié (Sexe -> Salaire -> Prêt)
        ('Gender', 'Loan_Approved')  # Effet direct (Sexe -> Prêt)
    ])
    return G

# ==========================================
# 3. MOTEUR DCME
# ==========================================
class DCMEngine:
    def __init__(self, df: pd.DataFrame, graph: nx.DiGraph):
        self.df = df
        self.graph = graph
        self.features = ['Age', 'Gender', 'Salary']
        self.target = 'Loan_Approved'
        
        # Entraînement du modèle prédictif (f)
        self.model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        self.model.fit(self.df[self.features], self.df[self.target])
        
        # Baseline (phi_0) = E[f(X)]
        self.baseline = self.model.predict_proba(self.df[self.features])[:, 1].mean()

    def _predict(self, instance: dict) -> float:
        """Retourne la probabilité de prêt (classe 1) pour une instance."""
        df_inst = pd.DataFrame([instance])
        return self.model.predict_proba(df_inst[self.features])[:, 1][0]

    def _shapley_value(self, instance: dict, feature: str) -> float:
        """
        Calcule la valeur de Shapley causale pour une variable (Équation 1.2).
        """
        from itertools import combinations
        
        other_features = [f for f in self.features if f != feature]
        n = len(other_features)
        shapley = 0.0
        
        # On génère toutes les coalitions possibles (sous-ensembles)
        all_subsets = []
        for r in range(n + 1):
            all_subsets.extend(combinations(other_features, r))
        
        for S in all_subsets:
            S = list(S)
            
            # 1. Scénario avec la variable (S U {feature})
            # On part de la moyenne pour toutes les variables, puis on remplace par les valeurs de l'instance
            inst_with = {f: self.df[f].mean() for f in self.features}
            for f in S:
                inst_with[f] = instance[f]
            inst_with[feature] = instance[feature]
            
            # 2. Scénario sans la variable (S)
            inst_without = {f: self.df[f].mean() for f in self.features}
            for f in S:
                inst_without[f] = instance[f]
            # La variable 'feature' reste à sa valeur moyenne dans inst_without
            
            v_with = self._predict(inst_with)
            v_without = self._predict(inst_without)
            
            # Poids de la coalition
            weight = math.factorial(len(S)) * math.factorial(n - len(S)) / math.factorial(n)
            shapley += weight * (v_with - v_without)
            
        return shapley

    def _causal_salary(self, age: float, gender: float) -> float:
        """Equation causale du salaire (sans bruit)."""
        return 20000 + (age * 500) + (gender * 10000)

    def _causal_fill(self, instance: dict, intervened: set) -> dict:
        """Remplit les variables manquantes : marginale ou modele causal."""
        inst = instance.copy()
        for f in self.features:
            if f not in inst:
                inst[f] = self.df[f].mean()
        # On ne recalcule le salaire QUE si Age ou Gender est intervenu ET que Salary n'est pas directement intervenu
        if ('Age' in intervened or 'Gender' in intervened) and ('Salary' not in intervened):
            inst['Salary'] = self._causal_salary(inst['Age'], inst['Gender'])
        return inst

    def _shapley_value_causal(self, instance: dict, feature: str) -> float:
        """Phi_C : valeur de Shapley causale (avec propagation do-calculus)."""
        from itertools import combinations
        other_features = [f for f in self.features if f != feature]
        n = len(other_features)
        shapley = 0.0
        all_subsets = []
        for r in range(n + 1):
            all_subsets.extend(combinations(other_features, r))
        for S in all_subsets:
            S = list(S)
            intervened_with = set(S) | {feature}
            intervened_without = set(S)
            inst_with = {f: instance[f] for f in S}
            inst_with[feature] = instance[feature]
            inst_with_filled = self._causal_fill(inst_with, intervened_with)
            inst_without = {f: instance[f] for f in S}
            inst_without_filled = self._causal_fill(inst_without, intervened_without)
            v_with = self._predict(inst_with_filled)
            v_without = self._predict(inst_without_filled)
            weight = math.factorial(len(S)) * math.factorial(n - len(S)) / math.factorial(n)
            shapley += weight * (v_with - v_without)
        return shapley

    def calculate_dcme(self, instance: dict) -> dict:
        """DCME V3.1 : y = baseline + Sum(phi_C) = baseline + Sum(phi_D), psi = phi_C - phi_D (Sum(psi) = 0)."""
        phi_direct = {}
        for f in self.features:
            phi_direct[f] = self._shapley_value(instance, f)
        phi_causal = {}
        for f in self.features:
            phi_causal[f] = self._shapley_value_causal(instance, f)
        psi = {f: phi_causal[f] - phi_direct[f] for f in self.features}
        y_hat = self._predict(instance)
        sum_psi = float(sum(psi.values()))
        sum_psi_verified = bool(abs(sum_psi) < 1e-4)
        return {
            "prediction": float(round(y_hat, 4)),
            "baseline": float(round(self.baseline, 4)),
            "direct_contributions": {k: float(round(v, 4)) for k, v in phi_direct.items()},
            "causal_total_contributions": {k: float(round(v, 4)) for k, v in phi_causal.items()},
            "mediated_contributions": {k: float(round(v, 4)) for k, v in psi.items()},
            "sum_psi": float(round(sum_psi, 6)),
            "sum_psi_verified": bool(sum_psi_verified),
            "verification_sum": float(round(float(self.baseline) + float(sum(phi_direct.values())), 4)),
        }