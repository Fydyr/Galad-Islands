#!/bin/bash
# Script de conversion MP3 -> OGG avec ffmpeg

for f in *.mp3; do
    # Supprime l'extension .mp3 pour créer le nom de sortie
    base="${f%.mp3}"
    echo "Conversion de $f en ${base}.ogg ..."
    ffmpeg -i "$f" -c:a libvorbis -b:a 192k "${base}.ogg"
done

echo "Conversion terminée !"
