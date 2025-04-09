import heapq

class SelectionInitiale:

    """
    - La sélection des séquences d'hôtels via une exploration quasi exhaustive (Branch and Bound).
    - La génération associée d'un parcours optimisé des sites visités chaque jour, selon les distances maximales.

    Entrée :
        - instance : Objet instance contenant les données de l'instance courante (nombre de jours, hôtels, sites, etc.)
        - seuil : Seuil relatif pour conserver les solutions proches du meilleur résultat trouvé.
        - nb_max_sequences : Nombre maximal de séquences distinctes à retourner.
        - seuil_activation_pruning : Limite au-delà de laquelle le mécanisme de pruning par préfixe s'active.

    Sortie :
        - Une liste de tuples contenant (score_total, sequence_hotels, chemin_detaille_sites).
          Chaque séquence représente un ensemble compétitif d'hôtels et de sites associés.
    """
    def __init__(self, instance, seuil=0.90, nb_max_sequences=5, seuil_activation_pruning=8):
        """
        Initialise l'objet SelectionInitiale avec les paramètres de sélection et d'élagage.
        """
        self.instance = instance
        self.seuil_relatif = seuil
        self.nb_max_sequences = nb_max_sequences
        self.seuil_activation_pruning = seuil_activation_pruning
        self.ensemble_sequences_valides = []  # [(score, sequence)]
        self.ensemble_sequences_testees = set()
        self.meilleur_score = -1
        self.score_max_site = max(self.instance.scores_des_sites[self.instance.nombre_hotels:])

        self.scores_par_prefixe = {}  
        self.prefixes_a_exclure = set()
        self.longueur_min_prefixe = max(3, self.instance.nombre_de_jours - 1)
        self.nb_essais_min_prefixe = 5
        self.seuil_prefixe_mauvais = 0.85

        self.compteur_filtre_distance_hotel = 0
        self.compteur_filtre_impossible_vers_arrivee = 0
        self.compteur_prefixes_exclus = 0
        self.total_sequences_generées = 0




    def selectionner(self):
        """
        Lance le processus de sélection initiale, retourne les meilleures séquences trouvées selon les critères.
        Affiche pour chaque solution le détail jour par jour et la distance réelle.
        """
        chemins_possibles = self.generer_chemins_hotels_valides()
        print(f" {len(chemins_possibles)} chemins valides trouvés\n")

        for chemin in chemins_possibles:
            score, chemin_detaille = self.evaluer_chemin(chemin)
            self.ensemble_sequences_valides.append((score, chemin, chemin_detaille))
            if score > self.meilleur_score:
                self.meilleur_score = score

        seuil_valeur = self.seuil_relatif * self.meilleur_score
        candidats = [
            (score, seq, chemin_complet) for score, seq, chemin_complet in self.ensemble_sequences_valides
            if score >= seuil_valeur
        ]

        candidats.sort(reverse=True)

        finales = []
        vues = set()
        for score, seq, chemin_detaille in candidats:
            h = tuple(seq)
            if h not in vues:
                vues.add(h)
                finales.append((score, seq, chemin_detaille))
            if len(finales) >= self.nb_max_sequences:
                break

        print(f"\n Meilleur score estimé : {finales[0][0]:.2f}")
        print(f" {len(finales)} séquences retenues :\n")

        for i, (score, seq, chemin_detaille) in enumerate(finales, 1):
            ecart = 100 * (score / finales[0][0])
            print(f"{i}. Score = {score:.2f} ({ecart:.2f}%)")
            print(f"Hôtels sélectionnés : {seq}")
            print("   Chemin complet jour par jour :")
            print(f"   {chemin_detaille}")

            index = 0
            for jour in range(self.instance.nombre_de_jours):
                depart = chemin_detaille[index]
                arrivee = seq[jour + 1]
                jour_sites = []
                etape = [depart]

                index += 1
                while index < len(chemin_detaille) and chemin_detaille[index] != arrivee:
                    jour_sites.append(chemin_detaille[index])
                    etape.append(chemin_detaille[index])
                    index += 1

                if index < len(chemin_detaille):
                    etape.append(arrivee)
                    index += 1

                distance = 0
                for k in range(1, len(etape)):
                    a = etape[k - 1]
                    b = etape[k]
                    distance += self.instance.matrice_distances[a][b]



        return finales


    def generer_chemins_hotels_valides(self):
        chemins_valides = []
        self._explorer_chemins_hotel([0], 0, chemins_valides)
        return chemins_valides

    def _explorer_chemins_hotel(self, chemin_actuel, jour, chemins_valides):
        if jour == self.instance.nombre_de_jours:
            if chemin_actuel[-1] == 1:
                chemins_valides.append(chemin_actuel[:])
            return

        depart = chemin_actuel[-1]
        dmax = self.instance.distance_maximale_par_jour[jour]

        for hotel_suivant in range(self.instance.nombre_hotels + 2):
            if jour == self.instance.nombre_de_jours - 1 and hotel_suivant != 1:
                continue

            distance = self.instance.matrice_distances[depart][hotel_suivant]
            if distance <= dmax:
                chemin_actuel.append(hotel_suivant)
                self._explorer_chemins_hotel(chemin_actuel, jour + 1, chemins_valides)
                chemin_actuel.pop()



    def explorer(self, chemin_actuel, jour):
        if jour == self.instance.nombre_de_jours:
            self.gerer_sequence_terminee(chemin_actuel)
        else:
            self.gerer_exploration_hotel(chemin_actuel, jour)


    def gerer_sequence_terminee(self, chemin_actuel):
        chemin_complet = chemin_actuel + [1]
        score, chemin_detaille = self.evaluer_chemin(chemin_complet)
        self.ensemble_sequences_valides.append((score, chemin_complet[:], chemin_detaille))

        if score > self.meilleur_score:
            self.meilleur_score = score

        if self.instance.nombre_hotels > self.seuil_activation_pruning:
            for l in range(self.longueur_min_prefixe, len(chemin_complet) - 1):
                prefixe = tuple(chemin_complet[:l])
                if prefixe not in self.scores_par_prefixe:
                    self.scores_par_prefixe[prefixe] = []
                self.scores_par_prefixe[prefixe].append(score)

                if len(self.scores_par_prefixe[prefixe]) >= self.nb_essais_min_prefixe:
                    moyenne = sum(self.scores_par_prefixe[prefixe]) / len(self.scores_par_prefixe[prefixe])
                    if moyenne < self.meilleur_score * self.seuil_prefixe_mauvais:
                        self.prefixes_a_exclure.add(prefixe)

    def gerer_exploration_hotel(self, chemin_actuel, jour):
        

        dmax = self.instance.distance_maximale_par_jour[jour]
        print(f"\n Exploration des hôtels pour le jour {jour + 1} depuis {chemin_actuel[-1]} (dmax = {dmax:.2f})")
        depart = chemin_actuel[-1]

        for hotel in range(self.instance.nombre_hotels + 2):
            dist_depart = self.instance.matrice_distances[depart][hotel]
            if dist_depart > dmax:
                self.compteur_filtre_distance_hotel += 1
                continue

            if jour == self.instance.nombre_de_jours - 1:
                dist_vers_final = self.instance.matrice_distances[hotel][1]
                if dist_vers_final > dmax:
                    self.compteur_filtre_impossible_vers_arrivee += 1
                    continue


            print(" retenu")

            nouveau_chemin = chemin_actuel + [hotel]
            prefixe = tuple(nouveau_chemin)

            if self.instance.nombre_hotels > self.seuil_activation_pruning:
                for l in range(self.longueur_min_prefixe, len(nouveau_chemin) + 1):
                    sous_prefixe = tuple(nouveau_chemin[:l])
                    if sous_prefixe in self.prefixes_a_exclure:
                        self.compteur_prefixes_exclus += 1
                        break
                else:
                    if prefixe not in self.ensemble_sequences_testees:
                        self.ensemble_sequences_testees.add(prefixe)
                        self.explorer(nouveau_chemin, jour + 1)
                continue

            if prefixe in self.ensemble_sequences_testees:
                continue

            self.ensemble_sequences_testees.add(prefixe)
            self.explorer(nouveau_chemin, jour + 1)





    def evaluer_chemin(self, hotels):
        if len(hotels) != self.instance.nombre_de_jours + 1:
            return 0, []

        for jour in range(self.instance.nombre_de_jours):
            depart = hotels[jour]
            arrivee = hotels[jour + 1]
            dist = self.instance.matrice_distances[depart][arrivee]
            if dist > self.instance.distance_maximale_par_jour[jour]:
                print(f" Chemin rejeté : distance {depart} ➜ {arrivee} = {dist:.2f} > {self.instance.distance_maximale_par_jour[jour]:.2f}")
                return 0, []

        self.instance.reinitialiser_masque_sites()
        score_total = 0
        chemin_complet = [hotels[0]]

        for jour in range(self.instance.nombre_de_jours):
            chemin_jour = []
            score_total = self.parcourir_journee(hotels, jour, score_total, chemin_jour)
            chemin_complet.extend(chemin_jour[1:])

        return score_total, chemin_complet


    def parcourir_journee(self, hotels, jour, score_total, chemin_complet):
        depart = hotels[jour]
        arrivee = hotels[jour + 1]
        position = depart
        distance_max = self.instance.distance_maximale_par_jour[jour]

        etape = []

        if not chemin_complet or chemin_complet[-1] != depart:
            etape.append(depart)

        distance_parcourue = 0

        while True:
            candidats = []
            sites_valides = self.sites_atteignables(position, arrivee, distance_max - distance_parcourue)

            for site in sites_valides:
                d_site = self.instance.matrice_distances[position][site]
                d_retour = self.instance.matrice_distances[site][arrivee]

                if distance_parcourue + d_site + d_retour <= distance_max:
                    score_site = self.instance.scores_des_sites[site]
                    ratio = float('inf') if score_site == 0 else d_site / score_site
                    candidats.append((site, ratio, d_site, d_retour))

            if not candidats:
                break

            site_choisi, _, d_site, _ = min(candidats, key=lambda x: x[1])
            etape.append(site_choisi)
            score_total += self.instance.scores_des_sites[site_choisi]
            distance_parcourue += d_site
            position = site_choisi
            self.instance.marquer_site_comme_visite(site_choisi)

        d_retour = self.instance.matrice_distances[position][arrivee]
        distance_parcourue += d_retour
        etape.append(arrivee)
        chemin_complet.extend(etape)

        return score_total




    def evaluer_distance(self, chemin):
        total = 0
        for i in range(1, len(chemin)):
            total += self.instance.matrice_distances[chemin[i - 1]][chemin[i]]
        return total


    def hotels_atteignables(self, hotel_depart, jour):
        dmax = self.instance.distance_maximale_par_jour[jour]
        hotels_valides = []

        for h in range(self.instance.nombre_hotels + 2):
            d_depart = self.instance.matrice_distances[hotel_depart][h]
            if d_depart > dmax:
                continue  

    def hotels_atteignables(self, hotel_depart, jour):
        dmax = self.instance.distance_maximale_par_jour[jour]
        hotels_valides = []

        for h in range(self.instance.nombre_hotels + 2):
            d_depart = self.instance.matrice_distances[hotel_depart][h]
            if d_depart > dmax:
                continue  

            if jour == self.instance.nombre_de_jours - 1:
                d_vers_final = self.instance.matrice_distances[h][1]
                if d_vers_final > dmax:
                    continue

            hotels_valides.append(h)

        return hotels_valides

  
    def sites_atteignables(self, position, hotel_suivant, distance_restante):
        sites_valides = []
        

        for site in range(self.instance.indice_premier_site, self.instance.nombre_de_sites):
            if self.instance.masque_sites_visites[site]:
                d1 = self.instance.matrice_distances[position][site]
                d2 = self.instance.matrice_distances[site][hotel_suivant]
                total = d1 + d2
                if total <= distance_restante:
                    sites_valides.append(site)

        return sites_valides