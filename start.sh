#!/bin/bash

echo "Indiquez le numéro de l'instance à lancer (de 1 à 24)"
read -r instance

# Vérification que l'entrée est un nombre entre 1 et 24
if ! [[ "$instance" =~ ^[0-9]+$ ]] || [ "$instance" -lt 1 ] || [ "$instance" -gt 24 ]; then
    echo "Erreur : Veuillez entrer un nombre valide entre 1 et 24."
    read -r instance
fi

echo "Lancement de l'instance $instance..."
echo "----------------------------------------------------------"

# Exécution du script Python avec l'argument nommé --instance
python3 main.py --instance "$instance";
echo -e "\n\nFin de l'exécution du script."
