#!/bin/bash
# Script de conversion MP3/WAV -> OGG avec ffmpeg (requis ffmpeg et libvorbis installé)
# Il convertit tous les fichiers .mp3 et .wav du répertoire courant en .ogg
# Usage: ./sound-convert.sh

for f in *.mp3 and *.wav; do
    # Détermine le nom de base selon l'extension (.mp3 ou .wav)
    case "$f" in
        *.mp3) base="${f%.mp3}" ;;
        *.wav) base="${f%.wav}" ;;
        *)     base="${f%.*}" ;; # fallback
    esac
    echo "Conversion de $f en ${base}.ogg ..."
    ffmpeg -i "$f" -c:a libvorbis -b:a 192k "${base}.ogg"
done

echo "Conversion terminée !"
