#!/bin/bash
# Script de conversion MP3/WAV -> OGG avec ffmpeg
# Il convertit tous les fichiers .mp3 et .wav du répertoire courant en .ogg
# Usage: ./sound-convert.sh

for f in *.mp3 and *.wav; do
    # Supprime l'extension .mp3 pour créer le nom de sortie
    base="${f%.mp3}"
    echo "Conversion de $f en ${base}.ogg ..."
    ffmpeg -i "$f" -c:a libvorbis -b:a 192k "${base}.ogg"
done

echo "Conversion terminée !"
