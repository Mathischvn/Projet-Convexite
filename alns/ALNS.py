import numpy as np
import random
import copy

from algo.gestion_instances import Instance
from algo.selection_initiale import SelectionInitiale

from alns.destructions.supprimerPeuEfficaces import SupprimerPeuEfficace
from alns.destructions.supprimerChainesInefficaces import SupprimerChainesInefficaces
from alns.destructions.supprimerAleatoires import SupprimerAleatoires
from alns.destructions.supprimerSatures import SupprimerSatures

from alns.reparations.repairPPV import RepairPPV
from alns.reparations.repairSolutionInitiale import RepairSolutionInitiale




from check import verifier_chemin

class ALNS:
    def __init__(self, instance, solution_initiale, iterations=30000):
        self.instance = instance
        self.solution_courante = solution_initiale
        self.meilleure_solution = solution_initiale
        self.iterations = iterations

        self.operateurs_destruction = [
            (lambda sol: SupprimerAleatoires(self.instance, mode="day").detruire(sol), "SupprimerJour"),
            (lambda sol: SupprimerAleatoires(self.instance, mode="site").detruire(sol), "SupprimerSite"),
            (lambda sol: SupprimerAleatoires(self.instance, mode="multi_site").detruire(sol), "SupprimerMultiSites"),
            (lambda sol: SupprimerAleatoires(self.instance, mode="hotel").detruire(sol), "SupprimerHotel"),
            (lambda sol: SupprimerChainesInefficaces(self.instance, mode="multi_site").detruire(sol), "SupprimerChainesInefficaces"),
            (lambda sol: SupprimerPeuEfficace(self.instance, mode="site").detruire(sol), "SupprimerSite"),
            (lambda sol: SupprimerPeuEfficace(self.instance, mode="multi_site").detruire(sol), "SupprimerMultiSites"),
            (lambda sol: SupprimerPeuEfficace(self.instance, mode="hotel").detruire(sol), "SupprimerHotel"),
            (lambda sol: SupprimerPeuEfficace(self.instance, mode="day").detruire(sol), "SupprimerJour"),
            (lambda sol: SupprimerSatures(self.instance, mode="day").detruire(sol), "SupprimerSatures")
        ]

        self.operateurs_reparation = [
            (lambda sol, modif_type: RepairPPV(self.instance).reparer(sol, modif_type), "RepairPPV"),
            (lambda sol, modif_type: RepairSolutionInitiale(self.instance).reparer(sol, modif_type), "RepairSolutionInitial"),

        ]

        self.poids_duos = {
            (d_nom, r_nom): 1.0
            for _, d_nom in self.operateurs_destruction
            for _, r_nom in self.operateurs_reparation
            if not (r_nom == "RepairPPV" and d_nom == "SupprimerHotel")
        }

    def optimiser(self):
        for _ in range(self.iterations):
            destruction, nom_destruction = self.selectionner_operateur_destruction()
            reparation, nom_reparation = self.selectionner_operateur_reparation(nom_destruction)

            solution_temporaire, modif_type = destruction(copy.deepcopy(self.solution_courante))
            solution_temporaire = reparation(solution_temporaire, modif_type)

            verifier_chemin(self.instance, solution_temporaire["chemin"], solution_temporaire["hotels"])


            score_temp = self.evaluer(solution_temporaire)
            score_best = self.evaluer(self.meilleure_solution)

            duo = (nom_destruction, nom_reparation)
            gain = 1 if score_temp > score_best else 0
            alpha = 0.2
            self.poids_duos[duo] = (1 - alpha) * self.poids_duos[duo] + alpha * gain

            if gain:
                self.meilleure_solution = solution_temporaire
                self.solution_courante = solution_temporaire
                print(f" Score = {score_temp} supérieur au score max trouvé ({score_best}), sauvegardé comme meilleure solution.")
                self.solution_courante = copy.deepcopy(self.meilleure_solution)

                hotels = self.meilleure_solution['hotels']
                chemin = self.meilleure_solution['chemin']

                hotels_sans_doublons = [hotels[0]]
                for h in hotels[1:]:
                    if h != hotels_sans_doublons[-1]:
                        hotels_sans_doublons.append(h)

        return self.meilleure_solution


    def selectionner_operateur_destruction(self):
        total = sum(
            self.poids_duos.get((d_nom, r_nom), 0)
            for _, d_nom in self.operateurs_destruction
            for _, r_nom in self.operateurs_reparation
        )
        choix = random.uniform(0, total)
        cumule = 0
        for op, d_nom in self.operateurs_destruction:
            poids = sum(
                self.poids_duos.get((d_nom, r_nom), 0)
                for _, r_nom in self.operateurs_reparation
                if (d_nom, r_nom) != ("SupprimerHotel", "RepairPPV")
            )
            cumule += poids
            if choix <= cumule:
                return op, d_nom
        return self.operateurs_destruction[-1]

    def selectionner_operateur_reparation(self, d_nom):
        total = sum(
            self.poids_duos.get((d_nom, r_nom), 0)
            for _, r_nom in self.operateurs_reparation
        )
        choix = random.uniform(0, total)
        cumule = 0
        for op, r_nom in self.operateurs_reparation:
            if (d_nom, r_nom) == ("SupprimerHotel", "RepairPPV"):
                continue
            poids = self.poids_duos.get((d_nom, r_nom), 0)
            cumule += poids
            if choix <= cumule:
                return op, r_nom
        return self.operateurs_reparation[-1]

    def evaluer(self, solution):
        score_total = 0
        sites_vus = set()
        for s in solution['chemin']:
            if s >= self.instance.nombre_hotels and s not in sites_vus:
                score_total += self.instance.scores_des_sites[s]
                sites_vus.add(s)
        return score_total
