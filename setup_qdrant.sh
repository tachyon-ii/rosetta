#!/bin/bash
# Quick setup script for Qdrant-based deduplication

set -e

echo "========================================"
echo "Qdrant Deduplication Setup"
echo "========================================"
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo
    echo "Please install Docker Desktop:"
    echo "  Mac: https://docs.docker.com/desktop/install/mac-install/"
    echo "  Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

echo "✓ Docker found"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed"
    echo
    echo "Please install docker-compose or use Docker Desktop (includes compose)"
    exit 1
fi

echo "✓ docker-compose found"
echo

# Start Qdrant
echo "Starting Qdrant Docker container..."
docker-compose up -d

echo
echo "Waiting for Qdrant to start..."
sleep 5

# Check if Qdrant is responding
if curl -s http://localhost:6333/collections > /dev/null; then
    echo "✓ Qdrant is running at http://localhost:6333"
    echo
    echo "========================================"
    echo "Setup Complete!"
    echo "========================================"
    echo
    echo "Next steps:"
    echo
    echo "1. Activate Python environment:"
    echo "   source venv/bin/activate"
    echo
    echo "2. Index your data:"
    echo "   python3 tools/deduplicate_with_qdrant.py index dictionaries/wiktionary/wiktionary.hashed.txt"
    echo
    echo "3. Find duplicates:"
    echo "   python3 tools/deduplicate_with_qdrant.py find --threshold 0.95"
    echo
    echo "4. Export mapping:"
    echo "   python3 tools/deduplicate_with_qdrant.py export duplicates_mapping.json"
    echo
    echo "To stop Qdrant:"
    echo "   docker-compose down"
    echo
    echo "Qdrant dashboard: http://localhost:6333/dashboard"
    echo
else
    echo "❌ Error: Qdrant is not responding"
    echo
    echo "Check logs with:"
    echo "   docker-compose logs qdrant"
    exit 1
fi
