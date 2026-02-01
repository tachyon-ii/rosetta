cat tests/longer.txt | while read line; do                    
  echo "=== $line ==="
  echo "$line" | \
    ./tools/normalize.py | \
    ./udpipe/udpipe --tokenize --tag udpipe/english-ud-1.2-160523.udpipe 2>/dev/null | \
    ./tools/translate.py dictionaries/en_hi.txt
  echo
done