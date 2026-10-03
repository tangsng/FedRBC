#!/bin/bash
# 渲染验证页（Figure 5 β扫描 / Figure 6 Non-IID / Figure 8 声誉）
cd ~/cmc_build || exit 1
cp FedRBC_cmc.pdf ~/uploads/FedRBC_cmc.pdf
pdftoppm -png -r 70 -f 14 -l 14 FedRBC_cmc.pdf ~/uploads/fin14
pdftoppm -png -r 70 -f 18 -l 18 FedRBC_cmc.pdf ~/uploads/fin18
ls ~/uploads/fin*.png
