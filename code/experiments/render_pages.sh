#!/bin/bash
# 渲染包含图的页面为 PNG
cd ~/cmc_build || exit 1
for p in 6 7 9 13 14 18; do
  pdftoppm -png -r 70 -f $p -l $p FedRBC_cmc.pdf ~/uploads/pg$p
done
ls ~/uploads/pg*.png
