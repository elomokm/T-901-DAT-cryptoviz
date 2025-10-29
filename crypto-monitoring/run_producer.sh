#!/bin/zsh

# Script pour lancer le producer avec la config correcte

# Active le venv
source /Users/elomokoumassoun/Epitech/T-901-DAT-cryptoviz/crypto-monitoring/.venv/bin/activate

# Unset toutes les anciennes variables qui pourraient interférer
unset PRODUCER_ACKS
unset PRODUCER_LINGER_MS
unset PRODUCER_BATCH_SIZE
unset PRODUCER_COMPRESSION

# Config pour le producer (valeurs par défaut dans le code sont OK)
export SEND_EVERY_POLL=1
export POLL_INTERVAL_SEC=10

# Lance le producer
python3 crypto_producer.py
