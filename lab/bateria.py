"""Roda uma lista de submissões no juiz (detalhe=completo) e no motor local, e guarda tudo.

  python lab/bateria.py lab/subs_bangkok.json

Só para Bangkok (grátis). Respostas já salvas em respostas/ não são pedidas de novo.
Saída: respostas/<chave>.json e uma linha por submissão em lab/resultados.jsonl.
"""
import json
import sys
import time

from comum import RESP, chave, cliente, simular_local
from kickoff.api import ErroApi

AQUI = RESP.parent / "lab"


def pedir(c, sub):
    while True:
        try:
            return c.teste(sub["agencia"], sub, "completo")
        except ErroApi as e:
            if e.status == 429:
                espera = 65 if e.codigo == "rate_limit" else 62
                print(f"  {e.codigo}, aguardando {espera}s", flush=True)
                time.sleep(espera)
                continue
            raise


def main():
    subs = json.loads(open(sys.argv[1], encoding="utf-8").read())
    c = cliente()
    RESP.mkdir(exist_ok=True)
    saida = open(AQUI / "resultados.jsonl", "a", encoding="utf-8")
    for sub in subs:
        if sub["agencia"] != "Bangkok":
            raise SystemExit("bateria só roda em Bangkok (grátis)")
        k = chave(sub)
        arq = RESP / f"{k}.json"
        if arq.exists():
            juiz = json.loads(arq.read_text(encoding="utf-8"))
        else:
            juiz = pedir(c, sub)
            arq.write_text(json.dumps(juiz, ensure_ascii=False), encoding="utf-8")
        loc = simular_local(sub)
        lm, jm = loc.get("metricas", {}), juiz.get("metricas", {})
        bate = all(abs(lm.get(x, 0) - jm.get(x, 0)) <= tol for x, tol in
                   (("atendimento_pct", 1e-6), ("pico_kw", 1e-6), ("energia_kwh", 1e-3 * max(1, jm.get("energia_kwh", 0)))))
        linha = {"chave": k, "sub": sub, "nota": juiz.get("nota"), "juiz": jm, "local": lm, "bate": bate,
                 "taxa": juiz.get("taxa"), "saldo": juiz.get("saldo")}
        saida.write(json.dumps(linha, ensure_ascii=False) + "\n")
        saida.flush()
        print(f"{'OK ' if bate else 'DIF'} nota={juiz.get('nota'):>10.3f} at={jm.get('atendimento_pct'):6.2f}% "
              f"C={lm.get('certos')} U={lm.get('upgrades')} N={lm.get('nao_atendidos')} "
              f"P={lm.get('energia_ponta_kwh', 0):.1f} saldo={juiz.get('saldo')}  {k}", flush=True)


if __name__ == "__main__":
    main()
