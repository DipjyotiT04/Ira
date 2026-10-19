#!/bin/bash
# Create Ira model from Modelfile
set -e

MODELFILE="models/Modelfile.ira"
TAG="ira"

echo "Creating model '$TAG' from $MODELFILE..."
ollama create "$TAG" -f "$MODELFILE"

echo "Done! Test with: ollama run $TAG"