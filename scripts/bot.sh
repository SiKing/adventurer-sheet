#!/bin/bash -e

docker compose up -d
cd src
python -m bot 2>&1 | tee session.log
