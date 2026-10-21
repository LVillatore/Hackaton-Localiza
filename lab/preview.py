import json, sys
sys.path.insert(0, 'lab')
from comum import simular_local, chave
B = "Bangkok"
def S(car, ent="b3_45", dem=None, **pol):
    s = {"agencia": B, "carregadores": car, "entrada": ent}
    if dem is not None: s["demanda_contratada_kw"] = dem
    if pol: s["politica"] = pol
    return s
subs = [
 S({"ac_7":2,"dc_30":1}, prioridade="menor_soc", evitar_ponta=False, divisao="igual"),
 S({"ac_7":1}), S({"ac_7":2}), S({"ac_7":3}), S({"ac_7":6}),
 S({"ac_11":1}), S({"ac_11":3}),
 S({"ac_22x2":1}), S({"ac_22x2":3}),
 S({"dc_30":1}), S({"dc_30":2}),
 S({"dc_60x2":1}), S({"dc_120x2":1}),
 S({"dc_60x2":1,"ac_7":2}, "b3_75"),
 S({"dc_60x2":1,"ac_7":2}, "a4_150", 40),
 S({"dc_60x2":1,"ac_7":2}, "a4_150", 120),
 S({"dc_60x2":2}, "a4_225", 60),
 S({"dc_120x2":2}, "a4_300", 200),
 S({"ac_7":2,"dc_30":1}, prioridade="proxima_retirada", divisao="prioridade"),
 S({"ac_7":2,"dc_30":1}, prioridade="chegada"),
 S({"ac_7":2,"dc_30":1}, evitar_ponta=True),
 S({"ac_7":1}, evitar_ponta=True, prioridade="proxima_retirada"),
 S({"ac_7":2}, divisao="prioridade", prioridade="chegada"),
]
for s in subs:
    r = simular_local(s)
    if not r["valido"]: print("INVALIDO", r["erros"], chave(s)); continue
    m = r["metricas"]
    print(f"C={m['certos']:3} U={m['upgrades']:3} N={m['nao_atendidos']:3} P={m['energia_ponta_kwh']:7.1f} D={m['demanda_contratada_kw']:4} E={m['energia_kwh']:7.1f} viol={len(r['violacoes'])}  {chave(s)}")
json.dump(subs, open('lab/subs_bangkok.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
