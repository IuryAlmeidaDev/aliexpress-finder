# Radar Mercado Livre: oportunidades para marca própria

Data: 2026-09-15. Status: desenho consolidado para revisão do usuário.

## Objetivo aprovado

Descobrir proativamente produtos com demanda brasileira e potencial para desenvolver marca própria. O usuário recebe uma seleção fundamentada para investigar fornecedores posteriormente. Relógios, óculos, camisetas e cadernos são exemplos do conceito, não limites de descoberta.

Demanda observada e potencial de marca são os dois eixos principais. Identificar uma marca aparentemente aplicada a um produto genérico é apenas uma evidência possível; a oportunidade também pode estar em acabamento, material, embalagem, kits, experiência ou extensão de linha.

Não fazem parte desta versão: cruzamento de preços ou busca automática no AliExpress/Alibaba, confirmação de fabricante, previsão de lucro, algoritmo genético, compras e criação de marcas. Os fluxos existentes permanecem independentes.

## Abordagem

Radar com histórico, execução manual e semanal. Uma coleta pontual não permite analisar evolução; uma plataforma completa acrescentaria complexidade antes de validar a qualidade das descobertas. A primeira versão usa regras determinísticas configuráveis, sem dependência de serviço de IA.

O mesmo serviço de aplicação atende CLI e agendamento. A execução semanal ocorre no VPS Oracle, segunda-feira às 07:00 em America/Sao_Paulo, configurável. A CLI pode executar o serviço no servidor via SSH para usar o histórico central ou localmente com banco separado; não haverá sincronização automática entre bancos.

## Descoberta e cobertura

Selecionar subcategorias por IDs da árvore oficial, com política configurável de inclusão e exclusão. Começar por organização doméstica, papelaria, acessórios e ferramentas manuais, expandindo dentro das famílias permitidas. Nenhuma família será declarada inteiramente segura: a elegibilidade é avaliada também por subcategoria e atributos. Excluir itens regulados, perigosos, perecíveis e de alto risco conforme política explícita; casos incertos ficam para revisão e fora da seleção prioritária.

Padrões iniciais: até 30 categorias por rodada, 20 resultados de mais vendidos por categoria, 100 candidatos enriquecidos e 30 oportunidades no relatório principal. Reservar 20% das categorias para rotação entre as elegíveis menos recentemente consultadas; as demais mantêm cobertura recorrente. Esses limites são ajustáveis e não representam cobertura de todo o Mercado Livre.

Mais vendidos são a semente principal. Tendências ampliam descoberta apenas quando houver resolução suportada para produtos; palavras de tendência sem resolução ficam registradas como pistas, sem pontuação de produto inventada. Categorias sem ranking são registradas como indisponíveis.

## Fontes e viabilidade

A documentação consultada descreve rankings por categoria, tendências, atributos e avaliações autenticadas. Isso não comprova acesso operacional da aplicação. A primeira etapa técnica deve validar autenticação e acesso real com credenciais autorizadas, incluindo resolução de ITEM, PRODUCT e USER_PRODUCT. IDs desses tipos não são intercambiáveis.

Fontes consultadas em 2026-09-15:

- https://developers.mercadolivre.com.br/pt_br/mais-vendidos-no-mercado-livre
- https://developers.mercadolivre.com.br/pt_br/tendencias
- https://developers.mercadolivre.com.br/pt_br/opinioes-sobre-um-produto
- https://developers.mercadolivre.com.br/pt_br/categorizacao-de-produtos
- https://developers.mercadolivre.com.br/pt_br/atributos
- https://developers.mercadolivre.com.br/itens-e-buscas

Recursos sem acesso ficam explicitamente indisponíveis. Não substituir por coleta não validada nem apresentar resultados simulados como reais. Sem acesso ao caminho essencial de descoberta e detalhes, a execução termina com diagnóstico de configuração; não publica um ranking de sucesso vazio. Autorização inicial da conta é dependência externa a resolver na implementação. Tokens ficam fora de Git, planilhas e logs; a integração deve tratar renovação e revogação.

## Evidências e identidade

Cada observação registra fonte, ID e tipo originais, categoria, instante UTC, URL, valores disponíveis e condição de coleta. Valores ausentes são nulos com motivo, nunca zero implícito. Vendas arredondadas ou em faixas preservam essa semântica; vendas acumuladas não são vendas semanais.

Agrupar por identificador de catálogo quando a relação for comprovada. Similaridade textual e atributos geram associação candidata, sem fundir automaticamente produtos distintos. Avaliações compartilhadas por catálogo contam uma vez; não somar avaliações de anúncios que apontem para a mesma origem.

Guardar evidências de demanda, avaliações, atributos, hipóteses de diferenciação, contrapontos e limitações. Uma marca desconhecida não prova white label. Origem estrangeira, personalização fabril e titularidade de marca não podem ser inferidas como fatos a partir de título ou foto.

## Avaliação explicável

Exibir duas notas separadas de 0 a 100, cobertura das evidências de cada nota e justificativas. Pesos iniciais são hipóteses de produto, versionadas para posterior ajuste.

Demanda: posição relativa no ranking da própria categoria (40%), volume de avaliações (20%), satisfação considerando tamanho da amostra (20%) e evolução histórica comparável (20%). Normalizar volume dentro da amostra da categoria; amostra insuficiente torna esse componente indisponível. Satisfação usa média suavizada em direção à média da amostra, com força inicial equivalente a 20 avaliações. Não equiparar posição em categorias diferentes a volume absoluto de vendas.

Potencial de marca: diferenciação concreta sustentada em atributos ou avaliações (40%), problemas recorrentes com oportunidade de melhoria (25%), indícios de produto genérico ou similar sob marcas distintas (20%) e possibilidade de linha apoiada em atributos/categorias relacionadas (15%). Cada componente usa rubrica 0, 0,5 ou 1, com evidências citadas. Zero significa evidência contrária; falta de evidência significa indisponível. A rubrica e os padrões textuais devem constar da configuração versionada.

Calcular cada nota pela média ponderada dos componentes observados, informando a fração de pesos coberta. Apenas candidatos com cobertura mínima de 60% em ambos os eixos e evidência de diferenciação entram na lista prioritária. Outros ficam na aba de investigação, inclusive quando a análise determinística não encontra indícios suficientes de marca própria.

Ordenar a lista prioritária pela média geométrica das duas notas; desempatar por cobertura e identidade estável. A nota combinada serve para priorizar investigação, não expressa probabilidade de sucesso ou retorno financeiro. Aplicar limite inicial de cinco produtos por categoria no top 30 e redistribuir vagas quando faltarem candidatos, para manter diversidade.

Análise de avaliações identifica temas por regras explícitas. Um tema é recorrente quando aparece em pelo menos três avaliações distintas da amostra consultada; informar numerador, tamanho da amostra e exemplos. Não generalizar a frequência da amostra como taxa de defeitos total. Sugestões sem evidência específica são hipóteses para revisão e não recebem pontos.

## Histórico

SQLite no VPS, independente dos bancos dos serviços existentes. Persistir execuções, categorias visitadas, entidades, observações, evidências e avaliações versionadas. Registrar modo manual/semanal, configuração, versão de regras, status e cobertura de coleta.

Comparar com a observação mais próxima de sete dias antes, dentro de janela de cinco a nove dias, da mesma entidade, categoria e métrica. Sem par compatível, mostrar histórico insuficiente. Uma entrada no radar não prova lançamento de produto; ausência após falha de coleta não significa saída do ranking. Mudança de quantidade de avaliações não equivale a quantidade de vendas.

Conservar dados medidos separados das notas para permitir reavaliação futura. O algoritmo genético futuro precisará de resultados reais de decisões e investimentos, não apenas notas produzidas por estas regras.

## Componentes e fluxo

- Cliente Mercado Livre: autenticação, requisições, resolução por tipo e normalização; sem regras de ranking.
- Descoberta: escolhe categorias e sementes conforme política e orçamento.
- Evidências: deduplicação, atributos e temas de avaliações, preservando proveniência.
- Avaliação: funções determinísticas recebem evidências e histórico e retornam notas, cobertura e explicações.
- Repositório SQLite: persistência e consultas temporais, sem dependência da CLI.
- Serviço de execução: coordena etapas, limites e estados de sucesso parcial ou falha.
- Relatório e CLI: apresentam resultado e exportam Excel, reaproveitando o padrão existente onde adequado.

Fluxo: configuração e acesso → categorias → sementes → detalhes e avaliações → persistência de observações → comparação temporal → avaliação → relatório.

A descoberta sem termo exige interface própria; não forçar o novo serviço no contrato existente search(query). A CLI existente recebe uma rota dedicada para o radar, mantendo o novo fluxo fora dos cálculos financeiros de importação.

## Operação e falhas

Agendamento por systemd timer persistente e execução manual do mesmo comando no VPS. Trava de processo impede sobreposição no mesmo banco. Banco e relatórios ficam em diretório persistente exclusivo do projeto; instalação futura deve inspecionar o VPS antes de escolher caminhos e limites. Não requer portas públicas nem alterações em serviços existentes.

Em 429, respeitar Retry-After; em erros transitórios, até três tentativas com espera progressiva e limite total. Em 401, tentar renovação uma vez quando configurada; em revogação ou 403, registrar indisponibilidade sem repetição infinita. Falhas isoladas produzem relatório parcial com cobertura; falha essencial produz saída de erro. Exportação deve ser atômica e nomes devem incluir ID da execução para não sobrescrever histórico.

## Relatório

Excel por execução com abas Oportunidades, Investigar, Evidências e Execução. Incluir notas separadas, cobertura, motivos, diferenciação sugerida, contrapontos, links, categoria, métricas observadas, comparação temporal e próximos pontos a confirmar com fornecedor. A aba Execução informa limites, falhas, data e versão das regras. Terminal apresenta resumo e caminho do arquivo. Não haverá envio automático de mensagens nesta versão.

## Validação e aceite

Testes relevantes cobrem resolução dos três tipos de identidade; deduplicação de catálogo; ausência de dados; avaliações compartilhadas; notas e cobertura; contrapontos de marca; temas recorrentes; janela histórica; falhas de acesso, limite de chamadas e execução parcial; concorrência e exportação. Reexecutar a suíte existente para verificar ausência de regressões.

Teste real autorizado deve demonstrar descoberta sem palavra-chave, obtenção de evidências e relatório rastreável. Fixtures validam comportamento, mas não comprovam acesso à API. Instalação semanal só é considerada concluída depois de validar execução manual no VPS, persistência e configuração do timer. Evolução semanal requer duas observações reais compatíveis; na primeira rodada, mostrar histórico insuficiente.

Sucesso funcional: uma execução autônoma produz candidatos com evidências de demanda e hipóteses fundamentadas de marca própria, ou explica claramente por que a cobertura foi insuficiente. Não preencher o top 30 com hipóteses fracas apenas para atingir uma quantidade. A qualidade comercial será refinada com a revisão do usuário após as primeiras rodadas.
