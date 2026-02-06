# Running Deduplication on Linux Server

You're now on: `cuda.sentienos.com` (CentOS Stream 8)

## Quick Setup (5 steps)

### 1. Install Python 3 and pip (if needed)

```bash
# Check Python version
python3 --version

# If not installed or old version:
dnf install -y python3 python3-pip python3-devel
```

### 2. Create Virtual Environment

```bash
cd /var/www/rosetta

# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Start Qdrant Docker

```bash
# Start Qdrant
docker compose up -d

# Verify it's running
docker ps

# Should see:
# CONTAINER ID   IMAGE                COMMAND                  CREATED         STATUS         PORTS                    NAMES
# xxxxx          qdrant/qdrant:latest "/qdrant/entrypoint.…"   X seconds ago   Up X seconds   0.0.0.0:6333->6333/tcp   rosetta-qdrant

# Test the API
curl http://localhost:6333/collections
# Should return: {"result":{"collections":[]}}
```

### 4. Index Wiktionary Data (~15-20 minutes)

```bash
# Activate venv if not already
source venv/bin/activate

# Index the data
python3 tools/deduplicate_with_qdrant.py index \
    dictionaries/wiktionary/wiktionary.hashed.txt

# You'll see:
# Loading entries from dictionaries/wiktionary/wiktionary.hashed.txt...
# Loaded 100,000 entries...
# Loaded 200,000 entries...
# ...
# ✓ Indexing complete: 1,671,871 entries
```

### 5. Find Duplicates

**Option A: Sample Test (Fast - 5 minutes)**
```bash
# Test on 50k sample first
python3 tools/deduplicate_with_qdrant.py find \
    --threshold 0.90 \
    --sample 50000
```

**Option B: Full Dataset (Slow - 1-2 hours)**
```bash
# Run in background with nohup so it continues if you disconnect
nohup python3 tools/deduplicate_with_qdrant.py find \
    --threshold 0.90 \
    > dedup_find.log 2>&1 &

# Check progress
tail -f dedup_find.log

# Or check the process
ps aux | grep deduplicate
```

### 6. Export Results

```bash
python3 tools/deduplicate_with_qdrant.py export \
    --output duplicates_mapping.json
```

## Run Everything in One Go

```bash
# Setup script
cd /var/www/rosetta

# Install Python deps
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Start Docker
docker compose up -d
sleep 5

# Index data
python3 tools/deduplicate_with_qdrant.py index \
    dictionaries/wiktionary/wiktionary.hashed.txt

# Find duplicates (run in background)
nohup python3 tools/deduplicate_with_qdrant.py find \
    --threshold 0.90 \
    > dedup_find.log 2>&1 &

# Monitor progress
tail -f dedup_find.log
```

## Troubleshooting

### "docker compose: command not found"

Try with hyphen:
```bash
docker-compose up -d
```

### "Permission denied" for Docker

```bash
# Add your user to docker group
usermod -aG docker suman

# Or run as root (you're already root)
# Just use: docker compose up -d
```

### Monitor Progress While Running

```bash
# Watch the log file
tail -f dedup_find.log

# Check how many duplicates found so far
grep "found.*with duplicates" dedup_find.log | tail -1

# Check CPU usage
top

# Check Docker logs
docker logs rosetta-qdrant
```

### Stop/Restart

```bash
# Stop Qdrant
docker compose down

# Restart
docker compose up -d

# Kill the find process if needed
pkill -f deduplicate_with_qdrant
```

## Performance on This Server

Since this is a CUDA server (likely has GPU), the server specs should be:
- Multi-core CPU: Much faster than your M4 Mac
- More RAM: Can handle larger datasets
- Better I/O: Faster disk access

**Expected times:**
- Index 1.67M entries: ~10-15 minutes (vs 20-30 on your Mac)
- Find duplicates: ~45-60 minutes (vs 1-2 hours on your Mac)

## After It Completes

You'll have:
1. `./qdrant_data/` - Qdrant database with all vectors
2. `./qdrant_data/canonical_mapping.pkl` - Duplicate mapping
3. `duplicates_mapping.json` - Human-readable mapping

Download the results:
```bash
# On your Mac:
scp suman@cuda.sentienos.com:/var/www/rosetta/duplicates_mapping.json .
scp suman@cuda.sentienos.com:/var/www/rosetta/dedup_find.log .
```

## Screen Session (Recommended)

Use `screen` so you can disconnect and reconnect:

```bash
# Start screen session
screen -S dedup

# Run your commands
source venv/bin/activate
python3 tools/deduplicate_with_qdrant.py find --threshold 0.90

# Detach: Press Ctrl+A then D

# Reconnect later
screen -r dedup

# List sessions
screen -ls
```

Good luck! The server should handle this much better than your Mac.
