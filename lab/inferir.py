"""Infere pesos e custos de obra (Neblina) por mínimos quadrados sobre lab/resultados.jsonl.

  python lab/inferir.py [--sem COLUNA ...]

Modelo (regulamento 8.1), com C/U/N/P vindos do motor local e a nota do juiz:
  nota = wc*certos + wu*upgrades - wn*nao_atendidos - wd*demanda_kW - wp*kWh_ponta
         - sum_k n_k * custo_k - custo_entrada
onde custo_k = peso_infra * custo de obra do carregador k (o mesmo para entradas).
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CARREG = ("ac_7", "ac_11", "ac_22x2", "dc_30", "dc_60x2", "dc_120x2")


def linhas():
    """Resultados do juiz com C/U/N/P recalculados pelo motor atual (o gravado pode ser de versão antiga)."""
    from comum import simular_local
    vistos = {}
    for l in (AQUI / "resultados.jsonl").read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            vistos[r["chave"]] = r
    for r in vistos.values():
        loc = simular_local(r["sub"])["metricas"]
        jm = r["juiz"]
        r["local"] = loc
        r["bate"] = (abs(loc["atendimento_pct"] - jm["atendimento_pct"]) < 1e-6
                     and abs(loc["energia_kwh"] - jm["energia_kwh"]) <= 1e-3 * max(1, jm["energia_kwh"]))
    return list(vistos.values())


def features(r, existente="b3_45"):
    m, s = r["local"], r["sub"]
    f = {"certo": m["certos"], "upgrade": m["upgrades"], "-nao_atendido": -m["nao_atendidos"],
         "-demanda_kw": -m["demanda_contratada_kw"], "-ponta_kwh": -m["energia_ponta_kwh"]}
    for k in CARREG:
        f[f"-custo_{k}"] = -s["carregadores"].get(k, 0)
    if s["entrada"] != existente:
        f[f"-custo_{s['entrada']}"] = -1
    return f


def resolver(A, b):
    """Mínimos quadrados via equações normais + eliminação de Gauss (pivô parcial)."""
    n = len(A[0])
    M = [[sum(A[r][i] * A[r][j] for r in range(len(A))) for j in range(n)] +
         [sum(A[r][i] * b[r] for r in range(len(A)))] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-12:
            raise SystemExit(f"sistema singular na coluna {c}: faltam testes que variem essa coluna")
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c:
                fat = M[r][c] / M[c][c]
                M[r] = [a - fat * bb for a, bb in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def main():
    sem = set(sys.argv[sys.argv.index("--sem") + 1:]) if "--sem" in sys.argv else set()
    rs = [r for r in linhas() if r.get("nota") is not None]
    nao_bate = [r["chave"] for r in rs if not r["bate"]]
    if nao_bate:
        print("AVISO: motor local diverge do juiz nestes (C/U/N podem estar errados):", *nao_bate, sep="\n  ")
    fs = [features(r) for r in rs]
    cols = sorted({k for f in fs for k in f if any(g.get(k) for g in fs)} - sem)
    A = [[f.get(c, 0) for c in cols] for f in fs]
    b = [r["nota"] for r in rs]
    print(f"{len(rs)} testes, {len(cols)} incógnitas")
    w = resolver(A, b)
    print("\nestimativa:")
    for c, x in zip(cols, w):
        print(f"  {c.lstrip('-'):22s} {x:12.5f}")
    print("\nresíduos (juiz - modelo):")
    pior = 0
    for r, linha in zip(rs, A):
        e = r["nota"] - sum(a * x for a, x in zip(linha, w))
        pior = max(pior, abs(e))
        print(f"  {e:+10.5f}  nota={r['nota']:10.4f}  {r['chave']}")
    print(f"\nmaior resíduo: {pior:.6f}  ({'modelo linear explica a nota' if pior < 1e-3 else 'há algo fora do modelo'})")
    json.dump(dict(zip(cols, w)), open(AQUI / "pesos_estimados.json", "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
