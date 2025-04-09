def calculer_ratio_journee(instance, chemin_complet, hotels, jour):
    """
    Calcule le ratio score / distance pour une journée donnée.
    """
    d = instance.matrice_distances
    s = instance.scores_des_sites

    hotel_depart = hotels[jour]
    hotel_arrivee = hotels[jour + 1]

    index = 0
    sites = []

    while index < len(chemin_complet):
        if chemin_complet[index] == hotel_depart:
            index += 1
            while index < len(chemin_complet) and chemin_complet[index] != hotel_arrivee:
                sites.append(chemin_complet[index])
                index += 1
            break
        index += 1

    if not sites:
        return float('inf')

    distance_total = d[hotel_depart][sites[0]] + \
                     sum(d[sites[i]][sites[i+1]] for i in range(len(sites)-1)) + \
                     d[sites[-1]][hotel_arrivee]

    score_total = sum(s[site] for site in sites)
    if score_total == 0:
        return float('inf')

    return distance_total / score_total

def extraire_sites_du_jour(chemin, hotel_depart, hotel_arrivee):
    i = chemin.index(hotel_depart)
    j = chemin.index(hotel_arrivee, i + 1)
    return chemin[i+1:j]

def supprimer_jour_du_chemin(chemin, hd, ha):
    nouveau = []
    i = 0
    while i < len(chemin):
        if chemin[i] == hd:
            j = i + 1
            while j < len(chemin) and chemin[j] != ha:
                j += 1
            j += 1
            i = j
        else:
            nouveau.append(chemin[i])
            i += 1
    return nouveau

def ratio_distance_sur_score(d, s, chain):
    distance = sum(d[chain[i]][chain[i+1]] for i in range(len(chain)-1))
    score = sum(s[elt] for elt in chain)
    return distance / score if score > 0 else float('inf')

def extraire_plus_anormal(valeurs, key=lambda x: x):
    moyenne = sum(key(v) for v in valeurs) / len(valeurs)
    return max(valeurs, key=lambda x: abs(key(x) - moyenne))
