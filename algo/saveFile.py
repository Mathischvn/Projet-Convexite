def save_solution_file(paths, instance_number):
    """
    Enregistre la solution dans un fichier .sol respectant le format demandé.

    :param solution_value: Valeur de la solution (ex: coût ou distance totale).
    :param paths: Liste de listes, chaque sous-liste représentant un chemin journalier.
                  Peut aussi être une liste plate (qui sera automatiquement convertie).
    :param instance_number: Numéro de l’instance (utilisé pour nommer le fichier).
    """
    filename = f"Instance{instance_number}.sol"

    with open(f'resultats/{filename}', 'w') as f:

        # Si paths est une liste plate (ex: [42, 12, 33]) on l'encapsule
        if paths and all(isinstance(p, (str, int)) for p in paths):
            paths = [paths]

        for day_path in paths:
            line = ' '.join(map(str, day_path))
            f.write(f"{line}\n")

    print(f"✅ Fichier solution sauvegardé sous le nom {filename}")
