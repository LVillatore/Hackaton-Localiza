"""Confere o motor local contra TODAS as respostas do juiz salvas (sem chamar a API).

  python lab/conferir.py lab/subs_bangkok.json

Para cada submissão com resposta em respostas/<chave>.json, roda comparar.py e mostra a última linha.
"""
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

from comum import RAIZ, RESP, chave

sys.path.insert(0, str(RAIZ))
import comparar  # noqa: E402


class _Saida(io.StringIO):
    def reconfigure(self, **_):  # comparar.py chama sys.stdout.reconfigure
        pass


def main():
    subs = json.loads(open(sys.argv[1], encoding="utf-8").read())
    ok = total = 0
    with tempfile.TemporaryDirectory() as d:
        for sub in subs:
            arq = RESP / f"{chave(sub)}.json"
            if not arq.exists():
                continue
            total += 1
            s = Path(d) / "sub.json"
            s.write_text(json.dumps(sub), encoding="utf-8")
            buf = _Saida()
            with redirect_stdout(buf):
                comparar.main([str(s), str(arq)])
            ultima = buf.getvalue().strip().splitlines()[-1]
            ok += ultima.startswith("OK")
            print(f"{'OK ' if ultima.startswith('OK') else 'DIF'} {chave(sub)}" + ("" if ultima.startswith("OK") else f"\n    {ultima}"))
    print(f"\n{ok}/{total} batem com o juiz")


if __name__ == "__main__":
    main()
