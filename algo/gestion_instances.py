import numpy as np


class Instance:
    def __init__(self, fichier):
        self.nombre_de_sites, self.nombre_hotels, self.nombre_de_jours, \
        self.distance_maximale_par_jour, self.matrice_distances, self.scores_des_sites = self.lire_instance(fichier)
        self.indice_premier_site = self.nombre_hotels + 2
    
        # 1 = disponible, 0 = visité
        self.masque_sites_visites = np.ones(self.nombre_de_sites, dtype=bool)

    def reinitialiser_masque_sites(self):
        self.masque_sites_visites[:] = True

    def marquer_site_comme_visite(self, index):
        self.masque_sites_visites[index] = False

    def est_disponible(self, index):
        return self.masque_sites_visites[index]


    def lire_instance(self, fichier):
        """
        Lit les données du fichier d'entrée et initialise les paramètres du problème.

        :param fichier: Chemin du fichier contenant les données.
        :return: Tuple contenant les valeurs des paramètres du problème.
        """
        with open(fichier, 'r') as fichier_entree:
            lignes = [ligne.strip() for ligne in fichier_entree.readlines() if ligne.strip()]
        nombre_de_sites, nombre_hotels, nombre_de_jours = map(int, lignes[0].split())
        distance_maximale_par_jour = list(map(float, lignes[1].split()))
        del lignes[1] 
        liste_coordonnees = []
        scores_des_sites = []        
        for ligne in lignes[1:]:
            valeurs = ligne.split()
            if len(valeurs) == 3:
                x, y, score = map(float, valeurs)
                liste_coordonnees.append((x, y))
                scores_des_sites.append(int(score))
        matrice_distances = self.calculer_matrice_distances(liste_coordonnees)
        return nombre_de_sites, nombre_hotels, nombre_de_jours, distance_maximale_par_jour, matrice_distances, scores_des_sites

    def calculer_matrice_distances(self, liste_coordonnees):
        """
        Calcule la matrice des distances euclidiennes entre tous les sites.

        :param liste_coordonnees: Liste des coordonnées des sites.
        :return: Matrice des distances.
        """
        nombre_sites = len(liste_coordonnees)
        matrice_distances = np.zeros((nombre_sites, nombre_sites))
        for i in range(nombre_sites):
            for j in range(nombre_sites):
                if i != j:
                    matrice_distances[i][j] = np.sqrt(
                        (liste_coordonnees[i][0] - liste_coordonnees[j][0]) ** 2 +
                        (liste_coordonnees[i][1] - liste_coordonnees[j][1]) ** 2
                    )
        return matrice_distances
