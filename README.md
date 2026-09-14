# AliExpress & Alibaba B2B Resale Opportunity Finder & Tax Calculator 🇧🇷

Ferramenta CLI profissional para prospecção, filtragem inteligente e análise de viabilidade financeira de produtos no **AliExpress (B2C)** e **Alibaba (B2B Atacado)** voltada para revenda no mercado brasileiro (Mercado Livre, Shopee, Amazon Brasil, etc.).

O sistema elimina anúncios ardilosos (peças/acessórios disfarçados de produtos completos), aplica filtros semânticos avançados com sinônimos bilíngues, calcula os tributos aduaneiros segundo as regras vigentes do **Remessa Conforme** (para compras individuais B2C) ou **Importação Formal de Atacado** (para lotes B2B do Alibaba) e calcula o preço de revenda ideal, investimento total, lucro líquido e ROI.

---

## 🚀 Funcionalidades Principais

- **🔎 Prospecção Multicanal (B2C & B2B):**
  - **AliExpress B2C (`--fonte ali`):** Focado em varejo e dropshipping. Permite busca via Scraper Direto (stealth headers) ou Conector Oficial TOP Protocol (HMAC-SHA256). Avalia reputação da loja e vendas unitárias sob o regime Remessa Conforme.
  - **Alibaba B2B Atacado (`--fonte alibaba`):** Focado em compras em lote e atacado internacional. Realiza extração direta de faixas de preço por atacado, Quantidade Mínima de Pedido (MOQ), tempo de empresa e selos de segurança de fornecedores.
- **🛡️ Pipeline de Filtros Inteligente:**
  - **Anti-Trick (Anti-Pegadinha):** Detecta e descarta anúncios que vendem apenas acessórios (ex: pulseiras, tampas, caixas ou ferramentas) a preços baixos quando o usuário busca pelo produto principal (ex: relógios, smartphones).
  - **Filtro Semântico Multilíngue:** Suporta termos obrigatórios e termos proibidos, com dicionário de sinônimos cruzados em Português e Inglês (ex: `safira` $\leftrightarrow$ `sapphire`, `estéril`/`sem logo` $\leftrightarrow$ `sterile dial`).
  - **Filtro de Reputação B2C:** Garante produtos com nota mínima de avaliação e volume mínimo de vendas no AliExpress.
  - **Filtro de Fornecedores e Escala B2B:** Filtra por teto de MOQ (`--max-moq`), fornecedores certificados (`--verificados` / *Verified Supplier*) e proteção comercial (`--trade-assurance`).
- **💰 Motores Tributários Brasileiros Precisos:**
  - **AliExpress (Remessa Conforme):**
    - $\le$ US$ 50,00: Alíquota de 20% de Imposto de Importação (II).
    - $>$ US$ 50,00: Alíquota de 60% de Imposto de Importação com dedução fixa de US$ 20,00.
    - **Modo Choice:** Suporte a subsídio de II em compras no AliExpress Choice (`--choice`).
    - **ICMS "Por Dentro":** Gross-up exato sobre a base aduaneira + II.
  - **Alibaba B2B (Atacado Formal):**
    - Alíquota fixa de 60% de Imposto de Importação sobre o valor aduaneiro total (sem faixa de isenção ou dedução de US$ 20).
    - ICMS calculado "por dentro" com base cheia ($V_{ad} + II$).
- **📈 Simuladores de Margem e Viabilidade Financeira:**
  - **Unitário (B2C):** Preço de venda sugerido, comissão do marketplace (ex: 16%), margem líquida alvo (ex: 40%), lucro unitário e ROI %.
  - **Lote de Atacado (B2B):** Custo unitário final desembarcado, investimento total do lote ($Custo \times MOQ$), receita bruta do lote, lucro líquido total do lote e ROI projetado.
- **📊 Saída Visual e Exportação:**
  - Tabelas ricas e coloridas no terminal via `rich` com layouts adaptados para varejo e atacado.
  - Exportação completa e estruturada em Excel: `oportunidades_aliexpress.xlsx` ou `oportunidades_alibaba.xlsx`.

---

## 📁 Arquitetura do Projeto

```text
aliexpress-finder/
├── src/
│   ├── cli/
│   │   ├── exporter.py          # Exportação para planilhas Excel (openpyxl/pandas)
│   │   ├── formatters.py        # Tabelas ricas no terminal (rich) para B2C e B2B
│   │   └── main.py              # Entrypoint da interface CLI unificada
│   ├── clients/
│   │   ├── alibaba_scraper.py   # Scraper direto do Alibaba B2B (preço, MOQ, selos)
│   │   ├── base_client.py       # Interface base para clientes de busca
│   │   ├── direct_scraper.py    # Scraper direto HTTP do AliExpress com stealth headers
│   │   └── official_api.py      # Conector oficial AliExpress TOP Protocol (HMAC-SHA256)
│   ├── filters/
│   │   ├── alibaba_pipeline.py  # Orquestrador de filtros B2B (MOQ, Verified, Trade Assurance)
│   │   ├── anti_trick.py        # Detecção de pegadinhas de acessórios/peças
│   │   ├── pipeline.py          # Orquestrador sequencial de filtragem B2C
│   │   ├── reputation.py        # Filtro de nota da loja e volume de vendas
│   │   └── semantic.py          # Validação de termos e mapa de sinônimos bilíngues
│   ├── finance/
│   │   ├── margins.py           # Simulação unitária de preço de venda, lucro e ROI
│   │   ├── taxes.py             # Motor de tributação B2C (Remessa Conforme + ICMS)
│   │   └── wholesale.py         # Motor tributário e financeiro B2B atacado (II 60% + lote)
│   └── config.py                # Gerenciamento de configurações e variáveis de ambiente
├── tests/                       # Suíte completa de testes unitários e de integração
│   ├── test_alibaba_cli.py
│   ├── test_alibaba_filters.py
│   ├── test_alibaba_integration.py # Teste de integração ponta a ponta Alibaba B2B
│   ├── test_alibaba_scraper.py
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_direct_scraper.py
│   ├── test_filters.py
│   ├── test_integration.py         # Teste de integração ponta a ponta AliExpress B2C
│   ├── test_margins.py
│   ├── test_official_api.py
│   ├── test_taxes.py
│   └── test_wholesale_finance.py
├── .env.example                 # Modelo de variáveis de ambiente
├── requirements.txt             # Dependências do projeto
└── README.md                    # Documentação do projeto
```

---

## ⚙️ Instalação e Configuração

### 1. Pré-requisitos
- Python 3.10 ou superior.
- Ambiente Windows, Linux ou macOS.

### 2. Clonar e Instalar Dependências

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/aliexpress-finder.git
cd aliexpress-finder

# Crie e ative um ambiente virtual
python -m venv venv

# No Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# No Linux/macOS:
# source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configuração do Arquivo `.env`

Copie o arquivo de exemplo `.env.example` para `.env`:

```bash
# No Windows (cmd ou powershell):
copy .env.example .env
# No Linux/macOS:
# cp .env.example .env
```

O arquivo `.env` contém as configurações padrão de taxas e margens:

```ini
ALIEXPRESS_APP_KEY=
ALIEXPRESS_APP_SECRET=
DEFAULT_USD_BRL=5.50
DEFAULT_ICMS_RATE=0.17
DEFAULT_MARKETPLACE_FEE=0.16
DEFAULT_TARGET_MARGIN=0.40
```

#### Como plugar a API Oficial do AliExpress (quando aprovada):
1. Acesse o [AliExpress Open Platform](https://open.aliexpress.com/) ou o portal de afiliados.
2. Crie uma aplicação para obter sua **App Key** e **App Secret**.
3. Preencha os campos no `.env`:
   ```ini
   ALIEXPRESS_APP_KEY=sua_app_key_aqui
   ALIEXPRESS_APP_SECRET=seu_app_secret_aqui
   ```
4. O sistema detectará automaticamente as chaves e utilizará o cliente oficial `OfficialAliExpressClient` via protocolo TOP. Caso os campos fiquem vazios, o sistema opera de forma transparente em modo **Direct Scraper**.

---

## 📖 Como Usar (Exemplos Práticos)

Para ver todos os comandos disponíveis:
```bash
python -m src.cli.main --help
```

### Parâmetros da Linha de Comando:

| Parâmetro | Tipo | Escopo | Descrição |
| :--- | :--- | :--- | :--- |
| `--fonte` | Escolha | Global | Fonte de dados: `ali` (AliExpress B2C, padrão) ou `alibaba` (Alibaba B2B Atacado). |
| `--busca` | Texto | Global | Termo principal de busca (ex: `"relogio automatico"` ou `"custom watch"`). |
| `--incluir` | Texto | Global | Termos ou sinônimos obrigatórios separados por vírgula (ex: `"safira, sterile"`). |
| `--excluir` | Texto | Global | Termos proibidos separados por vírgula (ex: `"quartz, pulseira"`). |
| `--max-custo` | Número | Global | Custo final unitário máximo desembarcado em R$ (Landed Cost). |
| `--margem` | Número | Global | Margem líquida mínima desejada em percentual (padrão: `40` para 40%). |
| `--choice` | Flag | AliExpress | Aplica o subsídio Choice (Imposto de Importação zerado, cobrando apenas ICMS de 17%). |
| `--min-vendas` | Número | AliExpress | Volume mínimo de vendas unitárias do anúncio (padrão: valor do `.env`). |
| `--min-nota` | Número | AliExpress | Avaliação mínima da loja/anúncio (padrão: valor do `.env`). |
| `--max-moq` | Número | Alibaba | Quantidade Mínima de Pedido (MOQ) máxima aceita (ex: `50`, `100`). |
| `--verificados` | Flag | Alibaba | Filtra apenas fornecedores certificados com selo `Verified Supplier`. |
| `--trade-assurance`| Flag | Alibaba | Filtra apenas fornecedores com garantia de proteção `Trade Assurance`. |
| `--exportar` | Flag | Global | Salva os resultados formatados em Excel (`oportunidades_aliexpress.xlsx` ou `oportunidades_alibaba.xlsx`). |

---

### Exemplos de Execução:

#### A. AliExpress B2C (`--fonte ali`)

##### 1. Minerando Relógios Automáticos de Safira com Mostrador Estéril:
```bash
python -m src.cli.main --fonte ali --busca "relogio automatico" --incluir "safira, sterile" --excluir "quartz, pulseira" --exportar
```

##### 2. Teto de Custo e Margem Alvo no Modo Choice (II Subsidiado):
```bash
python -m src.cli.main --fonte ali --busca "relogio automatico" --choice --max-custo 200 --margem 35 --exportar
```

##### 3. Fones de Ouvido Bluetooth com Filtro de Reputação:
```bash
python -m src.cli.main --fonte ali --busca "fone bluetooth anc" --incluir "cancelamento ativo" --excluir "capa, case, cabo" --min-vendas 50 --min-nota 4.7 --exportar
```

#### B. Alibaba B2B Atacado (`--fonte alibaba`)

##### 1. Prospecção de Lotes de Relógios em Atacado com Baixo MOQ:
Busca por fornecedores de relógios no Alibaba com pedido mínimo (MOQ) de até 50 peças, exigindo fornecedores auditados (*Verified Supplier*) e com cobertura *Trade Assurance*, exportando para `oportunidades_alibaba.xlsx`:
```bash
python -m src.cli.main --fonte alibaba --busca "watch" --incluir "silicone" --excluir "strap" --max-moq 50 --verificados --trade-assurance --exportar
```

##### 2. Prospecção de Fones TWS para Importação com Teto de Custo Unitário:
Filtra fornecedores onde o custo unitário final desembarcado (produto + 60% II + ICMS por dentro) não ultrapasse R$ 35,00 por peça, com MOQ de até 100 unidades e margem de revenda projetada de 50%:
```bash
python -m src.cli.main --fonte alibaba --busca "bluetooth earphones" --max-moq 100 --max-custo 35 --margem 50 --verificados --exportar
```

##### 3. Acessórios e Gadgets Tecnológicos com Trade Assurance:
```bash
python -m src.cli.main --fonte alibaba --busca "smart ring" --max-moq 30 --trade-assurance --exportar
```

---

## 🧮 Metodologia de Cálculo Financeiro e Tributário

O sistema possui dois motores de cálculo financeiro e tributário especializados:

### 1. AliExpress B2C: Programa Remessa Conforme

Aplicado quando `--fonte ali`:

#### A. Valor Aduaneiro ($V_{ad}$)
$$V_{ad\text{ (BRL)}} = \text{Preço do Produto} + \text{Frete}$$
$$V_{ad\text{ (USD)}} = \frac{V_{ad\text{ (BRL)}}}{\text{Cotação USD/BRL}}$$

#### B. Imposto de Importação (II)
- **Modo Choice (`--choice`):** $II = \text{R\$ } 0{,}00$ (subsídio integral da plataforma).
- **Remessas até US$ 50,00:**
  $$II = V_{ad\text{ (BRL)}} \times 0{,}20$$
- **Remessas acima de US$ 50,00:**
  $$II = \max\left(0\,,\; (V_{ad\text{ (BRL)}} \times 0{,}60) - (20{,}00 \times \text{Cotação USD/BRL})\right)$$

#### C. ICMS Calculado "Por Dentro" (Grossed-Up)
$$\text{Base ICMS} = \frac{V_{ad\text{ (BRL)}} + II}{1 - \text{Alíquota ICMS}}$$
$$\text{Valor ICMS} = \text{Base ICMS} \times \text{Alíquota ICMS}$$

#### D. Custo Final Desembarcado Unitário (Landed Cost)
$$\text{Custo Final} = V_{ad\text{ (BRL)}} + II + \text{ICMS}$$

#### E. Simulação de Preço de Venda Unitário
$$\text{Preço Sugerido de Venda} = \frac{\text{Custo Final}}{1 - \text{Taxa Marketplace} - \text{Margem Líquida Alvo}}$$
$$\text{Comissão Marketplace (R\$)} = \text{Preço Sugerido} \times \text{Taxa Marketplace}$$
$$\text{Lucro Líquido Unitário (R\$)} = \text{Preço Sugerido} - \text{Comissão Marketplace} - \text{Custo Final}$$
$$\text{ROI (\%)} = \left(\frac{\text{Lucro Líquido}}{\text{Custo Final}}\right) \times 100\%$$

---

### 2. Alibaba B2B: Atacado e Importação Formal em Lotes

Aplicado quando `--fonte alibaba`. Em compras comerciais de atacado não há enquadramento no Remessa Conforme (sem faixa de isenção até US$ 50 e sem dedução fixa de US$ 20).

#### A. Imposto de Importação Fixo de 60%
Aplica-se a alíquota cheia sobre o valor unitário:
$$II_{\text{unit}} = V_{ad\text{ (BRL)}} \times 0{,}60$$

#### B. ICMS Calculado "Por Dentro" sobre a Base Cheia
O ICMS integra sua própria base sobre o somatório de $V_{ad} + II$:
$$\text{Base ICMS}_{\text{unit}} = \frac{V_{ad\text{ (BRL)}} + II_{\text{unit}}}{1 - \text{Alíquota ICMS}}$$
$$\text{ICMS}_{\text{unit}} = \text{Base ICMS}_{\text{unit}} \times \text{Alíquota ICMS}$$

#### C. Custo Unitário Final Desembarcado
$$\text{Custo Unitário Final} = V_{ad\text{ (BRL)}} + II_{\text{unit}} + \text{ICMS}_{\text{unit}}$$

#### D. Investimento Total no Lote
Calculado para o lote completo com base na Quantidade Mínima de Pedido (MOQ):
$$\text{Investimento Total Lote} = \text{Custo Unitário Final} \times MOQ$$

#### E. Simulação de Revenda do Lote e ROI
Considerando a revenda unitária de todas as unidades do lote nos marketplaces:
$$\text{Preço Unitário Sugerido} = \frac{\text{Custo Unitário Final}}{1 - \text{Taxa Marketplace} - \text{Margem Líquida Alvo}}$$
$$\text{Receita Bruta Total} = \text{Preço Unitário Sugerido} \times MOQ$$
$$\text{Comissão Marketplace Total} = \text{Receita Bruta Total} \times \text{Taxa Marketplace}$$
$$\text{Lucro Líquido do Lote} = \text{Receita Bruta Total} - \text{Comissão Marketplace Total} - \text{Investimento Total Lote}$$
$$\text{ROI do Lote (\%)} = \left(\frac{\text{Lucro Líquido do Lote}}{\text{Investimento Total Lote}}\right) \times 100\%$$

---

## 🧪 Execução dos Testes

O projeto conta com cobertura total de testes unitários e testes de integração de ponta a ponta utilizando `pytest`.

### Rodar Toda a Suíte de Testes:
```bash
python -m pytest -v
```
*(ou simplesmente `pytest -v`)*

### Teste de Integração Ponta a Ponta - AliExpress B2C:
Valida raspagem/dados, filtro anti-pegadinha, semântica, impostos Remessa Conforme, margens de revenda e exportação Excel:
```bash
python -m pytest tests/test_integration.py -v
```

### Teste de Integração Ponta a Ponta - Alibaba B2B:
Valida pipeline de filtros B2B (MOQ, fornecedores verificados e Trade Assurance), motor tributário de atacado (II 60% e ICMS por dentro), simulação financeira de lotes e exportação para `oportunidades_alibaba.xlsx`:
```bash
python -m pytest tests/test_alibaba_integration.py -v
```

---

## 📄 Licença

Projeto desenvolvido para fins educacionais e de pesquisa de mercado. Consulte os termos de serviço e diretrizes do AliExpress e Alibaba ao realizar coletas automatizadas.
