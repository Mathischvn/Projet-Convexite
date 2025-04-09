import copy
from collections import Counter
from alns.destructions.fonctionCommunesDestructions import *

class SupprimerSatures:
    def __init__(self, instance, mode="day"):
        self.instance = instance
        self.mode = mode  # utile pour RepairPPV

    def detruire(self, solution):
        hotels = solution['hotels']
        chemin = solution['chemin']

        # Étape 1 : repérer les hôtels saturés (présents >= 2 fois sauf aux extrémités)
        compteur = Counter(hotels[1:-1])
        hotels_satures = {h: c for h, c in compteur.items() if c >= 2}

        if not hotels_satures:
            return solution, self.mode

        # Étape 2 : identifier les jours utilisant un hôtel saturé
        jours_candidats = []
        for jour in range(1, len(hotels) - 1):
            hd = hotels[jour]
            ha = hotels[jour + 1]
            if hd in hotels_satures or ha in hotels_satures:
                ratio = calculer_ratio_journee(self.instance, chemin, hotels, jour)
                jours_candidats.append((jour, ratio))

        if not jours_candidats:
            return solution, self.mode

        # Étape 3 : supprimer la journée la plus inefficace parmi celles liées à un hôtel saturé
        jour_cible, _ = max(jours_candidats, key=lambda x: x[1])

        nouvelle_solution = copy.deepcopy(solution)
        nouvelle_solution['hotels'] = hotels[:jour_cible] + hotels[jour_cible + 1:]
        nouvelle_solution['chemin'] = supprimer_jour_du_chemin(chemin, hotels[jour_cible], hotels[jour_cible + 1])

        return nouvelle_solution, self.mode
