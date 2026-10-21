"""Busca a submissão de MAIOR NOTA estimada de uma agência, só com o motor local (não chama a API).

  python lab/melhor_nota.py Istanbul [--pesos lab/pesos_bangkok.json] [--top 5]

Percorre hardware+entrada em ordem crescente de obra e testa as 12 políticas com a maior demanda útil.
Em A4/SE, refaz com todas as demandas quando baixar a demanda ainda pode entrar no top.
Para quando nem atendendo todos os contratos na categoria certa a obra deixaria entrar no top.
Saída: lab/melhor_nota_<agencia>.json com as 'top' alternativas (melhor política/demanda por hardware+entrada).
"""
import argparse
import itertools
import json
import math
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from comum import cenario
from kickoff import validar
from otimizar import nota
from varrer import CARREG, POLITICAS, _sim

AQUI = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agencia")
    ap.add_argument("--pesos", default=str(AQUI / "pesos_bangkok.json"))
    ap.add_argument("--top", type=int, default=5)
    a = ap.parse_args()
    w = json.load(open(a.pesos, encoding="utf-8"))
    cen = cenario(a.agencia)
    ag, ex, car = cen.agencia, cen.agencia.entrada_existente, cen.carregadores
    teto_nota = len(cen.contratos) * w["certo"]

    combos = []
    for q in itertools.product(*[range(ag.vagas // car[k].saidas + 1) for k in CARREG]):
        c = {k: n for k, n in zip(CARREG, q) if n}
        if c and sum(n * car[k].saidas for k, n in c.items()) <= ag.vagas:
            combos.append(c)
    entradas = [e for e, ent in cen.entradas.items()
                if (e == ex or f"custo_{e}" in w) and ent.kw_util >= cen.entradas[ex].kw_util]

    def obra(c, e):
        return sum(n * w[f"custo_{k}"] for k, n in c.items()) + (0 if e == ex else w[f"custo_{e}"])

    def demandas(c, e):
        ent = cen.entradas[e]
        if ent.kva <= validar.B3_KVA:
            return [None]
        nominal = sum(n * car[k].potencia_kw for k, n in c.items())
        return list(range(30, min(validar.teto_demanda(ent), max(30, math.ceil(nominal / 10) * 10)) + 1, 10))

    def montar(c, e, p, d):
        s = {"agencia": a.agencia, "carregadores": c, "entrada": e, "politica": p}
        if d is not None:
            s["demanda_contratada_kw"] = d
        return s

    melhores = {}  # (hardware, entrada) -> (nota, sub, metricas)

    def registrar(s, m):
        n = nota(m, s, w, ex)
        k = json.dumps([s["carregadores"], s["entrada"]], sort_keys=True)
        if k not in melhores or n > melhores[k][0]:
            melhores[k] = (n, s, m)
        return n

    def corte():
        notas = sorted((x[0] for x in melhores.values()), reverse=True)
        return notas[a.top - 1] if len(notas) >= a.top else -math.inf

    pares = sorted(((obra(c, e), c, e) for c in combos for e in entradas), key=lambda x: x[0])
    print(f"{a.agencia}: {ag.vagas} vagas, {len(cen.contratos)} contratos, {len(pares)} pares hardware+entrada")
    sims = 0
    with ProcessPoolExecutor() as pool:
        for i in range(0, len(pares), 8):
            lote = pares[i:i + 8]
            if teto_nota - lote[0][0] < corte():
                break
            subs = [montar(c, e, p, demandas(c, e)[-1]) for _, c, e in lote for p in POLITICAS]
            refinar = []
            for s, m in pool.map(_sim, subs):
                sims += 1
                if not m:
                    continue
                n = registrar(s, m)
                d = s.get("demanda_contratada_kw")
                if d and n + w["demanda_kw"] * (d - 30) >= corte():
                    refinar += [montar(s["carregadores"], s["entrada"], s["politica"], x)
                                for x in demandas(s["carregadores"], s["entrada"])[:-1]]
            for s, m in pool.map(_sim, refinar):
                sims += 1
                if m:
                    registrar(s, m)
            print(f"  obra <= {lote[-1][0]:>7}: {sims} simulações, corte top{a.top} = {corte():.2f}", flush=True)

    top = sorted(melhores.values(), key=lambda x: -x[0])[:a.top]
    out = [{"nota": n, "obra": obra(s["carregadores"], s["entrada"]), "sub": s, "metricas": m} for n, s, m in top]
    (AQUI / f"melhor_nota_{a.agencia}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print()
    for x in out:
        m = x["metricas"]
        print(f"nota={x['nota']:10.2f} C={m['certos']} U={m['upgrades']} N={m['nao_atendidos']} "
              f"dem={m['demanda_contratada_kw']} ponta={m['energia_ponta_kwh']:.1f} obra={x['obra']} "
              f"pico={m['pico_kw']:.1f}  {json.dumps(x['sub'])}")


if __name__ == "__main__":
    main()
