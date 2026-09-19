"""Recompute metrics and Figures 9-10 from saved, unchanged test predictions."""
from pathlib import Path
import argparse
import csv
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

NAMES = ['Standing straight', 'Left arm raise', 'Right arm raise',
         'Left shoulder touch and twist', 'Right shoulder touch and twist',
         'Both arms raise', 'Forward bend', 'Sitting']
SHORT = ['1  Standing', '2  Left arm raise', '3  Right arm raise',
         '4  Left touch + twist', '5  Right touch + twist',
         '6  Both arms raise', '7  Forward bend', '8  Sitting']
KEYS = ['accuracy', 'macro_precision', 'balanced_accuracy', 'macro_f1']


def calculate(y, pred):
    cm = np.zeros((8, 8), dtype=int)
    np.add.at(cm, (y, pred), 1)
    support = cm.sum(axis=1)
    tp = cm.diagonal()
    precision = np.divide(tp, cm.sum(axis=0), out=np.zeros(8), where=cm.sum(axis=0)>0)
    recall = np.divide(tp, support, out=np.zeros(8), where=support>0)
    f1 = np.divide(2*tp, support+cm.sum(axis=0), out=np.zeros(8), where=support+cm.sum(axis=0)>0)
    return dict(accuracy=float(tp.sum()/cm.sum()), macro_precision=float(precision.mean()),
                balanced_accuracy=float(recall.mean()), macro_f1=float(f1.mean()),
                n_test=int(cm.sum()), n_correct=int(tp.sum()), confusion=cm.tolist(),
                support=support.tolist(), precision=precision.tolist(), recall=recall.tolist(), f1=f1.tolist())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    saved = list(csv.DictReader((args.results/'metrics.csv').open()))
    result = {}; pooled_y = []; pooled_pred = []; held_y = []; held_pred = []
    for p in range(1,4):
        name = f'P{p:02d}'
        with np.load(args.results/'outer'/f'random_rows_{name}_fold0_all10_tuned.npz', allow_pickle=False) as z:
            y, pred, hold = z['truth'], z['predictions'], z['hold']
            assert len(np.unique(z['test_rows'])) == len(y)
            result[name] = calculate(y, pred)
            pooled_y.extend(y); pooled_pred.extend(pred)
            held_y.extend(y[hold]); held_pred.extend(pred[hold])
        old = next(r for r in saved if r['design']=='random_rows' and r['procedure']=='all10_tuned'
                   and r['participant']==name and r['period']=='all_rows')
        for k in KEYS:
            assert np.isclose(result[name][k], float(old[k]), atol=1e-12, rtol=0), (name,k)
        assert result[name]['n_test'] == int(old['n_test'])
    result['Pooled'] = calculate(np.array(pooled_y), np.array(pooled_pred))
    result['Mean'] = {k: float(np.mean([result[p][k] for p in ['P01','P02','P03']])) for k in KEYS}
    result['Held_only'] = calculate(np.array(held_y), np.array(held_pred))
    result['Always_standing'] = calculate(np.array(pooled_y), np.zeros(len(pooled_y), dtype=int))
    assert result['Pooled']['n_test'] == 10141
    assert [round(100*result['Mean'][k],2) for k in KEYS] == [96.16,96.83,95.34,96.06]
    (out/'verified_metrics.json').write_text(json.dumps(result, indent=2)+'\n')
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'axes.labelsize':11,
                         'axes.titlesize':12, 'axes.spines.top':False, 'axes.spines.right':False,
                         'savefig.facecolor':'white'})
    palette = LinearSegmentedColormap.from_list('response', ['#f7fbfc','#b9dfe8','#5ba2b7','#235772','#112f45'])
    cm = np.array(result['Pooled']['confusion']); pct = 100*cm/cm.sum(axis=1,keepdims=True)
    fig, ax = plt.subplots(figsize=(9,7.3), layout='constrained')
    im = ax.imshow(pct,cmap=palette,vmin=0,vmax=100)
    ax.set_xticks(range(8),SHORT,rotation=43,ha='right',rotation_mode='anchor')
    ax.set_yticks(range(8),SHORT)
    ax.set_xlabel('Predicted posture'); ax.set_ylabel('Recorded posture label')
    ax.set_xticks(np.arange(-.5,8,1),minor=True); ax.set_yticks(np.arange(-.5,8,1),minor=True)
    ax.grid(which='minor',color='white',linewidth=1.2); ax.tick_params(which='both',length=0)
    for i in range(8):
        for j in range(8):
            text = '0' if cm[i,j]==0 else f'{pct[i,j]:.1f}%\n({cm[i,j]})'
            ax.text(j,i,text,ha='center',va='center',fontsize=9,color='white' if pct[i,j]>55 else '#153244')
    fig.colorbar(im,ax=ax,shrink=.8,pad=.035,label='Row-normalized test samples (%)')
    fig.savefig(out/'Fig9.png',dpi=350); plt.close(fig)
    plt.rcParams.update({'font.size':12, 'axes.labelsize':12, 'axes.titlesize':13})
    fig,(a,b) = plt.subplots(1,2,figsize=(12,5.3),gridspec_kw={'width_ratios':[1.05,1]},layout='constrained')
    people = ['P01','P02','P03']; groups = people+['Mean']; x=np.arange(4); width=.19
    for j,(k,label,color) in enumerate(zip(KEYS,['Accuracy','Macro-precision','Balanced accuracy','Macro-F1'],
                                          ['#263f58','#4f83a1','#55a99d','#a0c6d4'])):
        a.bar(x+(j-1.5)*width,[100*result[g][k] for g in groups],width=width,label=label,color=color)
    a.set(ylim=(0,100),ylabel='Performance (%)',xticks=x,xticklabels=groups)
    a.set_title('(a)  Random-sample test performance',loc='left',weight='bold',pad=12)
    a.grid(axis='y',color='#dde4e8',linewidth=.6); a.set_axisbelow(True)
    a.legend(loc='upper center',bbox_to_anchor=(.5,-.10),ncols=2,frameon=False,fontsize=10.5)
    recall=np.array([result[g]['recall'] for g in people]+[np.mean([result[g]['recall'] for g in people],axis=0)]).T*100
    im=b.imshow(recall,cmap=palette,vmin=0,vmax=100,aspect='auto')
    b.set_title('(b)  Recall by posture',loc='left',weight='bold',pad=12)
    b.set_xticks(range(4),groups); b.set_yticks(range(8),SHORT)
    b.set_xticks(np.arange(-.5,4,1),minor=True); b.set_yticks(np.arange(-.5,8,1),minor=True)
    b.grid(which='minor',color='white',linewidth=1.2); b.tick_params(which='both',length=0)
    for i in range(8):
        for j in range(4):
            b.text(j,i,f'{recall[i,j]:.1f}',ha='center',va='center',fontsize=12,
                   color='white' if recall[i,j]>55 else '#153244')
    fig.colorbar(im,ax=b,shrink=.85,pad=.03,label='Recall (%)')
    fig.savefig(out/'Fig10.png',dpi=350); plt.close(fig)
    print(json.dumps({g:{k:v for k,v in r.items() if k in KEYS+['n_test','n_correct']} for g,r in result.items()},indent=2))


if __name__=='__main__': main()
