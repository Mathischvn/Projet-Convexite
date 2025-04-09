import random
from alns.destructions.fonctionCommunesDestructions import *

class SupprimerPeuEfficace:
    def __init__(self, instance, mode):
        """
        :param mode: 'site', 'multi_site', 'hotel', ou 'day'
        """
        self.instance = instance
        self.mode = mode

    def detruire(self, solution):
        if self.mode == "site":
            return self._supprimer_site(solution), "site"
        elif self.mode == "multi_site":
            return self._supprimer_chaine_sites(solution), "multi_site"
        elif self.mode == "hotel":
            return self._supprimer_hotel(solution), "hotel"
        elif self.mode == "day":
            return self._supprimer_jour(solution), "day"
        else:
            raise ValueError(f"Mode de suppression inconnu : {self.mode}")

    def _supprimer_site(self, solution):
        chemin = solution['chemin']
        d = self.instance.matrice_distances
        s = self.instance.scores_des_sites

        ratios = []
        for i in range(1, len(chemin) - 1):
            prev, curr, next_ = chemin[i - 1], chemin[i], chemin[i + 1]
            if curr >= self.instance.nombre_hotels:
                score = s[curr]
                dist = d[prev][curr] + d[curr][next_]
                ratio = dist / score if score > 0 else float("inf")
                ratios.append((i, ratio))

        if not ratios:
            return solution

        moyenne = sum(r for _, r in ratios) / len(ratios)
        i_cible = max(ratios, key=lambda x: abs(x[1] - moyenne))[0]

        solution['chemin'] = chemin[:i_cible] + chemin[i_cible + 1:]
        return solution

    def _supprimer_chaine_sites(self, solution, longueur_max=3):
        chemin = solution['chemin']
        d = self.instance.matrice_distances
        s = self.instance.scores_des_sites
        candidats = []

        for l in range(2, longueur_max + 1):
            for i in range(1, len(chemin) - l):
                chaine = chemin[i:i + l]
                if any(x < self.instance.nombre_hotels for x in chaine):
                    continue

                prev = chemin[i - 1]
                next_ = chemin[i + l] if i + l < len(chemin) else None

                d_start = d[prev][chaine[0]]
                d_end = d[chaine[-1]][next_] if next_ is not None else 0
                d_chaine = sum(d[chaine[k]][chaine[k + 1]] for k in range(len(chaine) - 1))
                score = sum(s[x] for x in chaine)

                ratio = (d_start + d_chaine + d_end) / score if score > 0 else float("inf")
                candidats.append((i, l, ratio))

        if not candidats:
            return solution

        moyenne = sum(r for _, _, r in candidats) / len(candidats)
        i, l, _ = max(candidats, key=lambda x: abs(x[2] - moyenne))

        chaine_suppr = chemin[i:i + l]
        solution['chemin'] = [x for x in chemin if x not in chaine_suppr]
        return solution

    def _supprimer_hotel(self, solution):
        hotels = solution['hotels']
        d = self.instance.matrice_distances
        ratios = []

        for i in range(1, len(hotels) - 1):
            h_prev = hotels[i - 1]
            h = hotels[i]
            h_next = hotels[i + 1]
            ratio = d[h_prev][h] + d[h][h_next]
            ratios.append((i, ratio))

        if not ratios:
            return solution

        moyenne = sum(r for _, r in ratios) / len(ratios)
        i_cible = max(ratios, key=lambda x: abs(x[1] - moyenne))[0]
        hotels[i_cible] = None
        solution['hotels'] = hotels
        return solution

    def _supprimer_jour(self, solution):
        chemin = solution['chemin']
        hotels = solution['hotels']

        ratios = [
            calculer_ratio_journee(self.instance, chemin, hotels, jour)
            for jour in range(self.instance.nombre_de_jours)
        ]

        jours_valides = [
            (j, r) for j, r in enumerate(ratios)
            if 0 <= j < self.instance.nombre_de_jours and hotels[j] is not None and hotels[j + 1] is not None
        ]

        if not jours_valides:
            return solution

        jour_cible = extraire_plus_anormal(jours_valides, key=lambda x: x[1])[0]
        hd, ha = hotels[jour_cible], hotels[jour_cible + 1]

        solution['chemin'] = supprimer_jour_du_chemin(chemin, hd, ha)
        return solution
