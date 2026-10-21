# Especificação dos gráficos e do dashboard de análises

Data da análise: 21/10/2026. Escopo: seção 13.1 apresentada na imagem, código e artefatos presentes neste repositório. Este documento especifica uma implementação futura; não instala bibliotecas, não implementa etapas do motor e não autoriza chamadas ao juiz.

## 1. Recomendação principal

Implementar um exportador independente em Python, usando apenas a biblioteca padrão, que produza dados normalizados em JSON/CSV e um relatório HTML com gráficos SVG. Usar CSS e, quando necessário, JavaScript nativo para seleção de agência, cenário e intervalo. O primeiro relatório pode ser estático e abrir diretamente no navegador, sem servidor, CDN, instalação de pacotes ou conexão com o juiz.

Essa estratégia atende à restrição de dependências, aproveita os resultados existentes e permite compartilhar gráficos vetoriais e tabelas auditáveis. A interatividade deve começar pequena: filtros, seleção de período, detalhes do ponto e exportação de dados. Não é necessário construir um framework de gráficos.

Para evolução de nota, manter um histórico acrescentado a cada avaliação, com horário real, submissão normalizada, origem da nota e versões dos dados, pesos, eventos e motor. Mostrar os resultados individuais e a melhor nota comparável até aquele momento. O histórico atual permite uma visão por ordem de registro, mas não uma cronologia confiável por hora.

Power BI Desktop é uma alternativa independente para consumir as mesmas exportações. Sua adoção não deve tornar o simulador dependente do Power BI nem levar a chamadas automáticas à API. Matplotlib, Plotly e ferramentas semelhantes ficam como alternativas condicionais a uma alteração explícita da restrição de dependências.

## 2. Base da análise e restrições

### 2.1 Inspeção realizada

Foram inventariados os diretórios `kickoff/`, `lab/`, `testes/`, `dados/`, `respostas/` e os arquivos da raiz. Foi localizado apenas o `AGENTS.md` da raiz como arquivo de instruções desse tipo. Foram examinados o código Python, as instruções e documentos dos kits, as estruturas dos JSON/JSONL, as configurações de submissão e os resultados salvos.

Os CSVs foram inspecionados por cabeçalho e pelo carregador/resumo do projeto, sem despejar seu conteúdo integral no contexto, conforme o `AGENTS.md`. As 40 curvas Markdown correspondem a oito conteúdos distintos, repetidos entre as cinco agências. As credenciais de `gameday.env` não foram lidas; arquivos compilados de `__pycache__/` e objetos internos de `.git/` não constituem fontes funcionais para os gráficos.

Referências locais principais: [AGENTS.md](AGENTS.md), [LEIAME.md](LEIAME.md), [simular.py](simular.py), [comparar.py](comparar.py), [motor.py](kickoff/motor.py), [medicao.py](kickoff/medicao.py), [nota.py](kickoff/nota.py), [modelo.py](kickoff/modelo.py), [validar.py](kickoff/validar.py), [tempo.py](kickoff/tempo.py), [dados.py](kickoff/dados.py), [API](kickoff/api.py) e os arquivos de `lab/` citados adiante.

### 2.2 Regras que a implementação deve preservar

- Python 3.10 ou superior; somente biblioteca padrão, sem novas dependências.
- Não modificar os módulos protegidos `dados.py`, `validar.py`, `potencia.py`, `medicao.py`, `nota.py`, `tempo.py` e `modelo.py` sem pedido explícito.
- Não refatorar o laço de eventos nem implementar etapas futuras para viabilizar um gráfico.
- Após mudanças, executar `python -m unittest discover -s testes` e `python simular.py exemplo_submissao.json`.
- Consultas de teste ao juiz dependem da autorização prevista no `AGENTS.md`, inclusive a validação gratuita de Bangkok descrita no roteiro. Abrir ou atualizar o relatório não pode disparar testes.
- Os kits são dados fictícios do cenário; as curvas são estimativas usadas pelo regulamento. Apresentar “simulação da janela pública”, sem sugerir telemetria operacional real da Localiza.
- A imagem contém requisitos de dashboard, não o regulamento completo. A regra oficial de agregação da nota entre agências não está implementada nos módulos examinados e não deve ser presumida.

## 3. Arquitetura e disponibilidade dos dados

### 3.1 Fluxo existente

```text
dados/<Agencia>/ + catálogo opcional
                |
          dados.carregar
                |
     validar.validar / normalizar
                |
           motor.simular
                |
  Resultado: retiradas, perdas, bins, trace, violações
                |
    medicao.metricas / medicao.series
                |
     nota.custo_infra / nota.pontuar, se houver catálogo
                |
        simular.py --series -> JSON

respostas/*.json -> comparação com o juiz salvo
lab/*.json/jsonl -> experimentos, estimativas e alternativas
```

| Componente | Papel e implicação para os gráficos |
|---|---|
| `kickoff/modelo.py` | Define agência, vagas elétricas, veículos, contratos, carregadores, entradas e cenário. É a referência das unidades e relações. |
| `kickoff/dados.py` | Converte CSV/Markdown em objetos; filtra categorias desconhecidas e contratos com devolução anterior à retirada. Agregações devem usar contratos carregados e a janela válida, não contar linhas brutas indiscriminadamente. |
| `kickoff/validar.py` | Normaliza políticas e demanda; calcula o limite efetivo. Deve ser reutilizado para identificar configurações equivalentes. |
| `kickoff/motor.py` | Implementa a operação das etapas 2 a 6. `agendar_eventos` e `on_evento` ainda são `pass` na etapa 7. |
| `kickoff/medicao.py` | Mede energia em intervalos de 15 minutos, calcula métricas e exporta as séries compatíveis com o juiz. |
| `kickoff/nota.py` | Calcula infraestrutura e seis contribuições da nota com custos e pesos do catálogo. |
| `simular.py` | Aceita uma submissão ou lista; `--series` inclui séries. Sem catálogo suficiente, emite `nota: null` e aviso. |
| `comparar.py` | Compara métricas e algumas séries com respostas salvas. Não calcula uma comparação completa das parcelas da nota. |
| `lab/comum.py` | Simulação local com métricas e séries, sem catálogo; fornece nomes de arquivos por configuração e cliente da API. |
| `lab/bateria.py` | Executa ou reutiliza respostas de Bangkok e acrescenta linhas a `resultados.jsonl`; não registra horário e pode repetir registros ao reutilizar arquivos. |
| `lab/conferir.py` | Reexecuta comparações locais com respostas existentes, sem chamar a API. |
| `lab/inferir.py` | Estima coeficientes por mínimos quadrados, recalculando métricas locais; salva `pesos_estimados.json`. Não deve ser executado automaticamente ao abrir o relatório. |
| `lab/otimizar.py`, `lab/melhor_nota.py` | Procuram maior nota estimada, usando coeficientes do laboratório. |
| `lab/varrer.py` | Prioriza menos perdas, depois obra, demanda e ponta. Sua ordenação não equivale à maior nota. |
| `lab/cenarios.py`, `lab/preview.py` | Preparam e comparam configurações locais. Alguns scripts escrevem arquivos ao executar; leitura de fonte é diferente de execução. |

### 3.2 Agências carregadas

Contagens obtidas pelo carregador existente; vagas são vagas elétricas, não capacidade total de estacionamento.

| Agência | Vagas elétricas | Frota | Contratos carregados | Entrada existente | Operação relevante |
|---|---:|---:|---:|---|---|
| Bangkok | 6 | 80 | 271 | B3 45 kVA / 40,5 kW úteis | Fecha às 18h em dias úteis; tutorial sem pontuação no consolidado competitivo. |
| Hanoi | 6 | 305 | 1.167 | B3 45 kVA / 40,5 kW úteis | Opera até 20h de segunda a sábado; domingo até 14h. |
| Istanbul | 4 | 235 | 1.293 | B3 45 kVA / 40,5 kW úteis | Aberta 24h, todos os dias. |
| Marrakech | 10 | 480 | 1.230 | B3 45 kVA / 40,5 kW úteis | Fecha às 18h em dias úteis e às 13h no sábado. |
| Zurich | 4 | 255 | 867 | B3 75 kVA / 67,5 kW úteis | Opera até 20h em dias úteis e até 14h no sábado. |

### 3.3 Artefatos existentes e lacunas

| Artefato | Situação observada | Consequência |
|---|---|---|
| `respostas/*.json` | 30 arquivos: 29 de Bangkok com séries e um placar de Istanbul sem séries. | Comparação temporal com o juiz está disponível para Bangkok. Não preencher séries ausentes de outras agências com zeros. |
| Séries de Bangkok | Cada resposta completa tem 2.688 intervalos de 15 min. | Quatro semanas públicas; requer seleção de dia/semana para leitura detalhada. |
| `lab/resultados.jsonl` | 27 registros, 27 chaves distintas, todos de Bangkok, sem timestamp. Há 21 `bate=true` e seis `false` históricos. | Não tratar esses indicadores antigos como validação do motor atual nem as linhas como horários. |
| `lab/melhor_nota_Istanbul.json` | Cinco alternativas ordenadas pela nota estimada. | Ranking de candidatos, não histórico de evolução. |
| `lab/varredura_Istanbul.json` | Cinco alternativas priorizando perdas e custo. | Comparação multicritério; ordem diferente do ranking por nota. |
| `lab/pesos_estimados.json`, `lab/pesos_bangkok.json` | Coeficientes inferidos e valores usados pelo laboratório. | Identificar como estimativa; uso em outra agência é hipótese, não confirmação de pesos oficiais. |
| `dados/catalogo.json` | Ausente na análise. | Cascata oficial recalculada e custo oficial local ainda não estão disponíveis. |
| Histórico de chamadas e avaliações | Sem registro completo de horário, ID de requisição, versão e seleção de solução. | Necessário para evolução de nota e contabilização confiável de m7Coins. |
| Eventos ao vivo | Interface aceita parâmetros, mas a aplicação no motor não está implementada. | Não afirmar que `--eventos` por si só reproduz o juiz com eventos. |

### 3.4 Evidência atual de comparação

Foi executado `python lab/conferir.py lab/subs_bangkok.json`, sem API. Resultado: **25/27 comparações passaram segundo os critérios atuais de `comparar.py`**. As duas divergências foram:

| Configuração / chave | Primeira divergência reportada |
|---|---|
| `Bangkok_ac_22x2x3_b3_45` | `series.potencia_kw`, sábado 30/10/2049 12:30 |
| `Bangkok_ac_7x2+dc_30x1_b3_45_prio-prox` | `series.potencia_kw`, segunda 25/10/2049 15:15 |

Esse resultado é mais atual que o campo `bate` do JSONL, mas tem limites: o comparador aceita tolerância relativa de 1% para energia total, usa 1e-6 nas demais métricas numéricas e séries, compara apenas a contagem das perdas e não compara o vetor de SOC. Também termina com código de saída zero mesmo quando há divergência. O painel deve informar o alcance da comparação, e não apenas mostrar um selo genérico “validado”.

## 4. Contrato de dados comum aos gráficos

### 4.1 Identificação e proveniência

Cada gráfico deve apontar para uma execução identificada, contendo agência, submissão normalizada, período, origem (`modelo` ou `juiz`), origem dos pesos (`catalogo_oficial`, `estimado` ou `ausente`), versão do motor e dos dados e conjunto de eventos.

“Modelo com pesos oficiais” continua sendo um resultado calculado pelo modelo; não vira resultado do juiz. Uma nota oficial recebida do juiz pode coexistir com parcelas estimadas localmente, desde que a distinção seja visível.

Não associar resposta e submissão apenas pelo nome do arquivo. As respostas atuais não embutem a submissão completa. Usar as listas e registros existentes para construir um manifesto explícito, marcando associações não comprovadas. A função `lab/comum.chave` é útil para localizar artefatos, mas não substitui um identificador canônico versionado.

Identificador recomendado: SHA-256 de JSON canônico com submissão normalizada; identificador da execução deve incluir também versões dos dados, eventos, motor e pesos. Duas avaliações da mesma configuração continuam sendo duas ocorrências distintas.

### 4.2 Tempo e unidades

- Época do cenário: `2049-10-17 00:00`, conforme `tempo.EPOCA`.
- Janela pública: `[1080, 41400)`, ou `[17/10/2049 18:00, 14/11/2049 18:00)`; fim exclusivo.
- Horário de um intervalo: `inicio_min + indice * passo_min`. O intervalo cobre esse instante até o seguinte.
- `nao_atendidos_min` contém deslocamentos relativos ao início da janela. Somar `inicio_min` antes de converter para data/hora.
- Os horários dos objetos `Retirada.t` são minutos absolutos desde a época; não somar T0 novamente.
- Os dias de calendário inicial e final são parciais: 28 dias de duração não significam 28 datas civis completas. Marcar cortes ao agregar por dia.
- O calendário operacional usa o fuso do cenário, sem identificador de fuso explícito nos objetos. Não aplicar o fuso geográfico presumido de Bangkok ou Istanbul.
- Horário real de uma avaliação é outro campo: persistir ISO 8601 com fuso, preferencialmente UTC; apresentar no fuso escolhido pela equipe.
- Unidades: potência em kW, energia em kWh, capacidade aparente em kVA, SOC em %, autonomia em km, nota/obra em pontos e gasto de testes em m7Coins.

### 4.3 Formatos de séries e agregação

O adaptador deve aceitar tanto `resposta.series` diretamente, como nas respostas atuais do juiz, quanto `resposta.series.publico`, emitido por `simular.py --series`. Ausência de uma chave significa dado indisponível, não uma série de zeros.

| Campo | Semântica | Agregação correta |
|---|---|---|
| `potencia_kw[i]` | Média de potência no intervalo de 15 min; calculada por `energia_do_bin * 4`. | Energia é soma de potência × duração em horas. Média de um período é ponderada pela duração; pico é máximo. |
| `plugados_max[i]` | Máximo dos estados registrados de veículos conectados naquele intervalo. | Máximo de intervalos para pico; média desses máximos não é ocupação média real. |
| `fila_max[i]` | Máximo da fila registrada segundo a convenção de compatibilidade do motor. | Não inferir espera média nem contagem real contínua a partir dessa série. |
| `soc_retirada` | Um SOC por atendimento, sem timestamp/ID na exportação. | Histograma do período completo; filtros temporais exigem dados adicionais. |
| `nao_atendidos_min` | Um deslocamento por atendimento perdido. | Contagem por intervalo, dia ou hora; preservar ocorrências simultâneas. |

Limitar resultados brutos do motor à janela pública: o motor pode processar devoluções e recargas após o fim da janela. Para intervalos de 15 min, `sum(potencia_kw) / 4` deve reproduzir a energia pública, dentro da tolerância numérica.

## 5. Requisitos por gráfico

### G01 — Cascata de pontos por agência e comparação com o juiz

**Pergunta:** de onde vêm os ganhos e as perdas da nota, e quanto o modelo difere do resultado do juiz?

**Dados:** métricas locais completas; `nota.ITENS`; pesos e custos oficiais quando disponíveis; `pontos.itens`, `pontos.nota`, `nota`, `valido` e `violacoes`; resposta salva do juiz da mesma submissão e contexto. Cada item de `pontos.itens` tem rótulo, quantidade, peso e contribuição.

**Visualização:** cascata de seis contribuições: categoria correta, upgrade, não atendimento, demanda contratada, energia de ponta e infraestrutura. Acrescentar total calculado, nota aplicada pelo simulador, nota do juiz e diferença `modelo - juiz`. Mostrar tabela com quantidade, unidade, coeficiente e produto.

**Cálculo:** reutilizar `nota.pontuar`; os pesos oficiais já carregam seu sinal. Não subtrair novamente um coeficiente negativo. O laboratório usa outra convenção: magnitudes positivas e subtração explícita, inclusive chaves prefixadas por `-` em um dos arquivos. Normalizar isso no adaptador, sem mudar os módulos.

**Cuidados:**

- `simular.py` aplica nota zero se houver violações, mesmo que `pontos.nota` seja diferente. Apresentar a condição e o ajuste de aplicação; a soma das parcelas explica o total bruto, não necessariamente a nota final aplicada.
- Sem catálogo, permitir uma cascata estimada, com versão e agência de origem dos coeficientes; mostrar “nota local oficial indisponível”.
- As respostas examinadas trazem nota e quatro métricas agregadas, não as seis contribuições oficiais. Não inventar uma segunda cascata detalhada do juiz.
- `lab/inferir.py` estima custo de equipamento multiplicado pelo peso de infraestrutura. Esse coeficiente efetivo não permite separar custo bruto e peso sem outra informação.
- Não truncar valores negativos nem usar escala logarítmica comum. Arredondar apenas para exibição.

**Aceitação:** soma das parcelas reproduz o total bruto; ajuste por violação é explícito; comparação só une execuções equivalentes; custo desconhecido não vira zero. A versão sem catálogo permanece utilizável para diagnóstico, mas identificada como estimada.

### G02 — Potência em 15 minutos, limite e ponta

**Pergunta:** quando a infraestrutura é exigida, quanto se aproxima do limite e como a política de ponta afeta a recarga?

**Dados:** `potencia_kw`, `inicio_min`, `passo_min`, submissão normalizada, `validar.limite_kw`, horários da agência e `tempo.eh_ponta`. Exibir modelo e juiz quando ambos tiverem séries.

**Visualização:** linha em degraus ou barras contíguas para média de cada intervalo; limite efetivo tracejado; faixa de ponta sombreada; indicação discreta de agência fechada. Eixo X com data e hora, Y em kW. Seleção de dia, semana e janela completa; detalhes com intervalo exato, potência e energia.

**Regras:** B3 usa `entrada.kw_util`; A4/SE usa demanda normalizada. Para `a4_150`, o teto contratável é 130 kW, embora a entrada tenha 135 kW úteis. Não desenhar 150 kW a partir do nome. Demanda omitida em A4/SE é normalizada ao teto; em B3 não existe demanda contratada, embora a métrica use zero por convenção.

**Cuidados:** ponta é segunda a sexta, `[18h,21h)`. Com `evitar_ponta`, pode haver veículos conectados consumindo zero. Fechamento não interrompe necessariamente a recarga. Não suavizar a curva; não chamar o máximo das médias de 15 min de pico instantâneo. Uma média abaixo do limite não comprova, isoladamente, ausência de qualquer ultrapassagem instantânea.

No estado atual, usar limite constante da configuração. Se eventos forem implementados depois, exportar a linha do tempo de limites efetivos antes de representá-los; não derivar limites dinâmicos de eventos que o motor ainda ignora.

**Aceitação:** 2.688 janelas no período completo atual; integração reproduz energia; máximo reproduz `pico_kw`; marcação da ponta segue o calendário do cenário; diferença modelo/juiz pode ser consultada no mesmo intervalo.

### G03 — Ocupação das vagas elétricas e saídas

**Pergunta:** as saídas instaladas ficam ocupadas e respeitam a capacidade de vagas elétricas?

**Dados:** `plugados_max`, `cenario.agencia.vagas`, quantidades de carregadores e `Carregador.saidas`; opcionalmente `Resultado.trace` para duração exata dos estados registrados.

**Visualização:** série em degraus de “máximo de veículos conectados por 15 min”, com referências de saídas instaladas e vagas elétricas. Inteiros no eixo Y. Exibir, se útil, `100 * plugados_max / saidas_instaladas`, rotulado como ocupação máxima por janela.

**Cuidados:** quantidade de carregadores difere da quantidade de saídas; `dc_60x2` tem duas saídas por unidade. Veículo conectado pode estar sem carregar por ponta, limite ou por atingir 80% com agência fechada. Ocupação de saídas não é utilização energética, nem quantidade total de carros no pátio. A fila não deve ser somada aos conectados para comparar com vagas elétricas.

O `trace` permite calcular ocupação média ponderada pelo tempo entre mudanças, cortando no período solicitado. O JSON compacto do juiz não permite recuperar esse indicador exato. Não apresentar médias de máximos como se fossem médias temporais.

**Aceitação:** referências calculadas pela configuração; conferir `plugados <= saidas <= vagas` nos dados aplicáveis; ausência de registros gera estado indisponível. Uma futura análise de ocupação total do pátio exige uma fonte adicional específica.

### G04 — Fila ao longo do tempo

**Pergunta:** em quais momentos a fila registrada cresce, e como isso coincide com potência, ocupação e perdas?

**Dados:** `fila_max`, `trace` local, horários da agência e política de prioridade.

**Visualização:** painel de degraus alinhado aos gráficos G02 e G03, com escala própria e contagens inteiras. Título obrigatório no estado atual: “Fila registrada — convenção do juiz”.

**Limitação central:** `FILA_COMO_JUIZ = True`. Em `Motor.anotar`, a fila exportada usa `fila_reg`; `plugar_fila` zera esse registro ao conectar um carro, e uma entrada posterior pode atualizá-lo para o tamanho real. Portanto, `fila_max` e o `trace` correspondente não garantem representar `len(self.fila)` ao longo de todo o tempo. Zero registrado não comprova ausência de carros aguardando.

**Cuidados:** não calcular tempo médio de espera, percentuais de veículos aguardando ou probabilidade de perda a partir dessa série. Não alterar o modo global do motor para “corrigir” um gráfico. Se a fila operacional real for necessária, especificar uma telemetria separada em trabalho posterior e autorizado, preservando a série de comparação com o juiz.

`menor_soc` ordena autonomia restante em km, não SOC percentual; usar essa explicação na legenda de políticas. `proxima_retirada` é prioridade por compatibilidade de categoria, não reserva exclusiva de um veículo.

**Aceitação:** semântica visível; série numérica preservada; filtros sincronizados com potência/ocupação; indisponibilidade de fila real explicitada. Comparação com o juiz não deve ser interpretada como validação da espera real.

### G05 — Distribuição de SOC na retirada

**Pergunta:** os clientes atendidos recebem veículos aptos e qual margem de carga existe na entrega?

**Dados:** `soc_retirada` para o período completo; para análises locais detalhadas, `Resultado.retiradas` fornece `t`, `contrato_id`, `veiculo_id`, `rank_pedido`, `rank_entregue` e `soc`.

**Visualização:** histograma em faixas fixas de 5 pontos percentuais, com referência em 80%; mostrar contagem e percentual dos atendidos. Destacar valores abaixo de 80%, se existirem, sem ocultá-los. Incluir 100% na última faixa e usar as mesmas faixas para comparar fontes. Indicadores opcionais: mínimo, mediana e tamanho da amostra.

**Cuidados:** SOC é percentual da bateria; dois modelos com o mesmo SOC podem ter autonomias distintas. Estoque inicial pode sair acima de 80%; isso não é violação. Clientes perdidos não têm SOC de retirada e não entram como zero. A amostra contém apenas atendimentos, e não resume sozinha a qualidade de atendimento de toda a demanda.

O vetor exportado pelo juiz não tem timestamps nem IDs. Não associá-lo por índice a todos os contratos, pois há perdas. Para filtrar SOC por dia/hora/categoria no modelo, exportar as retiradas detalhadas sem alterar `medicao.py`. Para o juiz, desabilitar esses filtros quando a associação não estiver disponível.

**Aceitação:** soma das frequências igual ao número de retiradas da fonte; faixas e bordas explícitas; amostra vazia apresentada como “sem retiradas”; tolerância numérica próxima de 80% documentada, sem esconder violações relevantes.

### G06 — Clientes perdidos por dia e hora

**Pergunta:** onde estão concentradas as perdas e qual é sua proporção frente à demanda?

**Dados:** `nao_atendidos_min`, `inicio_min`; contratos carregados para o denominador de demanda por horário. Na saída bruta local, perdas são apenas tempos absolutos, sem ID de contrato.

**Visualização:** mapa de calor com datas nas linhas e horas nas colunas, complementado por barras diárias. Disponibilizar alternância entre contagem e taxa de perda, com valores e denominadores no detalhe. Dias da semana agregados podem ser uma visão secundária.

**Cálculo:** `t = inicio_min + deslocamento`; agrupar por data/hora do cenário. Taxa da célula = `perdas / contratos previstos na célula * 100`. Zero contratos implica “não aplicável”, não 0% de perda. Usar apenas contratos válidos na janela e no mesmo conjunto de dados da avaliação.

**Cuidados:** cliente perdido não espera por outro carro. Não confundir fila de recarga com fila de clientes. Datas inicial/final têm cobertura parcial. Vários contratos podem ocorrer simultaneamente: manter multiplicidade e não deduplicar pelo minuto. Horário isolado não identifica com segurança a categoria ou a causa de cada perda.

**Aceitação:** soma das células igual ao total de perdas da fonte; taxa usa denominador correto; horários relativos são convertidos uma única vez; distinguir célula zero, sem demanda e sem dados. Modelo e juiz devem poder ser comparados por contagens horárias, além do total.

### G07 — m7Coins gastos no juiz por agência

**Pergunta:** quanto do orçamento de testes foi efetivamente gasto e em quais agências?

**Dados existentes:** `taxa`, `saldo` e `repetido` nas respostas; `taxa` e `saldo` no JSONL. Para contabilidade confiável, registrar cada chamada efetivamente realizada com ID de ocorrência, horário, agência, detalhe solicitado, resposta e cobrança.

**Visualização:** barras por agência em m7Coins; opcionalmente evolução acumulada dos gastos no horário real. Mostrar cobertura do registro e separar chamadas de testes de reaproveitamento de respostas locais.

**Cuidados:**

- Uma resposta salva pode ser lida muitas vezes. `lab/bateria.py` pode acrescentar novamente a taxa de uma resposta antiga ao log ao reutilizá-la; somar as linhas cegamente duplica gasto.
- Não deduplicar só por configuração: chamadas diferentes da mesma configuração podem ter contextos ou detalhes diferentes. Identificar a ocorrência de API; usar `repetido` e a taxa efetiva retornada.
- Custos documentados: Bangkok gratuito; outras agências, placar 20 e completo 50, com complemento de 30 quando o placar já foi pago, conforme o LEIAME. Esses valores não substituem o registro efetivo da resposta.
- Os arquivos examinados mostram taxa zero em Bangkok e uma resposta de Istanbul com taxa 20 e saldo 980. Isso evidencia essa cobrança, mas não prova que o diretório contém todo o histórico financeiro da equipe.
- `saldo` é uma fotografia global; não é gasto por agência nem valor a somar. Se faltarem chamadas, apresentar total “documentado”, não gasto definitivo.

**Aceitação:** importar duas vezes a mesma ocorrência não aumenta o total; ler cache não cria cobrança; falha sem informação de taxa permanece indeterminada; relatório não realiza consultas de teste automaticamente.

### G08 — Custo de obra por agência

**Pergunta:** qual infraestrutura foi escolhida e qual seu custo em pontos?

**Dados:** configuração selecionada por agência, `nota.custo_infra` com parcelas `carregadores`, `entrada` e `total`, catálogo oficial quando disponível. Alternativa provisória: `obra` nos resultados do laboratório e coeficientes estimados.

**Visualização:** barras empilhadas por agência, separando carregadores e mudança de entrada. Título indica “custo de obra” ou “penalidade estimada de infraestrutura”, conforme o dado. Exibir configuração e procedência no detalhe.

**Regras:** manter a entrada existente tem custo de troca zero; custos de carregadores são quantidade × custo unitário. Custo de obra difere de sua contribuição na nota, que inclui o peso de infraestrutura. Penalidade de demanda contratada deve aparecer separadamente; não é custo de equipamento.

**Cuidados:** não usar R$; não somar alternativas mutuamente exclusivas da mesma agência; usar uma seleção explícita. Não misturar custo bruto oficial com penalidade efetiva inferida na mesma série. Custo ausente não é custo zero. A parcela de entrada em Zurich depende de sua entrada existente B3 75, diferente das outras agências.

**Aceitação:** total igual à soma das parcelas; seleção por agência identificável; cenários estimados rotulados; unidades separadas do gráfico de m7Coins.

### G09 — Evolução de nota durante a competição

**Pergunta:** a equipe está melhorando as soluções ao longo do trabalho, com que evidência e em qual contexto de avaliação?

**Visualização principal:** pontos para cada avaliação e linha em degraus da melhor nota comparável já observada. Eixo X: horário real da avaliação; eixo Y: pontos. Painéis separados por agência e origem; estimativas locais e notas do juiz têm símbolos distintos. Exibir a configuração selecionada em uma série separada, caso a equipe registre escolhas.

**Dados e estratégia:** definidos em detalhe na seção 6. Sem timestamp confiável, oferecer somente eixo “ordem de registro”, explicitando essa limitação. Não transformar rankings `top 5` ou horários de contratos em histórico de avaliações.

**Consolidado:** excluir Bangkok do total competitivo. Enquanto a regra de consolidação oficial não estiver disponível, mostrar evolução por agência e, se necessário, uma soma explicitamente denominada “soma analítica das agências selecionadas”. Não chamá-la de nota oficial da equipe. Ausência de nota de uma agência torna o consolidado incompleto, não zero.

**Aceitação:** histórico preserva avaliações piores; melhor nota nunca usa observações futuras; segmentos com versões/eventos/pesos distintos não são unidos como se fossem diretamente comparáveis; nota desconhecida não entra na linha como zero.

### G10 — Justificativa da entrada elétrica e demanda contratada

**Pergunta:** por que a configuração escolhida é preferível às alternativas avaliadas?

**Dados:** alternativas de `lab/melhor_nota_Istanbul.json`, `lab/varredura_Istanbul.json`, submissões e novas simulações locais quando necessárias; limites normalizados, perdas, atendimento, pico de 15 min, energia de ponta, custos, nota e origem dos coeficientes.

**Visualização:** dispersão custo × atendimento ou custo × perdas, identificando configuração e nota; tabela comparativa das melhores alternativas; para A4/SE, curva de sensibilidade demanda × nota/perdas mantendo hardware e política fixos. Destacar a seleção e as alternativas dominadas dentro do conjunto avaliado.

**Cuidados:**

- Otimização por nota e busca de zero perdas são objetivos diferentes. O ranking de `varrer.py` é lexicográfico; o de `melhor_nota.py` usa nota estimada.
- Em Istanbul, o primeiro item salvo em `melhor_nota_Istanbul.json` tem obra estimada 9.250, duas perdas e nota estimada 8.419,8067. O primeiro de `varredura_Istanbul.json` tem obra estimada 10.250 e zero perdas. É uma comparação de escolhas, não uma prova de ótimo global.
- A resposta oficial salva de Istanbul usa a submissão recomendada com `proxima_retirada`; o primeiro item do ranking por nota usa `chegada`. Não subtrair essas notas e chamar o resultado de erro do simulador.
- Não definir demanda contratada pelo pico observado em uma única configuração: baixar o limite muda a dinâmica da recarga, a fila e o atendimento. Reexecutar cada alternativa.
- Maior potência instalada não garante mais potência efetiva: curvas dos veículos, compartilhamento das saídas e limite da agência restringem a entrega.
- Resultados dos 28 dias públicos não asseguram desempenho nas semanas ocultas. Qualificar a conclusão como melhor alternativa encontrada no conjunto e contexto avaliados.

**Aceitação:** cada ponto tem submissão recuperável; filtro usa mesma agência, período e versões; curvas de sensibilidade variam parâmetros identificados; justificativa final combina custo, serviço e nota, com as respectivas limitações.

## 6. Estratégia recomendada para evolução de nota

### 6.1 Registrar avaliações, não amostrar uma nota artificial a cada 15 minutos

A unidade natural já existente é a avaliação de uma submissão sobre a janela pública. `simular.py` gera um resultado por submissão; `lab/bateria.py` acrescenta um registro por cenário; as buscas locais produzem candidatos. Por isso, registrar cada avaliação é uma extensão pequena e verificável do fluxo existente.

Não é necessário consultar o juiz periodicamente para produzir uma linha contínua. Registrar simulações locais e as respostas de testes que forem autorizados; entre avaliações, a melhor nota conhecida permanece constante. Avaliações paralelas devem ter início e término reais; o resultado só passa a integrar o conhecimento da equipe quando termina.

### 6.2 Histórico proposto

Criar futuramente `analises/historico_avaliacoes.jsonl`, sem sobrescrever os registros antigos. Um gravador único deve receber resultados de trabalhadores paralelos; evitar várias escritas concorrentes no mesmo JSONL. `sqlite3` é alternativa da biblioteca padrão se o volume e a necessidade de transações justificarem.

| Campo proposto | Finalidade |
|---|---|
| `schema_version`, `avaliacao_id`, `sequencia` | Evolução do formato, identidade da ocorrência e desempate de ordenação. |
| `iniciada_em`, `concluida_em`, `importada_em` | Horários reais com fuso; permitir nulo para momento histórico desconhecido. |
| `agencia`, `periodo`, `inicio_min`, `fim_min` | Delimitar o cenário e a janela avaliada. |
| `submissao_normalizada`, `config_id` | Configuração completa e identificação canônica. |
| `origem_resultado`, `origem_pesos` | Separar modelo/juiz e catálogo/estimativa/ausência. |
| `motor_versao`, `dados_hash`, `pesos_hash`, `eventos_hash` | Reproduzir o contexto; commit sozinho não descreve alterações locais não commitadas. |
| `nota`, `nota_bruta`, `metricas`, `violacoes`, `valido` | Resultado e condições de aplicação da nota. |
| `detalhe`, `arquivo_resultado`, `resultado_hash` | Placar/completo, artefato imutável e integridade. |
| `chamada_id`, `taxa_m7coins`, `saldo_m7coins`, `repetido`, `reutilizado_localmente` | Relacionar avaliação e cobrança sem confundir cache com chamada. |
| `comparacao_id`, `escopo_comparacao` | Evidência de compatibilidade; distinguir métricas, séries, SOC e perdas por horário. |

Separar o diário de avaliações do diário de chamadas, ainda que relacionados por ID: uma avaliação local não é uma chamada, e a mesma resposta pode fundamentar várias análises. Um registro de seleção pode referenciar `avaliacao_id`, horário e motivo, sem alterar retroativamente o resultado.

Exemplo conceitual de metadados, com nulos intencionais para um legado sem horário:

```json
{
  "schema_version": 1,
  "avaliacao_id": "legado-bangkok-001",
  "sequencia": 1,
  "concluida_em": null,
  "agencia": "Bangkok",
  "origem_resultado": "juiz",
  "origem_pesos": "ausente",
  "periodo": "publico",
  "inicio_min": 1080,
  "fim_min": 41400,
  "arquivo_resultado": "respostas/bkk_exemplo.json",
  "nota": 14.47494914247065
}
```

Esse exemplo mostra campos parciais e não substitui o contrato completo. `origem_pesos: ausente` significa que não há pesos locais disponíveis nesse registro, não que a nota do juiz foi calculada sem pesos.

### 6.3 Regra da melhor nota

Para uma agência, origem e contexto comparáveis, calcular `melhor(t) = max(nota_i)` entre avaliações concluídas até `t` e aptas à seleção. Excluir entradas inválidas, resultados desconhecidos e configurações com violações da linha de “melhor solução válida”; mostrar suas ocorrências separadamente. Uma nota oficial aplicada por violação pode permanecer no histórico bruto.

Pesos, eventos ou regras novos abrem um novo segmento. Reavaliar candidatos sob o novo contexto para compará-los, preservando o histórico original. Não substituir uma nota antiga pelo resultado do motor atual na mesma linha.

No consolidado, guardar um conjunto selecionado com uma configuração por agência pontuada. Não somar todas as notas de todas as tentativas. Mostrar a cobertura e o horário da última avaliação de cada componente. Se a regra oficial permitir soma, documentar essa regra e sua versão antes de usar o rótulo oficial.

### 6.4 Migração dos arquivos atuais

1. Importar o JSONL como sequência de registros históricos, mantendo seus valores originais e sem inventar horário de conclusão.
2. Construir um manifesto associando submissões e respostas; reconhecer aliases e cópias da mesma resposta sem confundi-los com novas avaliações oficiais.
3. Tratar `melhor_nota_Istanbul.json` e `varredura_Istanbul.json` como conjuntos de candidatos sem cronologia conhecida.
4. Registrar reexecuções locais como novas avaliações, com data atual e versão do motor, vinculadas ao artefato anterior.
5. Não usar `mtime` do arquivo como horário de avaliação: cópia, edição e regeneração alteram esse valor. Se mantido para auditoria, chamar de data do arquivo.

### 6.5 Visão secundária: pontuação acumulada no tempo simulado

Pode ajudar a explicar em que dias ocorrem ganhos e perdas, mas deve ser chamada de “decomposição acumulada da nota no período simulado”. Não atende, sozinha, ao acompanhamento das decisões da equipe durante a competição.

É possível calculá-la localmente com retiradas detalhadas, tempos de perdas, energia em ponta por bin e pesos. Contar atendimentos corretos/upgrades pelo rank; acumular cada perda no seu instante; acumular energia de ponta conforme os bins. Demanda contratada e infraestrutura são termos fixos da avaliação e devem entrar uma única vez, por exemplo no início, com essa convenção declarada. Não descontá-los a cada janela.

O último ponto deve coincidir com a soma bruta das parcelas para a mesma janela; se houver aplicação de nota zero por violações, explicar esse ajuste separadamente. A resposta compacta do juiz não permite reconstruir toda essa decomposição por horário. Sem catálogo, a curva será estimada e assim deve ser identificada.

## 7. Implementação com as tecnologias disponíveis

### 7.1 Camada de exportação independente

Proposta de estrutura futura, ainda inexistente:

```text
analises/
  exportar.py                  # normalização, cálculo e rastreabilidade
  renderizar.py                # HTML/SVG com biblioteca padrão
  historico_avaliacoes.jsonl   # avaliações novas e importações identificadas
  historico_chamadas.jsonl     # ocorrências efetivas de API
  selecoes.jsonl               # decisões por agência
relatorios/
  index.html                  # pacote offline gerado
  dados/
    execucoes.csv
    series_15min.csv
    retiradas.csv
    perdas.csv
    pontos.csv
    chamadas.csv
    candidatos.csv
  manifesto.json
```

O exportador deve carregar dados pelo código existente e consumir artefatos salvos. Para obter detalhes locais adicionais, pode chamar `motor.simular` e serializar `Resultado.retiradas` e `trace` em arquivos auxiliares, sem alterar os módulos protegidos. Nunca executar scripts inteiros com efeitos colaterais apenas para aproveitar uma função.

Separar cálculo e desenho: o mesmo JSON/CSV alimentará SVG, Power BI ou uma ferramenta futura. Centralizar fórmulas no exportador para evitar versões diferentes da nota em Python, JavaScript e DAX.

### 7.2 Tabelas de exportação

| Tabela | Grão e campos essenciais |
|---|---|
| `execucoes` | Uma linha por avaliação; IDs, agência, origem, configuração, versões, horários, nota e validade. |
| `series_15min` | Uma linha por avaliação/origem/intervalo; início/fim, potência, energia, plugados máximos, fila registrada, limite, ponta e agência aberta. |
| `retiradas` | Uma linha por retirada local; IDs, horário, ranks e SOC. SOC do juiz sem identidade deve ficar em tabela de amostras própria, sem inventar chaves de contrato. |
| `perdas` | Uma linha por ocorrência; horário e origem. Usar sequência para preservar perdas simultâneas, com ID de contrato nulo quando desconhecido. |
| `pontos` | Uma linha por componente e avaliação; quantidade, unidade, coeficiente, contribuição e origem dos pesos. |
| `chamadas` | Uma linha por ocorrência real de consulta; taxa, saldo, horário e referência à resposta. |
| `candidatos` | Uma linha por alternativa avaliada; critérios de seleção, métricas e referência à execução. |

CSV com cabeçalho estável, codificação definida, datas ISO e números sem separador de milhar. Para Excel/Power BI, explicitar separador e localidade de importação; um perfil UTF-8 com BOM pode facilitar a abertura no Windows. JSON mantém números como números e ausência como `null`. Tratar dados textuais como texto na importação para evitar fórmulas involuntárias em planilhas.

### 7.3 Renderização HTML/SVG sem pacotes

Usar `json`, `csv`, `pathlib`, `datetime`, `collections`, `statistics`, `math`, `hashlib`, `html` e, se conveniente, `xml.etree.ElementTree`. SVG oferece retângulos para barras/cascata/mapa de calor, caminhos para séries e textos para eixos. Pode ser embutido em HTML e manipulado por JavaScript nativo. [MDN: SVG em HTML](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Structuring_content/Including_vector_graphics_in_HTML) e [scripts em SVG](https://developer.mozilla.org/en-US/docs/Web/SVG/Guides/Scripting).

Requisitos de implementação:

- Gerar um HTML autocontido ou um pacote com recursos locais; não depender de fontes externas nem bibliotecas por CDN.
- Para abertura direta por arquivo, embutir os dados necessários; não depender de `fetch` de arquivos locais, cujo comportamento é restrito em navegadores.
- Escapar textos com `html.escape`; ao embutir JSON em HTML, neutralizar `<` e sequências que possam encerrar o elemento de dados. Não inserir texto arbitrário com `innerHTML`.
- Usar `viewBox`, eixos legíveis, legenda com padrões além de cores, descrição textual e tabela alternativa dos dados.
- Renderizar séries por caminhos, em vez de milhares de elementos por ponto; filtrar período antes de detalhar a visualização.
- Fornecer SVG para exportação vetorial e CSS de impressão para salvar relatório em PDF pelo navegador. Geração automática de PNG/PDF de alta fidelidade não é recurso pronto da biblioteca padrão; avaliar separadamente se passar a ser requisito.
- Se necessário servir arquivos localmente, usar `http.server` vinculado a `127.0.0.1` e apenas a pasta `relatorios/`; não servir a raiz que contém credenciais e dados internos. Para o MVP autocontido, esse servidor é dispensável.

A principal desvantagem é implementar e manter escalas, eixos e componentes de desenho. Limitar o escopo a cascata, barras, degraus, histograma e matriz; evitar zoom complexo e edição de gráficos na primeira versão.

### 7.4 Comparação de alternativas

| Alternativa | Compatibilidade com a restrição | Utilidade e decisão |
|---|---|---|
| Python padrão + HTML/SVG + JavaScript nativo | Sem pacotes externos no projeto; navegador como visualizador. | Recomendada: dados reproduzíveis, exportação vetorial e apresentação offline. Exige desenho de componentes simples. |
| Python padrão + CSV + ferramenta de planilha já disponível | Exportador compatível; aplicação de apresentação independente. | Boa entrega rápida de barras, linhas e tabelas. Manter cálculos centrais fora de planilhas manuais. |
| `tkinter.Canvas` | Módulo padrão, mas disponibilidade de Tcl/Tk precisa ser verificada no ambiente. | Possível painel desktop; compartilhamento e exportação menos convenientes. Não é a primeira escolha. |
| Power BI Desktop com CSV/JSON | Uso externo independente, sem importação de pacote no simulador. | Útil se a equipe já domina e dispõe do aplicativo; avaliar custo de preparação do relatório. |
| Matplotlib em um novo script do repositório | Introduz dependência externa. | Adequado para figuras estáticas se a regra for alterada; não é a implementação compatível atual. |
| Plotly/Dash/Streamlit | Introduzem dependências externas. | Interatividade conveniente, mas ampliam instalação e manutenção. Não necessários para os requisitos atuais. |
| Biblioteca JavaScript de gráficos por CDN | Continua sendo dependência externa. | Não usar como atalho para contornar a restrição de bibliotecas Python. |

Separar um ambiente com Matplotlib ou Plotly não os torna biblioteca padrão. Um fluxo externo de apresentação pode ser considerado como ferramenta independente, mas sua incorporação ao projeto deve ser uma decisão explícita. Matplotlib exporta formatos como PNG/SVG/PDF; Plotly permite HTML interativo. [Matplotlib: savefig](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html), [Plotly: exportação HTML](https://plotly.com/python/interactive-html-export/).

## 8. Power BI e outras ferramentas externas

### 8.1 Uso independente recomendado como alternativa

O Power BI Desktop aceita fontes Text/CSV e JSON. Isso permite importar tabelas produzidas pelo exportador sem adicionar bibliotecas ao Python. [Microsoft: fontes do Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-data-sources).

Recomendação específica: usar as tabelas normalizadas em formato longo, relacionando-as por `avaliacao_id`, com dimensões de agência e calendário. Distinguir calendário simulado de data real de avaliação. Importar origem e versão como filtros obrigatórios. Não juntar tabelas de diferentes granularidades de modo que dupliquem valores de nota ou custo.

O ganho é acelerar filtros, comparação entre agências e montagem visual para uma equipe familiarizada com BI. O custo é manter um artefato adicional, o modelo de dados e o procedimento de atualização. Cascata e sombreamento temporal podem exigir preparação própria. Evitar reconstruir regras do motor em medidas DAX; importar as contribuições já calculadas.

Excel ou outra planilha já disponível também pode consumir CSV para apresentações simples. A preferência entre essas ferramentas depende do domínio da equipe; nenhuma delas foi verificada como instalada neste ambiente.

### 8.2 Integração é outro escopo

Atualizar relatórios por serviço, chamar APIs do Power BI, embutir painéis autenticados ou sincronizar fontes automaticamente acrescenta autenticação, configuração, operação e possivelmente licenciamento. Não há essa infraestrutura no repositório. Avaliar apenas se houver necessidade concreta de distribuição e atualização recorrente.

Publicar do Desktop para o serviço transfere o modelo e os relatórios para um workspace. “Publish to web” torna o conteúdo publicamente acessível; não equivale a compartilhamento privado. Esses mecanismos não são necessários para apresentar localmente o dashboard. [Microsoft: publicação pelo Desktop](https://learn.microsoft.com/en-us/power-bi/service-report-save) e [Publish to web](https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-publish-to-web).

O relatório externo deve consumir os resultados exportados. Não configurar o Power BI para chamar o endpoint pago do juiz em atualizações periódicas. Credenciais do jogo não pertencem a CSVs, HTML, planilhas ou modelos de apresentação distribuídos.

## 9. Apresentação, comparabilidade e manutenção

Cada página deve mostrar agência, configuração, período, origem dos dados, versão de pesos, horário de geração e cobertura disponível. Oferecer uma visão por agência e uma consolidada, sem misturar políticas ou alternativas no mesmo total.

Usar verde para ganhos, vermelho para perdas e cores distintas para modelo/juiz, sempre com legenda e padrões ou marcadores adicionais. Manter fundo simples, unidades nos eixos e escalas comparáveis. Evitar gráficos 3D, excesso de casas decimais, curvas suavizadas e eixos duplos que dificultem avaliar magnitudes.

A visão por agência deve reunir indicadores de atendimento, perdas, nota, energia, pico médio de 15 min e obra, seguidos pelos gráficos G01–G06. O consolidado contém G07–G10 e informa quantas agências têm resultados disponíveis. A tabela de comparação deve ficar acessível mesmo quando o gráfico não puder ser produzido.

O filtro temporal não pode alterar silenciosamente um número cuja granularidade não permite o filtro. Exemplo: ao selecionar um dia, o histograma do juiz sem timestamps deve permanecer explicitamente no período completo ou ficar indisponível. A nota de uma avaliação de 28 dias também não se transforma automaticamente na nota de um único dia.

Requisitos transversais de integridade:

- Preservar respostas brutas e gerar arquivos derivados em pasta separada.
- Não substituir nulos por zero; distinguir indisponível, sem ocorrência e não aplicável.
- Não arredondar dados antes de calcular totais ou comparar fontes.
- Comparar arrays apenas após conferir início, passo, tamanho, período e unidade.
- Comparar distribuição de SOC e horários de perdas quando existirem dados, além dos critérios limitados de `comparar.py`.
- Reutilizar a medição existente, inclusive sua convenção de estados registrados no mesmo instante, sem tentar corrigir o resultado apenas no desenho.
- Registrar mudanças de pesos e eventos; quebrar séries históricas quando a comparação deixa de ser equivalente.
- Não apresentar ausência de eventos no motor como simulação validada de contingências.

## 10. Roteiro de entrega e critérios de aceite

### Entrega 1 — Dados e gráficos operacionais offline

Criar o adaptador e o manifesto; começar com `exemplo_submissao.json` e sua resposta salva. Produzir G02–G06 em HTML/SVG, com tabelas e CSV. A comparação de Bangkok permite testar o desenho com dados reais do cenário sem nova chamada ao juiz. Incluir estado indisponível para agências sem série oficial.

### Entrega 2 — Pontuação e decisões

Adicionar G01, G08 e G10 usando estimativas claramente identificadas enquanto não houver catálogo. Importar o catálogo oficial quando fornecido e permitir trocar a origem sem reescrever os gráficos. Manter o significado de custo bruto separado de coeficiente inferido.

### Entrega 3 — Histórico e consolidado

Introduzir o registro de avaliações e chamadas; gerar G07 e G09, mostrando o legado por ordem de registro. Acrescentar seleção explícita de solução por agência e só implementar consolidação oficial quando sua regra estiver documentada. Exportar as mesmas tabelas para Power BI se houver vantagem prática para a equipe.

### Verificações obrigatórias da implementação futura

| Verificação | Resultado esperado |
|---|---|
| Formatos de série direto e `series.publico` | Mesmo conjunto normalizado de valores. |
| Janela pública e horários relativos | Primeiro intervalo em 17/10/2049 18h; último termina em 14/11/2049 18h; perdas posicionadas corretamente. |
| Energia e pico | Integração das médias confere com energia; máximo confere com o pico de 15 min. |
| Ocupação e fila | Quantidade de saídas calculada corretamente; fila identificada pela convenção efetivamente exportada. |
| Histograma e perdas | Frequências fecham com atendimentos/perdas; eventos simultâneos preservados; 100% incluído. |
| Nota e violações | Parcelas fecham com o total bruto; diferença para nota aplicada é explicada. |
| Histórico e cobrança | Reimportar artefato não cria avaliação oficial nem gasto novo; contexto e origem preservados. |
| Comparação | Divergência visual corresponde aos dados; não depender apenas do código de saída do comparador. |
| Ausências | Sem catálogo, série, retiradas ou histórico confiável produz mensagem adequada, nunca gráfico fictício. |
| Distribuição | HTML abre offline, SVG legível, nenhuma credencial exportada, tabelas recuperáveis. |

Testes novos devem focar transformações de dados e invariantes, sem criar testes que apenas repitam coordenadas ou cores do desenho. Depois de qualquer implementação, executar os dois comandos exigidos pelo `AGENTS.md`; a validação offline com respostas existentes é complementar e não consome m7Coins.

## 11. Decisões ainda dependentes de informação adicional

| Informação | Efeito | Conduta enquanto faltar |
|---|---|---|
| Catálogo oficial de custos e pesos por agência | Cascata e obra oficiais calculadas localmente. | Mostrar estimativas versionadas e resultado do juiz quando existente. |
| Regra de nota consolidada da competição | Total oficial da equipe e sua evolução. | Exibir por agência; soma analítica apenas com rótulo e cobertura explícitos. |
| Histórico de chamadas e avaliações com timestamps | Evolução horária anterior e gasto total auditável. | Legado por ordem de registro; gasto documentado com limite de cobertura. |
| Séries oficiais fora de Bangkok | Comparação temporal com outras agências. | Mostrar simulação local e placar disponível; não chamar API automaticamente. |
| Semântica e implementação dos eventos ao vivo | Limites dinâmicos, falhas e comparações sob eventos. | Informar que a etapa 7 está pendente. |
| Necessidade de fila operacional real | Análise de espera além da compatibilidade com o juiz. | Manter série atual rotulada e especificar telemetria separada para trabalho posterior. |

Essas lacunas não impedem iniciar o relatório operacional offline. Elas delimitam quais conclusões cada gráfico pode sustentar e quais resultados ainda precisam de uma fonte adicional.
