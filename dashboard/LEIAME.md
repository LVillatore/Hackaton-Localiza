# Dados do dashboard (regulamento 13.1)

Gerado por `python lab/exportar_dashboard.py` (motor local + respostas salvas do juiz + placar de 21/10 16:39).
CSV com separador `;` e UTF-8 com BOM (abre direto no Excel). Horários locais (UTC−3).

| Arquivo | Conteúdo |
|---|---|
| `secao1_motor_regras.json` | regras do juiz implementadas no motor, na ordem |
| `secao1_motor_correcoes.csv` | correções do dia: motivo, erro antes × depois |
| `secao1_precisao_testes.csv` | motor × juiz em cada resposta salva (nota, contratos, atendimento, pico, energia, erro %) |
| `secao1_precisao_por_agencia.csv` | resumo: testes, notas exatas, maior erro % por métrica |
| `secao2_pesos_estimados_x_oficiais.csv` | pesos inferidos na Neblina × pesos do H4 |
| `secao2_testes_inferencia.csv` | os 27 testes de Bangkok usados na inferência (o que variou, nota do juiz, C/U/N/P) |
| `secao3_agencias.json` | por agência: dados de entrada, busca, submissão escolhida, justificativa, alternativas |
| `secao3_metricas_finais.csv` | métricas da submissão final (motor) + nota oculta do juiz |
| `secao3_cascata_pontos.csv` | cascata item × quantidade × peso × pontos (motor e juiz) |
| `secao3_testes_api.csv` | todos os testes e envios finais, m7Coins e saldo |
| `secao4_m7coins.csv`, `secao4_m7coins_por_agencia.csv` | extrato de m7Coins (status: confirmado/inferido) |
| `secao4_custo_obra.csv` | obra por agência (carregadores, entrada, demanda) |
| `secao4_evolucao_nota.csv` | notas ao longo do dia (testes e placar) |
| `secao4_eventos.json` | eventos ao vivo e reação |
| `secao4_placar_1939utc.json` | placar completo (GET /placar) |
| `series/<Agencia>_15min.csv` | potência, plugados, fila (formato do juiz e real), não atendidos, por janela de 15 min |
| `series/<Agencia>_retiradas_soc.csv` | cada retirada com SOC, categoria pedida e entregue |
| `series/<Agencia>_nao_atendidos.csv` | horário de cada cliente não atendido |

Séries: semanas públicas, motor local, submissão final de cada agência (Marrakech com o evento de corte).
`fila_max_formato_juiz` reproduz a série do juiz (vai a 0 quando um carro sai da fila para plugar);
`fila_max_real` é o tamanho real da fila.
