def verifier_chemin(instance, chemin, sequence_hotels):
    erreurs = []

    if len(sequence_hotels) != instance.nombre_de_jours + 1:
        erreurs.append(
            f" Le nombre d'hôtels ({len(sequence_hotels)}) est invalide. "
            f"Attendu : {instance.nombre_de_jours + 1} (pour {instance.nombre_de_jours} jours)."
        )

    if chemin[0] != 0:
        erreurs.append(" Le chemin ne commence pas par l'hôtel 0.")

    if chemin[-1] != 1:
        erreurs.append(" Le chemin ne se termine pas par l'hôtel 1.")

    jour = 0
    position = chemin[0]
    distance_jour = 0
    sites_visites = set()
    index = 1

    for jour in range(instance.nombre_de_jours):
        if jour >= len(sequence_hotels) - 1:
            erreurs.append(f" Séquence d'hôtels incomplète pour le jour {jour + 1}.")
            break

        depart = sequence_hotels[jour]
        arrivee = sequence_hotels[jour + 1]
        distance_jour = 0

        if chemin[index - 1] != depart:
            erreurs.append(
                f" Mauvais hôtel de départ pour le jour {jour + 1} (attendu {depart}, trouvé {chemin[index - 1]})"
            )

        while index < len(chemin) and chemin[index] != arrivee:
            point = chemin[index]
            d = instance.matrice_distances[position][point]
            distance_jour += d

            if point >= instance.indice_premier_site:
                if point in sites_visites:
                    erreurs.append(f" Le site {point} a été visité plusieurs fois.")
                sites_visites.add(point)

            position = point
            index += 1

        if index < len(chemin):
            d = instance.matrice_distances[position][arrivee]
            distance_jour += d
            if distance_jour > instance.distance_maximale_par_jour[jour] + 1e-4:
                erreurs.append(
                    f" Jour {jour + 1} dépasse la distance maximale ({distance_jour:.2f} > {instance.distance_maximale_par_jour[jour]:.2f})"
                )
            index += 1
            position = arrivee
        else:
            erreurs.append(f" Le jour {jour + 1} est incomplet (arrivée non trouvée).")
            break

    if not erreurs:
        print(" Chemin valide !")
    else:
        print(" Erreurs détectées dans le chemin :")
        for err in erreurs:
            print(err)
        print("\n🛠️ Chemin complet analysé :")
        print(chemin)
        print("🛠️ Séquence d'hôtels attendue :")
        print(sequence_hotels)
