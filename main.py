# === Importations ===
import argparse
import time
from algo.gestion_instances import Instance
from algo.selection_initiale import SelectionInitiale
from alns.ALNS import ALNS
from algo.saveFile import save_solution_file
from check import verifier_chemin

def executer_avec_chrono(algo, *args):
    debut = time.time()
    resultat = algo(*args)
    duree = time.time() - debut
    return resultat, duree

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sélection initiale d'hôtels et sites.")
    parser.add_argument("--instance", type=str, required=True, help="Numéro de l'instance (1 à 24)")
    args = parser.parse_args()

    chemin_fichier_instance = f"data/instance{args.instance}.txt"
    instance = Instance(chemin_fichier_instance)

    print("\n\n==================  SÉLECTION INITIALE HÔTELS & SITES ==================")
    selection_initiale = SelectionInitiale(instance, seuil=0.99, nb_max_sequences=50)
    resultats_initiaux, temps_selection = executer_avec_chrono(selection_initiale.selectionner)

    # Initialisation du max_score à une valeur très faible avant la boucle
    max_score = float('-inf')
    

    print(f"\n Meilleur score estimé : {resultats_initiaux[0][0]:.2f}")
    print(f" {len(resultats_initiaux)} séquences retenues :\n")

    for i, (score, seq, chemin_detaille) in enumerate(resultats_initiaux, 1):
        ecart = 100 * (score / resultats_initiaux[0][0])

        index = 0
        for jour in range(instance.nombre_de_jours):
            jour_sites = []

            depart = chemin_detaille[index]
            index += 1

            arrivee = seq[jour + 1]
            while index < len(chemin_detaille) and chemin_detaille[index] != arrivee:
                jour_sites.append(chemin_detaille[index])
                index += 1

            # l'hôtel d'arrivée pour ce jour
            index += 1  # On saute l'hôtel d'arrivée pour le jour suivant
 


    meilleure_sequence = resultats_initiaux[0][1]
    meilleur_chemin = resultats_initiaux[0][2]

    print("\n DEBUG chemin_complet final :")
    print(meilleur_chemin)

    
    verifier_chemin(instance, meilleur_chemin, meilleure_sequence)

    print(f"Temps total sélection initiale : {temps_selection:.2f} secondes")
    print("=========================================================================\n")


    # #  Lancement de l'ALNS

    solution_initiale = {
        "hotels": meilleure_sequence,
        "chemin": meilleur_chemin
    }

    alns = ALNS(instance, solution_initiale)
    solution_finale = alns.optimiser()


    print(f"Meilleur chemin trouvé : {solution_finale['chemin']}")
    print(f"Hôtels : {solution_finale['hotels']}")
    print(f"Score : {alns.evaluer(solution_finale)}")
    print("\n Vérification finale via le checkeur :")
    verifier_chemin(instance, solution_finale["chemin"], solution_finale["hotels"])


        