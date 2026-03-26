#!/bin/bash
echo 'Building rubric index...'
python scripts/build_embeddings.py
python scripts/build_index.py
echo 'Index ready.'
