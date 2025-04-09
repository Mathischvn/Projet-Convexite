import random
import copy
from alns.destructions.fonctionCommunesDestructions import *

class SupprimerAleatoires:
    def __init__(self, instance, mode):
        """
        :param mode: 'hotel', 'site', 'multi_site', ou 'jour'
        """
        self.instance = instance
        self.mode = mode

    def detruire(self, solution):
        if self.mode == "site":
            return self._supprimer_site(solution), "site"
        elif self.mode == "multi_site":
            return self._supprimer_multi_sites(solution), "multi_site"
        elif self.mode == "hotel":
            return self._supprimer_hotel(solution), "hotel"
        elif self.mode == "day":
            return self._supprimer_jour(solution), "day"
        else:
            raise ValueError(f"Mode de suppression inconnu : {self.mode}")

    def _supprimer_hotel(self, solution):

        hotels = solution['hotels']
        chemin = solution['chemin']
        nb_jours = self.instance.nombre_de_jours

        index = random.randint(1, len(hotels) - 2) 
        hotel_suppr = hotels[index]

        hotels[index] = None

        # Récupération des hôtels avant et après
        hotel_avant = hotels[index - 1]
        hotel_apres = hotels[index + 1]

        # Suppression des sites du jour précédent et du jour suivant
        def extraire_sites_jour(depart, arrivee):
            sites = []
            started = False
            for node in chemin:
                if node == depart:
                    started = True
                    continue
                if started:
                    if node == arrivee:
                        break
                    if node >= self.instance.nombre_hotels:
                        sites.append(node)
            return sites

        def supprimer_sites(chemin, sites_a_supprimer):
            return [node for node in chemin if node not in sites_a_supprimer]

        if index - 1 >= 0:
            dist_prev = self.instance.distance_maximale_par_jour[index - 1]
            sites_prev = extraire_sites_jour(hotel_avant, hotel_suppr)
            nb_suppr_prev = max(1, int(len(sites_prev) * 0.2))  # au moins 1 site
            sites_a_suppr_prev = random.sample(sites_prev, min(nb_suppr_prev, len(sites_prev)))
            chemin = supprimer_sites(chemin, sites_a_suppr_prev)

        if index < nb_jours:
            dist_next = self.instance.distance_maximale_par_jour[index]
            sites_next = extraire_sites_jour(hotel_suppr, hotel_apres)
            nb_suppr_next = max(1, int(len(sites_next) * 0.2))
            sites_a_suppr_next = random.sample(sites_next, min(nb_suppr_next, len(sites_next)))
            chemin = supprimer_sites(chemin, sites_a_suppr_next)

        solution['chemin'] = chemin
        solution['hotels'] = hotels

        return solution

    def _supprimer_site(self, solution):
        sites = [i for i in solution['chemin'] if i >= self.instance.nombre_hotels]
        if sites:
            a_supprimer = random.choice(sites)
            solution['chemin'].remove(a_supprimer)
        return solution

    def _supprimer_multi_sites(self, solution):
        chemin = solution['chemin']
        hotels = solution['hotels']
        nb_jours = self.instance.nombre_de_jours

        # Étape 1 : choisir un jour au hasard avec au moins 1 site
        jours_valides = []
        index = 0

        for j in range(nb_jours):
            depart = hotels[j]
            arrivee = hotels[j + 1]
            sites_jour = []

            if index < len(chemin) and chemin[index] == depart:
                index += 1

            while index < len(chemin) and chemin[index] != arrivee:
                site = chemin[index]
                if site >= self.instance.nombre_hotels and site not in hotels:
                    sites_jour.append(site)
                index += 1

            if sites_jour:
                jours_valides.append((j, sites_jour))

            if index < len(chemin):
                index += 1

        if not jours_valides:
            return solution

        # Étape 2 : choisir un jour au hasard parmi ceux avec des sites
        jour_choisi, sites = random.choice(jours_valides)

        # Étape 3 : supprimer jusqu'à 3 sites de cette journée
        nb_suppr = min(len(sites), random.randint(1, 3))
        a_supprimer = random.sample(sites, nb_suppr)
        solution['chemin'] = [x for x in chemin if x not in a_supprimer]

        return solution

    def _supprimer_jour(self, solution):
        chemin = solution['chemin']
        hotels = solution['hotels']
        jours_valides = []

        # Étape 1 : repérer les jours contenant des sites
        index = 0
        for j in range(self.instance.nombre_de_jours):
            depart = hotels[j]
            arrivee = hotels[j + 1]
            sites = []

            if index < len(chemin) and chemin[index] == depart:
                index += 1

            while index < len(chemin) and chemin[index] != arrivee:
                if chemin[index] >= self.instance.nombre_hotels:
                    sites.append(chemin[index])
                index += 1

            if sites:
                jours_valides.append((depart, arrivee, set(sites)))

            if index < len(chemin):
                index += 1

        if not jours_valides:
            return solution

        # Étape 2 : choisir un jour aléatoire et supprimer les sites de ce jour
        depart, arrivee, sites_a_supprimer = random.choice(jours_valides)

        solution['chemin'] = [
            node for node in chemin
            if node not in sites_a_supprimer
        ]

        return solution

