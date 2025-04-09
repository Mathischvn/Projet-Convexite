def save_solution_file(paths, score, instance_number):
    filename = f"Instance{instance_number}.sol"

    with open(f'resulats/{filename}', 'w') as f:
        f.write(f"{score}\n")

        if paths and all(isinstance(p, (str, int)) for p in paths):
            paths = [paths]

        for day_path in paths:
            line = ' '.join(map(str, day_path))
            f.write(f"{line}\n")

    print(f"✅ Fichier solution sauvegardé sous le nom {filename}")
