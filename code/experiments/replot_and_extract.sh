#!/bin/bash
# 重新生成全部图 + 提取 β/α 扫描新数据
cd /home/user1/projects/fedrbc || exit 1
python3 code/utils/plots_sim.py 2>&1 | tail -3
echo "=== β 扫描（sybil, 3 seeds, v5）==="
python3 -c "
import json, glob, statistics as st
def ms(m, a, b, atk, tag='v5', k='f1'):
    fs = [f for f in glob.glob('results/raw/%s_a%s_b%s_%s_s*_summary.json' % (m, a, b, atk))]
    fs = [f for f in fs if json.load(open(f))['config'].get('tag','') == tag]
    fs = [f for f in fs if not f.startswith('results/raw/ciciot_')]
    v = [json.load(open(f))['final'][k] for f in fs]
    v = [x for x in v if x == x]
    return (st.mean(v), st.stdev(v) if len(v) > 1 else 0, len(v)) if v else (float('nan'), 0, 0)
M = ['fedrbc', 'raid', 'fedgt', 'eiffel']
for b in ['0.1','0.2','0.3','0.4']:
    row = {m: '%.3f' % ms(m, '0.5', b, 'sybil')[0] for m in M}
    print('beta=%s  %s' % (b, row))
print('--- NonIID ---')
for a in ['0.1','0.5','1.0']:
    row = {m: '%.3f' % ms(m, a, '0.3', 'sybil')[0] for m in M}
    print('alpha=%s  %s' % (a, row))
"
