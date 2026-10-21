"""Exemplos numéricos do regulamento aplicados ao motor (etapas 2 a 6). python -m unittest discover -s testes"""
import heapq
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from kickoff import dados, motor, validar  # noqa: E402
from kickoff.modelo import Contrato  # noqa: E402

TEM_DADOS = (RAIZ / "dados" / "Bangkok").is_dir()


def _motor(carregadores, divisao="igual", prioridade="menor_soc", limite=None):
    cen = dados.carregar(RAIZ / "dados", "Bangkok")
    sub = validar.normalizar({"agencia": "Bangkok", "carregadores": carregadores, "entrada": "b3_45",
                              "politica": {"divisao": divisao, "prioridade": prioridade}}, cen)
    m = motor.Motor(cen, sub)
    m.aberta = True
    if limite is not None:
        m.limite_kw = limite
    return m


def _carro(m, vid, modelo, soc):
    mod = m.cen.modelos[modelo]
    v = motor.Veiculo(vid, mod, mod.rank, soc)
    m.veiculos[vid] = v
    return v


def _plugar(m, v, ponto_id):
    p = next(p for p in m.pontos if p.id == ponto_id)
    m.patio[v.id] = v
    m.plugar(v, p)


@unittest.skipUnless(TEM_DADOS, "dados/Bangkok ausentes")
class EscolhaDoCarro(unittest.TestCase):
    """6.3.1: contrato Prata."""

    def setUp(self):
        self.m = _motor({"dc_30": 1})
        m = self.m
        self.geely = _carro(m, "a_geely", "Geely EX2 Pro", 82)
        self.mini = _carro(m, "b_mini", "BYD Dolphin Mini GS", 95)
        self.mg4 = _carro(m, "c_mg4", "MG4 Urban Comfort", 100)
        self.jac = _carro(m, "d_jac", "JAC E-JS1", 100)
        for v in (self.geely, self.mg4, self.jac):
            m.patio[v.id] = v
        _plugar(m, self.mini, "dc_30-0")
        rank = m.cen.modelos["Geely EX2 Pro"].rank
        self.c = Contrato("k1", "Prata", rank, 600, None, 0, None)

    def test_sai_o_geely(self):
        self.assertIs(self.m.escolher_carro(self.c, 600), self.geely)

    def test_geely_78_sai_o_mini(self):
        self.geely.soc = 78
        self.assertIs(self.m.escolher_carro(self.c, 600), self.mini)

    def test_sem_prata_sai_mg4(self):
        self.geely.soc = 78
        self.mini.soc = 70
        self.assertIs(self.m.escolher_carro(self.c, 600), self.mg4)

    def test_fechada_ninguem_sai(self):
        self.m.aberta = False
        self.assertIsNone(self.m.escolher_carro(self.c, 600))


@unittest.skipUnless(TEM_DADOS, "dados/Bangkok ausentes")
class RecargaAte80(unittest.TestCase):
    def test_dolphin_gs_dc60_36_7_min(self):
        """6.3.2: Dolphin GS 20% -> 80% sozinho num DC-60, sem limite: 36,7 min."""
        m = _motor({"dc_60x2": 1}, limite=1e9)
        v = _carro(m, "v", "BYD Dolphin GS", 20)
        t0 = m.t
        m.entrar_patio(v, t0)
        self.assertTrue(v.plugado)
        while m.heap:
            t, _, _, tipo, p = heapq.heappop(m.heap)
            m.avancar(t)
            if tipo == "fim_recarga":
                m.on_fim_recarga(p[0], p[1], t)
        self.assertAlmostEqual(v.soc, 80, places=6)
        self.assertFalse(v.plugado)
        self.assertAlmostEqual(m.t - t0, 36.7, delta=0.05)


@unittest.skipUnless(TEM_DADOS, "dados/Bangkok ausentes")
class OrdemDaFila(unittest.TestCase):
    """6.3.3: A Kwid 30%, B Dolphin Mini 20%, C MG4 55%, D Leapmotor 40%."""

    def _fila(self, prioridade):
        m = _motor({"dc_30": 1}, prioridade=prioridade)
        carros = [("A", "Renault Kwid E-Tech", 30, 600), ("B", "BYD Dolphin Mini GS", 20, 620),
                  ("C", "MG4 Urban Comfort", 55, 640), ("D", "Leapmotor B10 BEV", 40, 655)]
        for vid, mod, soc, t in carros:
            v = _carro(m, vid, mod, soc)
            v.na_fila, v.entrou_fila_t = True, t
            m.fila.append(v)
        rk = {c: m.cen.modelos[n].rank for c, n in (("Bronze", "Renault Kwid E-Tech"),
                                                    ("Prata", "Geely EX2 Pro"), ("Ouro", "MG4 Urban Comfort"))}
        m.contratos_ord = [Contrato("o", "Ouro", rk["Ouro"], 750, None, 0, None),
                           Contrato("p", "Prata", rk["Prata"], 795, None, 0, None),
                           Contrato("b", "Bronze", rk["Bronze"], 840, None, 0, None)]
        m.ordenar_fila(660)
        return [v.id for v in m.fila]

    def test_menor_soc(self):
        self.assertEqual(self._fila("menor_soc"), list("ABDC"))

    def test_chegada(self):
        self.assertEqual(self._fila("chegada"), list("ABCD"))

    def test_proxima_retirada(self):
        self.assertEqual(self._fila("proxima_retirada"), list("CDBA"))


@unittest.skipUnless(TEM_DADOS, "dados/Bangkok ausentes")
class EscolhaDoCarregador(unittest.TestCase):
    def test_dolphin_vai_para_dc60(self):
        """6.3.4: DC-60 com Geely 30% e AC-22 vazio; Dolphin GS 20% vai para o DC-60."""
        m = _motor({"dc_60x2": 1, "ac_22x2": 1})
        _plugar(m, _carro(m, "g", "Geely EX2 Pro", 30), "dc_60x2-0")
        v = _carro(m, "d", "BYD Dolphin GS", 20)
        self.assertEqual(m.escolher_ponto(v).id, "dc_60x2-0")


@unittest.skipUnless(TEM_DADOS, "dados/Bangkok ausentes")
class Divisao(unittest.TestCase):
    """6.3.5: 2x DC-60, Geely 30% + Dolphin GS 50% no 1; Kwid 40% + JAC 75% no 2."""

    def _pot(self, divisao, limite):
        m = _motor({"dc_60x2": 2}, divisao=divisao, limite=limite)
        carros = {"geely": ("Geely EX2 Pro", 30, "dc_60x2-0"), "dolphin": ("BYD Dolphin GS", 50, "dc_60x2-0"),
                  "kwid": ("Renault Kwid E-Tech", 40, "dc_60x2-1"), "jac": ("JAC E-JS1", 75, "dc_60x2-1")}
        vs = {}
        for vid, (mod, soc, p) in carros.items():
            vs[vid] = _carro(m, vid, mod, soc)
            _plugar(m, vs[vid], p)
        m.recalcular_potencias(0)
        return {k: v.potencia_kw for k, v in vs.items()}

    def test_igual_40_5(self):
        for kw in self._pot("igual", 40.5).values():
            self.assertAlmostEqual(kw, 10.125, places=6)

    def test_prioridade_40_5(self):
        p = self._pot("prioridade", 40.5)
        self.assertAlmostEqual(p["kwid"], 26.6, places=6)
        self.assertAlmostEqual(p["geely"], 13.9, places=6)
        self.assertAlmostEqual(p["jac"], 0, places=6)
        self.assertAlmostEqual(p["dolphin"], 0, places=6)

    def test_igual_80(self):
        p = self._pot("igual", 80)
        self.assertAlmostEqual(p["jac"], 16.45, places=6)
        for k in ("geely", "dolphin", "kwid"):
            self.assertAlmostEqual(p[k], 21.183333, places=5)

    def test_prioridade_80(self):
        p = self._pot("prioridade", 80)
        self.assertAlmostEqual(p["kwid"], 26.6, places=6)
        self.assertAlmostEqual(p["geely"], 53.4, places=6)
        self.assertAlmostEqual(p["jac"], 0, places=6)
        self.assertAlmostEqual(p["dolphin"], 0, places=6)


def _rodar_eventos(m):
    """Despacha só os eventos que estes testes agendam (fim de recarga e ponta)."""
    while m.heap:
        t, _, _, tipo, p = heapq.heappop(m.heap)
        m.avancar(t)
        if tipo == "fim_recarga":
            m.on_fim_recarga(p[0], p[1], t)
        elif tipo == "ponta":
            m.on_ponta(p[0], t)


@unittest.skipUnless(TEM_DADOS, "dados/Bangkok ausentes")
class EvitarPonta(unittest.TestCase):
    """6.3.6: MG4 pluga seg 17:00 num AC-22 a 11 kW, de 29% a 80% (~22 kWh, 2 h)."""
    SEG_17 = 1 * 1440 + 17 * 60  # seg 18/10 17:00

    def _carga(self, evitar):
        cen = dados.carregar(RAIZ / "dados", "Bangkok")
        sub = validar.normalizar({"agencia": "Bangkok", "carregadores": {"ac_22x2": 1}, "entrada": "b3_45",
                                  "politica": {"evitar_ponta": evitar}}, cen)
        m = motor.Motor(cen, sub)
        m.aberta, m.limite_kw, m.t = True, 1e9, self.SEG_17
        if evitar:
            m.agendar(1440 + 18 * 60, motor.PRIO_ABERTURA, "ponta", True)
            m.agendar(1440 + 21 * 60, motor.PRIO_ABERTURA, "ponta", False)
        v = _carro(m, "mg4", "MG4 Urban Comfort", 29)
        m.entrar_patio(v, m.t)
        _rodar_eventos(m)
        ponta = sum(e for i, e in m.medidor.bins.items() if 1440 + 18 * 60 <= i * 15 < 1440 + 21 * 60)
        return m.t, ponta, v

    def test_sem_evitar_termina_19h_com_11_kwh_na_ponta(self):
        fim, ponta, v = self._carga(False)
        self.assertAlmostEqual(v.soc, 80, places=6)
        self.assertAlmostEqual(fim, 1440 + 19 * 60, delta=2)
        self.assertAlmostEqual(ponta, 11, delta=0.2)

    def test_com_evitar_termina_22h_sem_ponta(self):
        fim, ponta, v = self._carga(True)
        self.assertAlmostEqual(v.soc, 80, places=6)
        self.assertAlmostEqual(fim, 1440 + 22 * 60, delta=2)
        self.assertEqual(ponta, 0)
        self.assertTrue(v.plugado or v.soc >= 80)  # seguiu plugado durante a ponta


@unittest.skipUnless(TEM_DADOS, "dados/Bangkok ausentes")
class DemandaNoMotor(unittest.TestCase):
    """6.3.7: a4_150 com demanda 80 -> limite rígido de 80 kW; omitida -> 130 kW."""

    def _motor(self, **dem):
        cen = dados.carregar(RAIZ / "dados", "Bangkok")
        sub = validar.normalizar({"agencia": "Bangkok", "carregadores": {"dc_120x2": 2}, "entrada": "a4_150", **dem}, cen)
        return motor.Motor(cen, sub)

    def test_limites(self):
        self.assertEqual(self._motor(demanda_contratada_kw=80).limite_kw, 80)
        self.assertEqual(self._motor(demanda_contratada_kw=84).limite_kw, 80)
        self.assertEqual(self._motor(demanda_contratada_kw=85).limite_kw, 90)
        self.assertEqual(self._motor().limite_kw, 130)

    def test_teto_rigido(self):
        m = self._motor(demanda_contratada_kw=80)
        m.aberta = True
        for i, mod in enumerate(("Leapmotor B10 BEV", "MG4 Urban Comfort", "Geely EX2 Pro", "BYD Dolphin Plus")):
            m.entrar_patio(_carro(m, f"v{i}", mod, 10), m.t)
        self.assertAlmostEqual(sum(v.potencia_kw for p in m.pontos for v in p.conectados), 80, places=6)


if __name__ == "__main__":
    unittest.main()
