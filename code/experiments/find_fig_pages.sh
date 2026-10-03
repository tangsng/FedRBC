#!/bin/bash
# 定位 PDF 中各 Figure 的页码
cd ~/cmc_build || exit 1
for p in $(seq 1 30); do
  txt=$(pdftotext -f $p -l $p FedRBC_cmc.pdf - 2>/dev/null | tr '\n' ' ')
  for f in 1 2 3 4 5 6 7 8 9; do
    echo "$txt" | grep -q "Figure $f:" && echo "Figure$f -> page $p"
  done
done
