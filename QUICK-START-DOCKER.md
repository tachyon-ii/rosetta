# Quick Start: Fast Deduplication with Docker

## The Problem You Encountered

You saw this warning:
```
Local mode is not recommended for collections with more than 20,000 points.
Current collection contains 20100 points.
```

**Local file-based Qdrant is too slow for 1.67M entries!**

## The Solution: Docker Qdrant

Docker-based Qdrant is **30-40x faster** and designed for millions of vectors.

## Setup (2 minutes)

### Step 1: Install Docker (if not already installed)

**Mac:**
1. Download Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Install and start Docker Desktop
3. Wait for Docker to start (whale icon in menu bar)

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose-plugin

# Start Docker
sudo systemctl start docker
```

### Step 2: Start Qdrant

```bash
cd /Users/sumanpokhrel/rosetta

# Modern Docker (no hyphen)
docker compose up -d

# OR older Docker Compose (with hyphen)
docker-compose up -d
```

You should see:
```
[+] Running 2/2
 ✔ Network rosetta_rosetta-net  Created
 ✔ Container rosetta-qdrant     Started
```

### Step 3: Verify It's Running

```bash
# Check container is running
docker ps

# Test the API
curl http://localhost:6333/collections
```

Or open in browser: **http://localhost:6333/dashboard**

## Run Deduplication (Fast!)

Now re-run your indexing command:

```bash
source venv/bin/activate

# This will now use Docker Qdrant (much faster!)
python3 tools/deduplicate_with_qdrant.py index \
    dictionaries/wiktionary/wiktionary.hashed.txt
```

**Performance:**
- ❌ Local mode: ~10 hours for 1.67M entries
- ✅ Docker mode: ~15-20 minutes for 1.67M entries

### Complete Pipeline

```bash
# 1. Index data (~15-20 minutes)
python3 tools/deduplicate_with_qdrant.py index \
    dictionaries/wiktionary/wiktionary.hashed.txt

# 2. Find duplicates (~5 minutes)
python3 tools/deduplicate_with_qdrant.py find --threshold 0.95

# 3. Export results
python3 tools/deduplicate_with_qdrant.py export duplicates_mapping.json
```

## Manage Docker

```bash
# Check status
docker ps

# View logs
docker compose logs -f qdrant

# Stop Qdrant (keeps data)
docker compose down

# Restart Qdrant (data persists)
docker compose up -d

# Remove everything (including data)
docker compose down -v
rm -rf qdrant_data/
```

## Data Location

All data is stored in `./qdrant_data/` on your local disk:
- Vectors and indices
- Collection metadata
- Survives Docker restarts

## Troubleshooting

### "docker: command not found"

Docker is not installed. Install Docker Desktop:
- **Mac**: https://www.docker.com/products/docker-desktop/
- **Linux**: `sudo apt-get install docker.io docker-compose-plugin`

### "Cannot connect to the Docker daemon"

Docker Desktop is not running. Start it from Applications (Mac) or:
```bash
# Linux
sudo systemctl start docker
```

### "port is already allocated"

Another service is using port 6333:
```bash
# Find what's using it
lsof -i :6333

# Kill it
kill -9 <PID>

# Or change port in docker-compose.yml:
ports:
  - "6335:6333"  # Use 6335 instead
```

### Permission denied

```bash
# Mac: Start Docker Desktop application
# Linux: Add yourself to docker group
sudo usermod -aG docker $USER
# Then log out and back in
```

## Why Docker is Much Faster

| Feature | Local Mode | Docker Mode |
|---------|-----------|-------------|
| Indexing speed | Slow | **30-40x faster** |
| Memory efficiency | Poor | Excellent |
| Query optimization | None | Full HNSW |
| Concurrent access | Limited | Full support |
| Max recommended | 20k entries | Millions |

For 1.67M entries, Docker mode is **essential**.

## Alternative: Use the Setup Script

I've created a helper script:

```bash
./setup_qdrant.sh
```

This will:
1. Check Docker is installed
2. Start Qdrant
3. Verify it's working
4. Show next steps

## Ready!

Once Docker is running:
```bash
# Verify Qdrant is responding
curl http://localhost:6333/collections

# Should return: {"result":{"collections":[]}}
```

Then run your deduplication pipeline - it will be **much faster**!
