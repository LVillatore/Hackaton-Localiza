"""Varredura lexicográfica de uma agência só com o motor local (não chama a API).

  python lab/varrer.py Istanbul [--pesos lab/pesos_bangkok.json] [--top 5]

Ordem de preferência: menos não atendidos -> menor custo de obra -> menor demanda contratada
-> menos kWh na ponta. Custo de obra em pontos de nota (custos inferidos em Bangkok).

Estratégia: percorre hardware+entrada em ordem crescente de obra; em cada um testa as 12 políticas
com o maior limite útil da entrada; onde atinge o melhor N, procura a menor demanda que o mantém.
Para quando a obra passa da 'top'-ésima melhor alternativa já achada.
"""
import argparse
import itertools
import json
import math
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from comum import cenario, simular_local
from kickoff import validar

AQUI = Path(__file__).resolve().parent
CARREG = ("ac_7", "ac_11", "ac_22x2", "dc_30", "dc_60x2", "dc_120x2")
POLITICAS = [{"prioridade": p, "evitar_ponta": e, "divisao": d}
             for p in validar.MENU["prioridade"] for e in (False, True) for d in validar.MENU["divisao"]]


def distintas(achados):
    """Ordena e deixa só a melhor política/demanda de cada (hardware, entrada)."""
    alt, usados = [], set()
    for x in sorted(achados, key=lambda x: x[:4]):
        k = json.dumps([x[4]["carregadores"], x[4]["entrada"]], sort_keys=True)
        if k not in usados:
            usados.add(k)
            alt.append(x)
    return alt


def _sim(sub):
    r = simular_local(sub)
    return sub, (r["metricas"] if r["valido"] else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agencia")
    ap.add_argument("--pesos", default=str(AQUI / "pesos_bangkok.json"))
    ap.add_argument("--top", type=int, default=5)
    a = ap.parse_args()
    w = json.load(open(a.pesos, encoding="utf-8"))
    cen = cenario(a.agencia)
    ag, ex = cen.agencia, cen.agencia.entrada_existente
    car = cen.carregadores

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
        """Demandas úteis: de 30 até o 1º múltiplo de 10 >= potência nominal instalada."""
        ent = cen.entradas[e]
        if ent.kva <= validar.B3_KVA:
            return [None]
        nominal = sum(n * car[k].potencia_kw for k, n in c.items())
        teto = min(validar.teto_demanda(ent), max(30, math.ceil(nominal / 10) * 10))
        return list(range(30, teto + 1, 10))

    pares = sorted(((obra(c, e), c, e) for c in combos for e in entradas), key=lambda x: x[0])
    # A4/SE: a de menor obra que comporta a demanda máxima útil domina as maiores para o mesmo hardware
    print(f"{a.agencia}: {ag.vagas} vagas, {len(combos)} combinações de carregadores, entradas {entradas}")

    achados = []  # (N, obra, demanda, ponta, sub, metricas)
    melhor_n = math.inf
    vistos = set()
    with ProcessPoolExecutor() as pool:
        for i in range(0, len(pares), 8):
            lote = pares[i:i + 8]
            distintos = distintas(achados)
            if len(distintos) >= a.top:
                corte = distintos[a.top - 1]
                if lote[0][0] > corte[1] and corte[0] <= melhor_n:
                    break
            subs = []
            for custo, c, e in lote:
                dem = demandas(c, e)[-1]
                for p in POLITICAS:
                    s = {"agencia": a.agencia, "carregadores": c, "entrada": e, "politica": p}
                    if dem is not None:
                        s["demanda_contratada_kw"] = dem
                    subs.append(s)
            res = list(pool.map(_sim, subs))
            for s, m in res:
                if m:
                    melhor_n = min(melhor_n, m["nao_atendidos"])
            # para cada (hardware, entrada, política) que atinge o melhor N, desce a demanda
            refinar = []
            for s, m in res:
                if not m or m["nao_atendidos"] > melhor_n:
                    continue
                k = json.dumps([s["carregadores"], s["entrada"], s["politica"]], sort_keys=True)
                if k in vistos:
                    continue
                vistos.add(k)
                refinar.append(s)
            jobs = [{**s, "demanda_contratada_kw": d} for s in refinar
                    for d in demandas(s["carregadores"], s["entrada"]) if d is not None] + \
                   [s for s in refinar if "demanda_contratada_kw" not in s]
            for s, m in pool.map(_sim, jobs):
                if m:
                    achados.append((m["nao_atendidos"], obra(s["carregadores"], s["entrada"]),
                                    m["demanda_contratada_kw"], round(m["energia_ponta_kwh"], 3), s, m))
            print(f"  obra <= {lote[-1][0]:>7}: melhor N={melhor_n}, candidatos={len(achados)}", flush=True)

    alt = distintas(achados)
    out =[{"nao_atendidos": n, "obra": o, "demanda_kw": d, "ponta_kwh": p, "sub": s, "metricas": m}
           for n, o, d, p, s, m in alt[:a.top]]
    (AQUI / f"varredura_{a.agencia}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print()
    for x in out:
        print(f"N={x['nao_atendidos']} obra={x['obra']} dem={x['demanda_kw']} ponta={x['ponta_kwh']}  {json.dumps(x['sub'])}")


if __name__ == "__main__":
    main()
