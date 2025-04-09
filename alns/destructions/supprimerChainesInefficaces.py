import copy
from alns.destructions.fonctionCommunesDestructions import *

class SupprimerChainesInefficaces:
    def __init__(self, instance, mode="multi_site"):
        self.instance = instance
        self.mode = mode


    def detruire(self, solution):
        chemin = solution['chemin']
        hotels = solution['hotels']
        nb_hotels = self.instance.nombre_hotels
        d = self.instance.matrice_distances
        s = self.instance.scores_des_sites

        candidats = []
        i = 0
        while i < len(chemin):
            if chemin[i] < nb_hotels:
                j = i + 1
                while j < len(chemin) and chemin[j] >= nb_hotels:
                    j += 1
                zone_sites = chemin[i + 1:j]
                if len(zone_sites) >= 2:
                    for l in range(2, min(5, len(zone_sites)) + 1):
                        for k in range(0, len(zone_sites) - l + 1):
                            chaine = zone_sites[k:k + l]
                            ratio = ratio_distance_sur_score(d, s, chaine)
                            candidats.append((i + 1 + k, l, ratio))
                i = j
            else:
                i += 1

        if not candidats:
            return solution, self.mode

        i_cible, l_cible, _ = extraire_plus_anormal(candidats, key=lambda x: x[2])
        sites_a_supprimer = chemin[i_cible:i_cible + l_cible]

        nouveau_chemin = [x for x in chemin if x not in sites_a_supprimer]

        return {
            'chemin': nouveau_chemin,
            'hotels': hotels
        }, self.mode
