# Mapa Fiscal para CNPJ: 80795727000656
**Período de Análise:** 2023-01-16 a 2024-03-27

## 1. Resumo das Operações por Cabeçalho
| Natureza da Operação | Tipo de NF | Destino (UF) | Total de Documentos |
|----------------------|------------|--------------|---------------------|
| DEVOLUCAO | Entrada | MG | 1 |
| DEVOLUCAO DE COMPRA  UTILIZACAO NA PREST DE SERVIC | Saída | MG | 1 |
| DEVOLUCAO DE EMPRESTIMO | Saída | MG | 1 |
| REMESSA P/ARMAZENAGEM | Saída | MG | 2 |
| RETORNO DE COMODATO | Saída | MG | 1 |
| RETORNO DE COMODATO | Saída | SC | 1 |
| TRANSFERENCIA | Saída | SP | 1 |
| VENDA NO ESTADO | Saída | MG | 4 |

## 2. Detalhamento de Itens por Regime Fiscal (Matriz de Impostos)
| NCM | CFOP | ICMS (CST) | PIS (CST) | COFINS (CST) | Principais Naturezas de Operação | Total de Itens |
|-----|------|------------|-----------|--------------|----------------------------------|----------------|
| 22071090 | 5655 | 10 | 03 | 03 | VENDA NO ESTADO | 1 |
| 27101259 | 1661 | 60 | 07 | 07 | DEVOLUCAO | 1 |
| 27101259 | 5655 | 61 | 04 | 04 | VENDA NO ESTADO | 1 |
| 27101259 | 5656 | 61 | 04 | 04 | VENDA NO ESTADO | 1 |
| 27101259 | 5663 | 61 | 07 | 07 | REMESSA P/ARMAZENAGEM | 1 |
| 27101921 | 1661 | 60 | 07 | 07 | DEVOLUCAO | 1 |
| 27101921 | 5655 | 61 | 04 | 04 | VENDA NO ESTADO | 1 |
| 27101921 | 5663 | 61 | 07 | 07 | REMESSA P/ARMAZENAGEM | 2 |
| 27101921 | 5949 | 61 | 07 | 07 | DEVOLUCAO DE EMPRESTIMO | 1 |
| 38260000 | 5663 | 61 | 07 | 07 | REMESSA P/ARMAZENAGEM | 1 |
| 38260000 | 6659 | 61 | 07 | 07 | TRANSFERENCIA | 1 |
| 85044021 | 5909 | 41 | 07 | 07 | RETORNO DE COMODATO | 1 |
| 85072010 | 5909 | 41 | 07 | 07 | RETORNO DE COMODATO | 1 |
| 85176199 | 6909 | 40 | 07 | 07 | RETORNO DE COMODATO | 1 |
| 85177900 | 5909 | 41 | 07 | 07 | RETORNO DE COMODATO | 1 |
| 85291090 | 5909 | 41 | 07 | 07 | RETORNO DE COMODATO | 2 |
| 85311090 | 5909 | 41 | 07 | 07 | RETORNO DE COMODATO | 1 |
| 85369020 | 5909 | 41 | 07 | 07 | RETORNO DE COMODATO | 1 |
| 85444900 | 5210 | 00 | 07 | 07 | DEVOLUCAO DE COMPRA  UTILIZACAO NA PREST DE SERVIC | 1 |

## 3. Análise Qualitativa dos Códigos

### Códigos de Situação Tributária (CST) do ICMS
| CST ICMS | Descrição e Regime de Tributação |
|----------|----------------------------------|
| 00 | **Tributada Integralmente:** A operação é tributada pelo ICMS em sua totalidade, sem reduções ou isenções. |
| 10 | **Tributada e com cobrança do ICMS por Substituição Tributária:** A operação é tributada pelo ICMS, e o imposto já foi retido anteriormente por substituição tributária ou será retido na operação subsequente. |
| 40 | **Isenta:** A operação é isenta do ICMS, ou seja, não há incidência do imposto conforme legislação específica. |
| 41 | **Não Tributada:** A operação não é tributada pelo ICMS, geralmente por não se enquadrar no campo de incidência do imposto. |
| 60 | **ICMS cobrado anteriormente por substituição tributária:** O ICMS já foi recolhido anteriormente por Substituição Tributária (ST). O contribuinte que emite a nota não recolhe o ICMS novamente, pois o imposto já foi pago em etapa anterior da cadeia. |
| 61 | **ICMS cobrado anteriormente por substituição tributária (Não padrão):** Embora "61" não seja um CST padrão da tabela oficial do ICMS, sua proximidade com o "60" sugere que o ICMS foi cobrado anteriormente por substituição tributária, indicando que a operação subsequente não gera novo débito de ICMS para o emitente. Em um cenário real, este código exigiria validação ou esclarecimento junto à legislação específica ou sistema emissor. |

### Códigos de Situação Tributária (CST) do PIS e COFINS
| CST PIS/COFINS | Descrição e Regime de Tributação |
|----------------|----------------------------------|
| 03 | **Operação com Alíquota por Unidade de Medida de Produto (Monofásica):** Indica que o PIS/COFINS é recolhido em uma única etapa da cadeia produtiva (geralmente pelo fabricante ou importador), com alíquotas específicas por unidade de medida, e as etapas subsequentes são de alíquota zero. |
| 04 | **Operação Tributável - Tributação Monofásica - Revenda a Alíquota Zero:** Indica que o produto já teve o PIS/COFINS recolhido na etapa anterior (regime monofásico) e, na revenda, a alíquota é zero para evitar bitributação, pois o imposto já foi pago. |
| 07 | **Operação Isenta da Contribuição:** A operação é isenta do PIS/COFINS, ou seja, não há incidência dessas contribuições conforme legislação específica. |

### Códigos Fiscais de Operações e Prestações (CFOP)
| CFOP | Descrição e Implicação Fiscal |
|------|-------------------------------|
| 1661 | **Entrada de combustível ou lubrificante recebido em devolução de venda para consumidor ou usuário final:** Classifica a entrada de produtos (combustíveis/lubrificantes) que foram vendidos e estão sendo devolvidos por um consumidor final. (Operação de Entrada) |
| 5210 | **Devolução de compra para utilização na prestação de serviço:** Classifica a saída de mercadorias adquiridas para serem utilizadas na prestação de serviços, mas que estão sendo devolvidas ao fornecedor. (Operação de Saída) |
| 5655 | **Venda de combustível ou lubrificante de produção do estabelecimento, destinado a consumidor ou usuário final:** Classifica a venda de combustíveis ou lubrificantes produzidos pela empresa, diretamente para o consumidor final, dentro do estado. (Operação de Saída) |
| 5656 | **Venda de combustível ou lubrificante de produção do estabelecimento, destinado a consumidor ou usuário final, cuja operação tenha sido efetuada por meio de sistema de interligação de dutos, vasos ou tanques de armazenamento:** Similar ao 5655, mas específica para vendas realizadas através de sistemas de dutos, vasos ou tanques interligados, dentro do estado. (Operação de Saída) |
| 5663 | **Remessa de mercadoria para depósito fechado ou armazém geral:** Classifica a saída de mercadorias para serem armazenadas em depósito fechado ou armazém geral, sem que haja transferência de propriedade. (Operação de Saída) |
| 5909 | **Retorno de mercadoria ou bem remetido para depósito ou armazém geral ou para depósito fechado:** Classifica a saída de mercadorias ou bens que estavam em poder de terceiros (ex: em comodato, em depósito) e estão sendo devolvidos à empresa. (Operação de Saída, dentro do estado) |
| 5949 | **Outra saída de mercadoria ou prestação de serviço não especificado:** CFOP genérico para classificar outras saídas de mercadorias ou prestações de serviços que não possuem um código específico. (Operação de Saída, dentro do estado) |
| 6659 | **Transferência de combustível ou lubrificante de produção do estabelecimento, para outro estabelecimento da mesma empresa (interestadual):** Classifica a saída de combustíveis ou lubrificantes produzidos pela empresa, destinados a outro estabelecimento da mesma empresa, localizado em outro estado. (Operação de Saída Interestadual) |
| 6909 | **Retorno de mercadoria ou bem remetido para depósito ou armazém geral ou para depósito fechado (interestadual):** Similar ao 5909, mas para operações de retorno de mercadorias ou bens de outro estado. (Operação de Saída Interestadual) |