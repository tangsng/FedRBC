#!/bin/bash
# 排查 V100 上的图数据状态
cd /home/user1/projects/fedrbc || exit 1
echo "=== 1. plots_sim.py 的 TAG ==="
grep '^TAG' code/utils/plots_sim.py
echo ""
echo "=== 2. figures 目录时间戳 ==="
ls -la --time-style=+%m-%d_%H:%M results/figures/ | grep -E 'fig(5|6|7|8|9|10|1_|2_|3_)' | awk '{print $6, $7}'
echo ""
echo "=== 3. beta sweep v5 数据量（b=0.1/0.2/0.4）==="
ls results/raw/ | grep -cE '_a0\.5_b0\.[124]_sybil_s[0-9]+_v5_summary' || echo 0
echo "=== 4. NonIID v5 数据量（a=0.1/1.0）==="
ls results/raw/ | grep -cE '_a0\.[12]_b0\.3_sybil_s[0-9]+_v5_summary' || echo 0
echo "=== 5. beta/noniid sweep 旧 tag 数据量 ==="
ls results/raw/ | grep -E '_a0\.5_b0\.[124]_sybil|_a0\.[12]_b0\.3_sybil' | grep -cE '_v7_|_bl_'
echo "=== 6. v5 rep.npy 是否存在（fig9 需要）==="
ls results/raw/fedrbc_a0.5_b0.3_sybil_s*_v5_rep.npy 2>/dev/null | head -5
echo "=== 7. mttc.csv（fig10 数据源）==="
ls -la --time-style=+%m-%d_%H:%M results/raw/mttc.csv 2>/dev/null | awk '{print $6, $7}'
echo "=== 8. python 快速验证 load_summary beta=0.1 ==="
cd /home/user1/projects/fedrbc && python3 -c "
import sys; sys.path.insert(0, 'code/utils')
import os; os.chdir('/home/user1/projects/fedrbc')
from plots_sim import load_summary
ds = load_summary('fedrbc', '0.5', '0.1', 'sybil')
print('beta=0.1 v5 数据条数:', len(ds))
ds2 = load_summary('fedrbc', '0.5', '0.3', 'sybil')
print('beta=0.3 v5 数据条数:', len(ds2))
"
