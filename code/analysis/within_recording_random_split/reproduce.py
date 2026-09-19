"""Reproduce locally from public data; this release contains code and aggregates only."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
RUN = 'tshirt_score_improvement_20260919'
REF = 'tshirt_reference_method_20260919'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=['selected', 'full'])
    ap.add_argument('--repository', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    work = a.output.resolve()
    assert not work.exists(), 'Choose a new output directory.'
    for entry in json.loads((ROOT/'FILES.json').read_text()):
        assert sha(ROOT/entry['path']) == entry['sha256'], entry['path']
    shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns('__pycache__'))
    for entry in json.loads((ROOT/'INPUTS.json').read_text()):
        source = a.repository.resolve()/entry['repository_path']
        assert sha(source) == entry['sha256'], source
        target = work/entry['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    sys.path.insert(0, str(work/RUN))
    import benchmark as b
    import numpy as np
    from sklearn.model_selection import train_test_split
    b.self_test()
    for p in (1,2,3):
        _,y,source,_,_ = b.ref.load_data(p)
        train,test = train_test_split(np.arange(len(y)), test_size=.2, stratify=y,
                                     random_state=b.ref.seed_for(p,.2,(2,3,10)))
        expected = json.loads((ROOT/'aggregate/split_hashes.json').read_text())[f'P{p:02d}']
        assert b.ref.arrhash(source[train]) == expected['train_sha256']
        assert b.ref.arrhash(source[test]) == expected['test_sha256']
        if a.action == 'selected':
            rec = json.loads((ROOT/'aggregate/selected_models.json').read_text())[f'P{p:02d}']
            pred,prob,_ = b.fit_predict(p,rec['candidate'],train,test,rec['seed'])
            actual = b.ref.metrics(y[test],pred)
            for key in ('accuracy','balanced_accuracy','macro_precision','macro_f1'):
                assert np.isclose(actual[key],rec['metrics'][key],rtol=0,atol=1e-12), (p,key)
            assert actual['confusion_counts'] == rec['metrics']['confusion_counts']
            target = work/RUN/'results/outer'
            target.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(target/f'random_rows_P{p:02d}_fold0_all10_tuned.npz',
                test_rows=test,truth=y[test],predictions=pred,probabilities=prob,
                hold=b.load(p)[4].iloc[test].phase.eq('hold').to_numpy())
            print(f'P{p:02d}: selected-model refit matches all aggregate metrics and confusion counts.',flush=True)
        else:
            # Original comparison code expects the three reference tasks. Generate
            # them locally rather than distributing row-level records or indices.
            target = work/REF/'results'
            (target/'predictions').mkdir(parents=True,exist_ok=True)
            (target/'tasks').mkdir(exist_ok=True)
            b.ref.evaluate((p,.2,(2,3,10),str(target)))
    if a.action == 'full':
        subprocess.run([sys.executable,str(work/RUN/'benchmark.py'),'--workers',str(a.workers)],check=True)
        subprocess.run([sys.executable,str(work/RUN/'verify_and_report.py')],check=True)
    else:
        shutil.copyfile(ROOT/'aggregate/metrics.csv',work/RUN/'results/metrics.csv')
    subprocess.run([sys.executable,str(work/'build_figures.py'),'--results',str(work/RUN/'results'),
                    '--output',str(work/'figures')],check=True)
    print('Completed. All generated predictions and indices remain in your local output directory.')

if __name__ == '__main__': main()
