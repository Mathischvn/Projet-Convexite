import copy

class RepairPPV:
    def __init__(self, instance):
        self.instance = instance

    def reparer(self, solution, modif_type=None):
        print("=== REPARATION PPV ===")
        print(f"  Type de modification détectée : {modif_type}")
        print(f"  Hôtels initiaux : {solution['hotels']}")
        print(f"  Chemin initial  : {solution['chemin']}")

        sequence_hotels = self._completer_hotels(solution['hotels'])

        if modif_type in {"site", "multi_site"}:
            chemin = self._reparer_apres_suppression_site(solution['chemin'], sequence_hotels)
        elif modif_type == "day":
            chemin = self._reparer_jour_entier(solution['chemin'], sequence_hotels)
        else:
            chemin, sequence_hotels = self._reparer_apres_suppression_hotel(solution['chemin'], sequence_hotels)

        print(f"  Hotels complétés : {sequence_hotels}")
        print(f"  Chemin réparé    : {chemin}")
        print("======================\n")

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

    def _regenerer_chemin_ppv(self, sequence_hotels):
        self.instance.reinitialiser_masque_sites()
        chemin_complet = []

        for jour in range(self.instance.nombre_de_jours):
            depart = sequence_hotels[jour]
            arrivee = sequence_hotels[jour + 1]
            position = depart
            distance_max = self.instance.distance_maximale_par_jour[jour]

            etape = [depart]

            while distance_max > 0:
                candidats = self._sites_atteignables(position, arrivee, distance_max)
                if not candidats:
                    break

                site = min(candidats, key=lambda s: self.instance.matrice_distances[position][s])

                etape.append(site)
                distance_max -= self.instance.matrice_distances[position][site]
                position = site
                self.instance.masque_sites_visites[site] = False

            etape.append(arrivee)
            chemin_complet.extend(etape)

        return chemin_complet
    
    def _reparer_jour_entier(self, chemin_original, sequence_hotels):
        self.instance.reinitialiser_masque_sites()

        for h in range(self.instance.nombre_hotels):
            self.instance.masque_sites_visites[h] = False

        chemin_complet = []
        index = 0

        for jour in range(self.instance.nombre_de_jours):
            depart = sequence_hotels[jour]
            arrivee = sequence_hotels[jour + 1]
            contient_site = False
            i = index
            if i < len(chemin_original) and chemin_original[i] == depart:
                i += 1

            while i < len(chemin_original) and chemin_original[i] != arrivee:
                if chemin_original[i] >= self.instance.nombre_hotels:
                    contient_site = True
                    break
                i += 1

            if not contient_site:
        
                self._remettre_sites_jour(chemin_original, depart, arrivee)
                sous_chemin = self._ppv_jour(depart, arrivee, self.instance.distance_maximale_par_jour[jour])
            else:
            
                sous_chemin = self._extraire_etape_jour(chemin_original, depart, arrivee)

            
                for node in sous_chemin:
                    if node >= self.instance.nombre_hotels:
                        self.instance.masque_sites_visites[node] = False

            
            if chemin_complet and chemin_complet[-1] == sous_chemin[0]:
                chemin_complet.extend(sous_chemin[1:])
            else:
                chemin_complet.extend(sous_chemin)

            
            if index < len(chemin_original) and chemin_original[index] == depart:
                index += 1
            while index < len(chemin_original) and chemin_original[index] != arrivee:
                index += 1
            if index < len(chemin_original):
                index += 1

        return chemin_complet


    def _recalculer_sites_localise(self, chemin_original, sequence_hotels):
        self.instance.reinitialiser_masque_sites()
        chemin_complet = []
        index = 0

        for jour in range(self.instance.nombre_de_jours):
            depart = sequence_hotels[jour]
            arrivee = sequence_hotels[jour + 1]


            etape_jour = []
            if index < len(chemin_original) and chemin_original[index] == depart:
                index += 1

            while index < len(chemin_original) and chemin_original[index] != arrivee:
                index_site = chemin_original[index]
                if index_site >= self.instance.nombre_hotels:
                    self.instance.masque_sites_visites[index_site] = True 
                index += 1

            if index < len(chemin_original):
                index += 1

            sous_chemin = self._ppv_jour(depart, arrivee, self.instance.distance_maximale_par_jour[jour])
            if chemin_complet and chemin_complet[-1] == sous_chemin[0]:
                chemin_complet.extend(sous_chemin[1:])
            else:
                chemin_complet.extend(sous_chemin)


        return chemin_complet
    


    def _recalculer_sites(self, sequence_hotels):

        return self._regenerer_chemin_ppv(sequence_hotels)

    def _hotels_atteignables(self, hotel_depart, jour):
        dmax = self.instance.distance_maximale_par_jour[jour]
        return [
            h for h in range(self.instance.nombre_hotels)
            if self.instance.matrice_distances[hotel_depart][h] <= dmax
        ]

    def _sites_atteignables(self, position, hotel_suivant, distance_restante):
        return [
            s for s in range(self.instance.nombre_hotels, self.instance.nombre_de_sites)
            if self.instance.masque_sites_visites[s]
            and self.instance.matrice_distances[position][s] + self.instance.matrice_distances[s][hotel_suivant] <= distance_restante
        ]
    
    def _reparer_apres_suppression_site(self, chemin_original, sequence_hotels):
        self.instance.reinitialiser_masque_sites()
        chemin_complet = []
        index = 0

        for jour in range(self.instance.nombre_de_jours):
            depart = sequence_hotels[jour]
            arrivee = sequence_hotels[jour + 1]
            etape_jour = []
            distance_initiale = 0
            anciens_sites = []

            if index < len(chemin_original) and chemin_original[index] == depart:
                index += 1

            position = depart
            while index < len(chemin_original) and chemin_original[index] != arrivee:
                site = chemin_original[index]
                anciens_sites.append(site)
                distance_initiale += self.instance.matrice_distances[position][site]
                position = site
                index += 1

            if index < len(chemin_original):
                distance_initiale += self.instance.matrice_distances[position][arrivee]
                index += 1

   


           
            if len(anciens_sites) < self._compter_sites_jour(depart, arrivee, chemin_original):
                

                chemin_jour_original = self._extraire_etape_jour(chemin_original, depart, arrivee)
                self._remettre_sites_supprimes(anciens_sites, chemin_jour_original)

                etape_jour = self._ppv_jour(depart, arrivee, distance_initiale)
            else:
                
                etape_jour = [depart] + anciens_sites + [arrivee]

            chemin_complet.extend(etape_jour)

        return chemin_complet
    
    def _compter_sites_jour(self, depart, arrivee, chemin):
        count = 0
        started = False
        for node in chemin:
            if node == depart:
                started = True
                continue
            if started:
                if node == arrivee:
                    break
                if node >= self.instance.nombre_hotels:
                    count += 1
        return count
    
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


        chemin_j1 = self._ppv_jour(hotel_avant, nouvel_hotel, self.instance.distance_maximale_par_jour[index - 1])
        chemin_j2 = self._ppv_jour(nouvel_hotel, hotel_apres, self.instance.distance_maximale_par_jour[index])


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
    
    def _bloc_hotel_present(self, chemin, depart, arrivee):
        """Vérifie si un bloc [depart ... arrivee] est présent dans le chemin."""
        started = False
        for node in chemin:
            if node == depart:
                started = True
            if started and node == arrivee:
                return True
        return False
    
    def _remettre_disponibles(self, sites):
        for s in sites:
            if s >= self.instance.nombre_hotels:
                self.instance.masque_sites_visites[s] = True




    def _inserer_nouvel_hotel_autour(self, hotel_avant, hotel_apres, sites_avant, sites_apres, jour_index):
        """
        Essaie différentes combinaisons de suppression de suffixes/préfixes
        pour rendre possible l'insertion d'un hôtel entre hotel_avant et hotel_apres.
        """
        for nb_sup_avant in range(len(sites_avant) + 1):
            suffixe = sites_avant[-nb_sup_avant:] if nb_sup_avant > 0 else []
            nouveaux_avant = sites_avant[:-nb_sup_avant] if nb_sup_avant > 0 else sites_avant[:]

            for nb_sup_apres in range(len(sites_apres) + 1):
                prefixe = sites_apres[:nb_sup_apres] if nb_sup_apres > 0 else []
                nouveaux_apres = sites_apres[nb_sup_apres:] if nb_sup_apres > 0 else sites_apres[:]

                self._remettre_disponibles(nouveaux_avant + nouveaux_apres)

                hotels_possibles = self._hotels_atteignables(hotel_avant, jour_index)
                for h in hotels_possibles:
                    d1 = self.instance.matrice_distances[hotel_avant][h]
                    d2 = self.instance.matrice_distances[h][hotel_apres]
                    if d1 + d2 <= self.instance.distance_maximale_par_jour[jour_index]:
                        return h, nouveaux_avant, nouveaux_apres

        return None, sites_avant, sites_apres 
    
    def _ppv_jour(self, depart, arrivee, distance_max, sites_a_eviter=None):
        position = depart
        distance_restante = distance_max
        etape = [depart]
        sites_a_eviter = set(sites_a_eviter or [])

        while distance_restante > 0:
            candidats = self._sites_atteignables(position, arrivee, distance_restante)
            if not candidats:
                break

            prioritaires = [s for s in candidats if s not in sites_a_eviter]
            if prioritaires:
                candidats = prioritaires

            def score_continuite(s):
                d = self.instance.matrice_distances[position][s]
                d_vers_arrivee = self.instance.matrice_distances[s][arrivee]
                d_directe = self.instance.matrice_distances[position][arrivee]
                bonus = 1.2 if d_vers_arrivee < d_directe else 1
                return d / bonus

            site = min(candidats, key=score_continuite)

            etape.append(site)
            distance_restante -= self.instance.matrice_distances[position][site]
            position = site
            self.instance.masque_sites_visites[site] = False

        etape.append(arrivee)
        return etape

    def _extraire_etape_jour(self, chemin, depart, arrivee):
        etape = []
        started = False
        for node in chemin:
            if node == depart:
                started = True
            if started:
                etape.append(node)
            if node == arrivee:
                break
        return etape
    
    def _remettre_sites_jour(self, chemin, depart, arrivee):
        started = False
        for node in chemin:
            if node == depart:
                started = True
                continue
            if node == arrivee:
                break
            if started and node >= self.instance.nombre_hotels:
                self.instance.masque_sites_visites[node] = True

    def _remettre_sites_supprimes(self, anciens_sites, chemin_jour):
        """Remet uniquement les sites supprimés dans la journée disponibles (présents dans anciens_sites mais pas dans chemin_jour)."""
        sites_restants = set(chemin_jour)
        for s in anciens_sites:
            if s not in sites_restants and s >= self.instance.nombre_hotels:
                self.instance.masque_sites_visites[s] = True






