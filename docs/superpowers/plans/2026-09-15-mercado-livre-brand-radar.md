# Plano de implementação: Radar Mercado Livre para marca própria

**Objetivo:** adicionar descoberta autônoma de produtos brasileiros com evidências de demanda e potencial de marca própria, com histórico SQLite, relatório Excel, execução manual e agendamento semanal.

**Arquitetura:** um cliente oficial do Mercado Livre normaliza rankings, entidades e avaliações; um serviço de radar coordena descoberta, persistência e pontuação explicável; CLI e timer usam o mesmo serviço. O fluxo permanece isolado dos cálculos AliExpress/Alibaba.

**Especificação:** `docs/superpowers/specs/2026-09-15-mercado-livre-brand-radar-design.md`

## Etapas

1. Ampliar configuração e criar modelos, erros e cliente HTTP do Mercado Livre, incluindo ITEM, PRODUCT e USER_PRODUCT.
2. Criar política de categorias, extração determinística de evidências de marca e pontuação com cobertura explícita.
3. Criar repositório SQLite para execuções, observações, resultados e comparação semanal.
4. Criar serviço orquestrador, relatório Excel com quatro abas e resumo de terminal.
5. Integrar a rota `--fonte mercado-livre` à CLI sem exigir `--busca`, preservando os fluxos existentes.
6. Adicionar unidades systemd parametrizadas e documentação de configuração e operação.
7. Testar normalização, pontuação, histórico, relatório, CLI, falhas e regressões da suíte completa.
8. Validar no VPS, instalar em diretório próprio e habilitar o timer somente após credenciais reais estarem configuradas.

## Limites de entrega

Sem token autorizado, a entrega comprova comportamento por testes e fornece diagnóstico operacional; não afirma que a coleta real funcionou. O timer pode ser instalado desabilitado, aguardando credenciais. A primeira execução real não terá evolução semanal e deverá registrar histórico insuficiente.
