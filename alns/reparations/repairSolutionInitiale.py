class RepairSolutionInitiale:
    def __init__(self, instance):
        self.instance = instance

    def reparer(self, solution, modif_type=None):
        print("=== REPARATION PAR HEURISTIQUE INITIALE ===")
        print(f"  Type de modification détectée : {modif_type}")
        print(f"  Hôtels initiaux : {solution['hotels']}")
        print(f"  Chemin initial  : {solution['chemin']}")

        sequence_hotels = self._completer_hotels(solution['hotels'])

        if modif_type in {"site", "multi_site"}:
            chemin, sequence_hotels = self._reparer_apres_suppression_site(solution['chemin'], sequence_hotels)
        elif modif_type == "day":
            chemin = self._reparer_jour_entier(solution['chemin'], sequence_hotels)
        elif modif_type == "hotel":
            chemin, sequence_hotels = self._reparer_apres_suppression_hotel(solution['chemin'], sequence_hotels)
        else:
            chemin = self._reparer_jour_entier(solution['chemin'], sequence_hotels)

        print(f"  Hotels complétés : {sequence_hotels}")
        print(f"  Chemin réparé    : {chemin}")
        print("===========================================\n")

        return {
            'hotels': sequence_hotels,
            'chemin': chemin
        }

    def _completer_hotels(self, hotels):
        sequence = hotels[:]
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

            chemin_jour_original = [depart] + anciens_sites + [arrivee]
            self._remettre_sites_supprimes(anciens_sites, chemin_jour_original)

            sites_futurs = self._sites_utiles_apres(chemin_original, arrivee)
            chemin_jour = self._glouton_jour(depart, arrivee, self.instance.distance_maximale_par_jour[jour], sites_a_eviter=sites_futurs)
            self._marquer_sites_visites(chemin_jour)
            chemin_complet.extend(chemin_jour)

        return chemin_complet, sequence_hotels

    def _reparer_apres_suppression_hotel(self, chemin_original, hotels):
        self.instance.reinitialiser_masque_sites()
        hotels_modifies = hotels[:]
        chemin_complet = []

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
            print("Aucun trou détecté dans les hôtels, rien à réparer.")
            return chemin_original, hotels

       
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

        nouvel_hotel, sites_avant, sites_apres = self._inserer_nouvel_hotel_autour(
            hotel_avant, hotel_apres, sites_avant, sites_apres, index
        )

        if nouvel_hotel is None:
            print("⚠️ Aucun hôtel atteignable trouvé malgré les suppressions.")
            nouvel_hotel = hotel_avant 

        hotels_modifies[index] = nouvel_hotel

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
        distance_restante = distance_max
        etape = [depart]
        sites_a_eviter = set(sites_a_eviter or [])

        while True:
            candidats = [
                s for s in range(self.instance.nombre_hotels, self.instance.nombre_de_sites)
                if self.instance.masque_sites_visites[s]
                and self.instance.matrice_distances[position][s] + self.instance.matrice_distances[s][arrivee] <= distance_restante
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

            d = self.instance.matrice_distances[position][meilleur]
            etape.append(meilleur)
            distance_restante -= d
            position = meilleur
            self.instance.masque_sites_visites[meilleur] = False

        etape.append(arrivee)
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
        if depart not in chemin or arrivee not in chemin:
            return [depart, arrivee]
        index_d = chemin.index(depart)
        index_a = chemin.index(arrivee, index_d + 1)
        return chemin[index_d:index_a + 1]

    def _sites_utiles_apres(self, chemin, arrivee):
        try:
            idx = chemin.index(arrivee)
            return [s for s in chemin[idx + 1:] if s >= self.instance.nombre_hotels]
        except ValueError:
            return []

    def _inserer_nouvel_hotel_autour(self, hotel_avant, hotel_apres, sites_avant, sites_apres, jour_index):
        for nb_sup_avant in range(len(sites_avant) + 1):
            suffixe = sites_avant[-nb_sup_avant:] if nb_sup_avant > 0 else []
            nouveaux_avant = sites_avant[:-nb_sup_avant] if nb_sup_avant > 0 else sites_avant[:]

            for nb_sup_apres in range(len(sites_apres) + 1):
                prefixe = sites_apres[:nb_sup_apres] if nb_sup_apres > 0 else []
                nouveaux_apres = sites_apres[nb_sup_apres:] if nb_sup_apres > 0 else sites_apres[:]

                self._remettre_sites_supprimes(nouveaux_avant + nouveaux_apres, [])

                hotels_possibles = self._hotels_atteignables(hotel_avant, jour_index)
                for h in hotels_possibles:
                    d1 = self.instance.matrice_distances[hotel_avant][h]
                    d2 = self.instance.matrice_distances[h][hotel_apres]
                    if d1 + d2 <= self.instance.distance_maximale_par_jour[jour_index]:
                        return h, nouveaux_avant, nouveaux_apres

        return None, sites_avant, sites_apres
