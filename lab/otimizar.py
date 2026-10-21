"""Busca local da melhor submissão para uma agência, usando o motor e pesos estimados.

  python lab/otimizar.py Bangkok [--pesos lab/pesos_estimados.json] [--top 10]

Fases: (1) todas as combinações de carregadores que cabem nas vagas, com a entrada existente e a
política padrão; (2) as 12 políticas sobre as melhores; (3) entradas maiores e demandas sobre as melhores.
Entradas sem custo estimado são puladas. Nada aqui chama o juiz.
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

from comum import cenario, simular_local
from kickoff import validar

AQUI = Path(__file__).resolve().parent
CARREG = ("ac_7", "ac_11", "ac_22x2", "dc_30", "dc_60x2", "dc_120x2")
POLITICAS = [{"prioridade": p, "evitar_ponta": e, "divisao": d}
             for p in validar.MENU["prioridade"] for e in (False, True) for d in validar.MENU["divisao"]]


def nota(m, sub, w, existente):
    n = (w.get("certo", 0) * m["certos"] + w.get("upgrade", 0) * m["upgrades"]
         - w.get("nao_atendido", 0) * m["nao_atendidos"] - w.get("demanda_kw", 0) * m["demanda_contratada_kw"]
         - w.get("ponta_kwh", 0) * m["energia_ponta_kwh"])
    n -= sum(q * w.get(f"custo_{k}", 0) for k, q in sub["carregadores"].items())
    if sub["entrada"] != existente:
        n -= w[f"custo_{sub['entrada']}"]
    return n


def combos(vagas):
    saidas = {k: cenario("Bangkok").carregadores[k].saidas for k in CARREG}
    faixas = [range(0, vagas // saidas[k] + 1) for k in CARREG]
    for q in itertools.product(*faixas):
        if 0 < sum(n * saidas[k] for n, k in zip(q, CARREG)) <= vagas:
            yield {k: n for k, n in zip(CARREG, q) if n}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agencia")
    ap.add_argument("--pesos", default=str(AQUI / "pesos_estimados.json"))
    ap.add_argument("--top", type=int, default=8)
    a = ap.parse_args()
    w = {k.lstrip("-"): v for k, v in json.load(open(a.pesos, encoding="utf-8")).items()}
    cen = cenario(a.agencia)
    ex = cen.agencia.entrada_existente
    avaliados = {}

    def avaliar(sub):
        k = json.dumps(sub, sort_keys=True)
        if k not in avaliados:
            r = simular_local(sub)
            avaliados[k] = (nota(r["metricas"], sub, w, ex), sub, r["metricas"]) if r["valido"] else None
        return avaliados[k]

    base = {"agencia": a.agencia, "entrada": ex}
    conhecidos = [c for c in combos(cen.agencia.vagas) if all(f"custo_{k}" in w for k in c)]
    fase1 = [x for x in (avaliar({**base, "carregadores": c}) for c in conhecidos) if x]
    fase1.sort(key=lambda x: -x[0])
    print(f"fase 1: {len(fase1)} combinações de carregadores", file=sys.stderr)
    fase2 = [x for _, s, _ in fase1[:a.top] for x in (avaliar({**s, "politica": p}) for p in POLITICAS) if x]
    fase2.sort(key=lambda x: -x[0])
    entradas = [e for e, ent in cen.entradas.items() if e != ex and f"custo_{e}" in w
                and ent.kw_util >= cen.entradas[ex].kw_util]
    fase3 = []
    for _, s, _ in fase2[:a.top]:
        for e in entradas:
            ent = cen.entradas[e]
            dems = [None] if ent.kva <= validar.B3_KVA else range(30, validar.teto_demanda(ent) + 1, 10)
            for d in dems:
                sub = {**s, "entrada": e, **({"demanda_contratada_kw": d} if d else {})}
                x = avaliar(sub)
                if x:
                    fase3.append(x)
    todos = sorted([x for x in avaliados.values() if x], key=lambda x: -x[0])
    print(f"{len(todos)} submissões simuladas\n")
    for n, s, m in todos[:a.top]:
        print(f"{n:10.3f}  C={m['certos']} U={m['upgrades']} N={m['nao_atendidos']} "
              f"P={m['energia_ponta_kwh']:.1f}  {json.dumps({k: v for k, v in s.items() if k != 'agencia'})}")


if __name__ == "__main__":
    main()
