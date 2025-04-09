class RepairSolutionInitiale:
    def __init__(self, instance):
        self.instance = instance

    def reparer(self, solution, modif_type=None):

        if modif_type == "hotel":
            chemin, sequence_hotels = self._reparer_apres_suppression_hotel(solution['chemin'], solution['hotels'])
            sequence_hotels = self._completer_hotels(sequence_hotels)

        else:
            sequence_hotels = self._completer_hotels(solution['hotels'])

            if modif_type in {"site", "multi_site"}:
                chemin, sequence_hotels = self._reparer_apres_suppression_site(solution['chemin'], sequence_hotels)
            elif modif_type == "day":
                chemin = self._reparer_jour_entier(solution['chemin'], sequence_hotels)
            else:
                chemin = self._reparer_jour_entier(solution['chemin'], sequence_hotels)
        chemin = nettoyer_doublons_consecutifs(chemin)

        return {
            'hotels': sequence_hotels,
            'chemin': chemin
        }

    def _completer_hotels(self, hotels):
        sequence = hotels[:]
        expected_len = self.instance.nombre_de_jours + 1

        if len(sequence) < expected_len:
            last_known = sequence[-1] if sequence[-1] is not None else sequence[-2]
            while len(sequence) < expected_len:
                sequence.append(last_known)
        elif len(sequence) > expected_len:
            sequence = sequence[:expected_len]

        for i in range(1, len(sequence) - 1):
            if sequence[i] is None:
                candidats = self._hotels_atteignables(sequence[i - 1], i)
                if candidats:
                    sequence[i] = min(candidats, key=lambda h: self.instance.matrice_distances[sequence[i - 1]][h])
                else:
                    sequence[i] = sequence[i - 1] 

        return sequence


    def _hotels_atteignables(self, hotel_depart, jour):
        dmax = self.instance.distance_maximale_par_jour[jour]
        return [
            h for h in range(self.instance.nombre_hotels)
            if self.instance.matrice_distances[hotel_depart][h] <= dmax
        ]

    def _reparer_jour_entier(self, chemin_original, sequence_hotels):
        self.instance.reinitialiser_masque_sites()
        chemin_complet = []

        for jour in range(self.instance.nombre_de_jours):
            depart = sequence_hotels[jour]
            arrivee = sequence_hotels[jour + 1]
            sites_futurs = self._sites_utiles_apres(chemin_original, arrivee)
            chemin_jour = self._glouton_jour(depart, arrivee, self.instance.distance_maximale_par_jour[jour], sites_a_eviter=sites_futurs)
            self._marquer_sites_visites(chemin_jour)
            chemin_complet.extend(chemin_jour)

        return chemin_complet

    def _reparer_apres_suppression_site(self, chemin_original, sequence_hotels):
        self.instance.reinitialiser_masque_sites()
        chemin_complet = []

        index = 0
        for jour in range(self.instance.nombre_de_jours):
            depart = sequence_hotels[jour]
            arrivee = sequence_hotels[jour + 1]

            anciens_sites = []
            if index < len(chemin_original) and chemin_original[index] == depart:
                index += 1
            while index < len(chemin_original) and chemin_original[index] != arrivee:
                anciens_sites.append(chemin_original[index])
                index += 1
            if index < len(chemin_original):
                index += 1

            # Réactivation des sites supprimés
            chemin_jour_original = [depart] + anciens_sites + [arrivee]
            self._remettre_sites_supprimes(anciens_sites, chemin_jour_original)

            chemin_jour = glouton_multi_site_partiel(self.instance, depart, arrivee, anciens_sites, self.instance.distance_maximale_par_jour[jour])


            self._marquer_sites_visites(chemin_jour)
            chemin_complet.extend(chemin_jour)

        return chemin_complet, sequence_hotels


    def _reparer_apres_suppression_hotel(self, chemin_original, hotels):
        self.instance.reinitialiser_masque_sites()
        hotels_modifies = hotels[:]
        chemin_complet = []

        # Étape 1 : détecter le trou dans les hôtels
        hotel_avant = None
        hotel_apres = None
        index = None

        for i in range(len(hotels)):
            if hotels[i] is None:
                hotel_avant = hotels[i - 1]
                hotel_apres = hotels[i + 1]
                index = i
                break

        if index is None:
            return chemin_original, hotels

        # Étape 2 : extraire les sites entre ces deux hôtels
        sites_avant, sites_apres = [], []
        phase = None
        for node in chemin_original:
            if node == hotel_avant:
                phase = "avant"
                continue
            if node == hotel_apres:
                break
            if node in hotels:
                continue
            if phase == "avant":
                sites_avant.append(node)
            elif phase == "apres":
                sites_apres.append(node)

        # Étape 3 : tentative d’insertion d’un nouvel hôtel avec suppression partielle
        nouvel_hotel = self._inserer_nouvel_hotel_autour(chemin_original, hotels, index)

        if nouvel_hotel is None:
            nouvel_hotel = hotel_avant 

        hotels_modifies[index] = nouvel_hotel

        # Étape 4 : régénération des 2 journées autour
        bloc_1 = self._extraire_etape_jour(chemin_original, hotel_avant, nouvel_hotel)
        bloc_2 = self._extraire_etape_jour(chemin_original, nouvel_hotel, hotel_apres)

        self._remettre_sites_supprimes(sites_avant, bloc_1)
        self._remettre_sites_supprimes(sites_apres, bloc_2)

        futurs_j2 = self._sites_utiles_apres(chemin_original, nouvel_hotel)
        futurs_j3 = self._sites_utiles_apres(chemin_original, hotel_apres)

        chemin_j1 = self._glouton_jour(hotel_avant, nouvel_hotel, self.instance.distance_maximale_par_jour[index - 1], sites_a_eviter=futurs_j2)
        self._marquer_sites_visites(chemin_j1)
        chemin_j2 = self._glouton_jour(nouvel_hotel, hotel_apres, self.instance.distance_maximale_par_jour[index], sites_a_eviter=futurs_j3)
        self._marquer_sites_visites(chemin_j2)

        # Étape 5 : reconstruction complète du chemin
        for j in range(self.instance.nombre_de_jours):
            if j == index - 1:
                chemin_complet.extend(chemin_j1)
            elif j == index:
                chemin_complet.extend(chemin_j2)
            else:
                depart = hotels[j]
                arrivee = hotels[j + 1]
                chemin_complet.extend(self._extraire_etape_jour(chemin_original, depart, arrivee))

        return chemin_complet, hotels_modifies

    def _glouton_jour(self, depart, arrivee, distance_max, sites_a_eviter=None):
        position = depart
        distance_parcourue = 0
        etape = [depart]
        sites_a_eviter = set(sites_a_eviter or [])

        while True:
            candidats = [
                s for s in range(self.instance.nombre_hotels, self.instance.nombre_de_sites)
                if self.instance.masque_sites_visites[s]
                and self.instance.matrice_distances[position][s] + self.instance.matrice_distances[s][arrivee] + distance_parcourue <= distance_max
                and self.instance.scores_des_sites[s] > 0 
            ]

            if not candidats:
                break

            prioritaires = [s for s in candidats if s not in sites_a_eviter]
            if prioritaires:
                candidats = prioritaires

            def ratio_avec_continuite(s):
                d_depart = self.instance.matrice_distances[position][s]
                d_vers_arrivee = self.instance.matrice_distances[s][arrivee]
                d_directe = self.instance.matrice_distances[position][arrivee]
                bonus = 1.2 if d_vers_arrivee < d_directe else 1
                return d_depart / (self.instance.scores_des_sites[s] * bonus)

            meilleur = min(candidats, key=ratio_avec_continuite)

            d_site = self.instance.matrice_distances[position][meilleur]
            if distance_parcourue + d_site + self.instance.matrice_distances[meilleur][arrivee] > distance_max:
                break 
            etape.append(meilleur)
            distance_parcourue += d_site
            position = meilleur
            self.instance.masque_sites_visites[meilleur] = False

        d_retour = self.instance.matrice_distances[position][arrivee]
        if distance_parcourue + d_retour <= distance_max:
            etape.append(arrivee)
        else:
            print(f"[AVERTISSEMENT] Étape ignorée : {position} → {arrivee} dépasse {distance_max} (actuel: {distance_parcourue + d_retour:.2f})")

        return etape



    def _remettre_sites_supprimes(self, anciens_sites, chemin_jour):
        sites_restants = set(chemin_jour)
        for s in anciens_sites:
            if s not in sites_restants and s >= self.instance.nombre_hotels:
                self.instance.masque_sites_visites[s] = True

    def _marquer_sites_visites(self, chemin):
        for node in chemin:
            if node >= self.instance.nombre_hotels:
                self.instance.masque_sites_visites[node] = False

    def _extraire_etape_jour(self, chemin, depart, arrivee):
        if depart == arrivee:
            return [depart]
        if depart not in chemin or arrivee not in chemin:
            return [depart, arrivee]
        index_d = chemin.index(depart)
        try:
            index_a = chemin.index(arrivee, index_d + 1)
        except ValueError:
            return [depart, arrivee]
        return chemin[index_d:index_a + 1]


    def _sites_utiles_apres(self, chemin, arrivee):
        try:
            idx = chemin.index(arrivee)
            return [s for s in chemin[idx + 1:] if s >= self.instance.nombre_hotels]
        except ValueError:
            return []

    def _inserer_nouvel_hotel_autour(self, chemin_original, hotels, index):
        hotel_avant = hotels[index - 1]
        hotel_apres = hotels[index + 1]
        distance_max = self.instance.distance_maximale_par_jour[index]


        position_depart = hotel_avant
        for node in reversed(chemin_original):
            if node == hotel_avant:
                break
            if node >= self.instance.nombre_hotels:
                position_depart = node
                break

        hotels_possibles = []
        for h in range(self.instance.nombre_hotels):
            d1 = self.instance.matrice_distances[position_depart][h]
            d2 = self.instance.matrice_distances[h][hotel_apres]
            total = d1 + d2
            if total <= distance_max:
                hotels_possibles.append((h, total))


        for h, total in hotels_possibles:
            d1 = self.instance.matrice_distances[position_depart][h]
            d2 = self.instance.matrice_distances[h][hotel_apres]

        if not hotels_possibles:
            return hotel_avant

        # Choix du meilleur hôtel (minimisant le total d1 + d2)
        nouvel_hotel = min(hotels_possibles, key=lambda x: x[1])[0]
        return nouvel_hotel



def ajouter_jour_au_chemin(chemin_complet, sous_chemin):
    if not sous_chemin:
        return


    if chemin_complet and chemin_complet[-1] == sous_chemin[0]:
        chemin_complet.extend(sous_chemin[1:])
    else:
        chemin_complet.extend(sous_chemin)


def nettoyer_doublons_consecutifs(chemin):
    chemin_nettoye = []
    dernier = None
    for node in chemin:
        if node != dernier:
            chemin_nettoye.append(node)
        dernier = node
    return chemin_nettoye

def glouton_multi_site_partiel(instance, depart, arrivee, anciens_sites, distance_max):
    position = depart
    distance_parcourue = 0
    etape = [depart]
    anciens_sites_set = set(anciens_sites)

    while True:
        candidats = []
        for s in range(instance.nombre_hotels, instance.nombre_de_sites):
            if not instance.masque_sites_visites[s]:
                continue
            if s in anciens_sites_set:
                continue

            d_site = instance.matrice_distances[position][s]
            d_retour = instance.matrice_distances[s][arrivee]

            if distance_parcourue + d_site + d_retour > distance_max:
                continue

            d_directe = instance.matrice_distances[position][arrivee]
            bonus = 1.2 if d_retour < d_directe else 1
            score = instance.scores_des_sites[s]

            if score <= 0:
                continue 

            ponderation = d_site / (score * bonus)
            candidats.append((s, ponderation, d_site))

        if not candidats:
            break

        site_choisi, _, d_site = min(candidats, key=lambda x: x[1])
        etape.append(site_choisi)
        distance_parcourue += d_site
        position = site_choisi
        instance.masque_sites_visites[site_choisi] = False

    d_retour = instance.matrice_distances[position][arrivee]
    if distance_parcourue + d_retour <= distance_max:
        etape.append(arrivee)

    return etape

