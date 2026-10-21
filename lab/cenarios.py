"""Converte cenários no formato da equipe (lista de carregadores, chaves de política soltas) para a
submissão oficial, valida e simula no motor local com a nota estimada.

  python lab/cenarios.py ARQUIVO [--agencia Bangkok] [--pesos lab/pesos_bangkok.json] [--salvar subs.json]
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from comum import cenario, simular_local
from kickoff import validar
from otimizar import nota

AQUI = Path(__file__).resolve().parent


def converter(c: dict, agencia: str) -> dict:
    sub = {"agencia": agencia, "carregadores": dict(Counter(c["carregadores"])), "entrada": c["entrada"]}
    if c.get("demanda_contratada_kw") is not None:
        sub["demanda_contratada_kw"] = c["demanda_contratada_kw"]
    sub["politica"] = {"prioridade": c.get("fila_prioridade", "menor_soc"),
                       "evitar_ponta": bool(c.get("evitar_ponta", False)),
                       "divisao": c.get("divisao_potencia", "igual")}
    return sub


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arquivo")
    ap.add_argument("--agencia", default="Bangkok")
    ap.add_argument("--pesos", default=str(AQUI / "pesos_bangkok.json"))
    ap.add_argument("--salvar")
    a = ap.parse_args()
    w = json.load(open(a.pesos, encoding="utf-8"))
    cen = cenario(a.agencia)
    subs = []
    for i, c in enumerate(json.loads(Path(a.arquivo).read_text(encoding="utf-8-sig")), 1):
        sub = converter(c, a.agencia)
        subs.append(sub)
        r = simular_local(sub)
        print(f"Cenário {i}: {c.get('_comentario', '')[:70]}")
        if not r["valido"]:
            print(f"  INVÁLIDO: {'; '.join(r['erros'])}\n")
            continue
        m = r["metricas"]
        n = nota(m, sub, w, cen.agencia.entrada_existente)
        infra = sum(q * w[f"custo_{k}"] for k, q in sub["carregadores"].items()) + \
            (0 if sub["entrada"] == cen.agencia.entrada_existente else w[f"custo_{sub['entrada']}"])
        print(f"  nota={n:10.2f}  certos={m['certos']} upg={m['upgrades']} perdidos={m['nao_atendidos']} "
              f"atend={m['atendimento_pct']:.2f}%  pico={m['pico_kw']:.1f}kW  ponta={m['energia_ponta_kwh']:.1f}kWh  "
              f"demanda={m['demanda_contratada_kw']}kW  obra={infra}\n")
    if a.salvar:
        Path(a.salvar).write_text(json.dumps(subs, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
