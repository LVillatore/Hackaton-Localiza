"""Utilitários do laboratório: carregar credenciais, simular localmente e chamar o juiz."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from kickoff import api, medicao, motor, tempo, validar  # noqa: E402
from kickoff.dados import carregar  # noqa: E402

RESP = RAIZ / "respostas"
_cen: dict = {}


def cliente() -> api.Cliente:
    """Lê GAMEDAY_URL/GAMEDAY_TOKEN de gameday.env (sem imprimir o token)."""
    env = {}
    for linha in (RAIZ / "gameday.env").read_text(encoding="utf-8-sig").splitlines():
        if "=" in linha and not linha.lstrip().startswith("#"):
            k, v = linha.split("=", 1)
            env[k.strip()] = v.strip()
    return api.Cliente(env["GAMEDAY_URL"], env["GAMEDAY_TOKEN"])


def cenario(ag: str):
    if ag not in _cen:
        _cen[ag] = carregar(RAIZ / "dados", ag, None)
    return _cen[ag]


def simular_local(sub: dict, eventos=()) -> dict:
    """Métricas completas do motor local (certos, upgrades, ponta...) + séries."""
    cen = cenario(sub["agencia"])
    erros = validar.validar(sub, cen)
    if erros:
        return {"valido": False, "erros": erros}
    s = validar.normalizar(sub, cen)
    res = motor.simular(cen, s, eventos)
    ini, fim = tempo.JANELA_PUBLICA
    m = medicao.metricas(res.retiradas, res.nao_atendidos, res.bins, ini, fim)
    m["demanda_contratada_kw"] = s["demanda_contratada_kw"] or 0
    return {"valido": True, "norm": s, "metricas": m, "violacoes": res.violacoes,
            "series": medicao.series(res.bins, res.trace, res.retiradas, res.nao_atendidos, ini, fim)}


def chave(sub: dict) -> str:
    """Nome de arquivo estável para a submissão."""
    car = "+".join(f"{k}x{v}" for k, v in sorted(sub["carregadores"].items()) if v)
    pol = sub.get("politica") or {}
    p = "-".join(str(pol[k])[:4] for k in sorted(pol))
    d = sub.get("demanda_contratada_kw")
    return f"{sub['agencia']}_{car}_{sub['entrada']}" + (f"_d{d}" if d else "") + (f"_{p}" if p else "")
