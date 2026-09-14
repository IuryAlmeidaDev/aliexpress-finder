# AliExpress Resale Opportunity Finder & Tax Calculator 🇧🇷

Ferramenta CLI profissional para prospecção, filtragem inteligente e análise de viabilidade financeira de produtos no **AliExpress** voltada para revenda no mercado brasileiro (Mercado Livre, Shopee, Amazon Brasil, etc.).

O sistema elimina anúncios ardilosos (peças/acessórios disfarçados de produtos completos), aplica filtros semânticos avançados com sinônimos bilíngues, calcula os tributos aduaneiros segundo as regras vigentes do **Remessa Conforme** (Imposto de Importação + ICMS por dentro) e calcula o preço de revenda ideal, lucro líquido e ROI.

---

## 🚀 Funcionalidades Principais

- **🔎 Busca Flexível:**
  - **Scraper Direto (Stealth):** Funciona de imediato sem necessidade de chaves de API, com headers otimizados e parsing resiliente de HTML/JSON.
  - **Conector Oficial AliExpress (TOP Protocol):** Estruturado com assinatura digital criptográfica HMAC-SHA256 pronto para plugar sua `App Key` e `App Secret` assim que aprovado no portal de desenvolvedores do AliExpress.
- **🛡️ Pipeline de Filtros Inteligente:**
  - **Anti-Trick (Anti-Pegadinha):** Detecta e descarta anúncios que vendem apenas acessórios (ex: pulseiras, tampas, caixas ou ferramentas) a preços baixos quando o usuário busca pelo produto principal (ex: relógios, smartphones).
  - **Filtro Semântico Multilíngue:** Suporta termos obrigatórios e termos proibidos, com dicionário de sinônimos cruzados em Português e Inglês (ex: `safira` $\leftrightarrow$ `sapphire`, `estéril`/`sem logo` $\leftrightarrow$ `sterile dial`).
  - **Filtro de Reputação:** Garante produtos com nota mínima de avaliação e volume mínimo de vendas para evitar fornecedores de risco.
- **💰 Motor Tributário Brasileiro Preciso:**
  - Aplica o cálculo oficial do **Remessa Conforme**:
    - $\le$ US$ 50,00: Alíquota de 20% de Imposto de Importação (II).
    - $>$ US$ 50,00: Alíquota de 60% de Imposto de Importação com dedução fixa de US$ 20,00.
    - **ICMS Calculado "Por Dentro":** Gross-up exato sobre a base aduaneira + II.
- **📈 Simulador de Margem e Viabilidade Financeira:**
  - Determinação do preço de venda sugerido com base na comissão do marketplace (ex: 16%) e margem líquida desejada (ex: 40%).
  - Cálculo de Lucro Líquido e Retorno sobre o Investimento (ROI %).
- **📊 Saída Visual e Exportação:**
  - Tabela colorida e interativa no terminal usando `rich`.
  - Exportação completa dos resultados formatados para planilhas Excel (`.xlsx`).

---

## 📁 Arquitetura do Projeto

```text
aliexpress-finder/
├── src/
│   ├── cli/
│   │   ├── exporter.py       # Exportação para planilhas Excel (openpyxl/pandas)
│   │   ├── formatters.py     # Tabelas ricas no terminal (rich)
│   │   └── main.py           # Entrypoint da interface CLI
│   ├── clients/
│   │   ├── base_client.py    # Interface base para clientes de busca
│   │   ├── direct_scraper.py # Scraper direto HTTP com stealth headers
│   │   └── official_api.py   # Conector oficial TOP Protocol (HMAC-SHA256)
│   ├── filters/
│   │   ├── anti_trick.py     # Detecção de pegadinhas de acessórios/peças
│   │   ├── pipeline.py       # Orquestrador sequencial de filtragem
│   │   ├── reputation.py     # Filtro de nota da loja e volume de vendas
│   │   └── semantic.py       # Validação de termos e mapa de sinônimos bilíngues
│   ├── finance/
│   │   ├── margins.py        # Simulação de preço de venda, lucro e ROI
│   │   └── taxes.py          # Motor de tributação aduaneira (Remessa Conforme + ICMS)
│   └── config.py             # Gerenciamento de configurações e variáveis de ambiente
├── tests/                    # Suíte completa de testes unitários e de integração
├── .env.example              # Modelo de variáveis de ambiente
├── requirements.txt          # Dependências do projeto
└── README.md                 # Documentação do projeto
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
| Parâmetro | Tipo | Descrição |
| :--- | :--- | :--- |
| `--busca` | Texto (Obrigatório) | Termo principal de busca no AliExpress (ex: `"relogio automatico"`). |
| `--incluir` | Texto (Opcional) | Termos ou sinônimos obrigatórios separados por vírgula (ex: `"safira, sterile"`). |
| `--excluir` | Texto (Opcional) | Termos proibidos separados por vírgula (ex: `"quartz, pulseira"`). |
| `--max-custo` | Número (Opcional) | Custo final máximo desembarcado no Brasil em R$ (Landed Cost). |
| `--margem` | Número (Opcional) | Margem líquida mínima desejada em percentual (padrão: `40` para 40%). |
| `--exportar` | Flag | Se presente, salva a tabela final em uma planilha Excel (`oportunidades_aliexpress.xlsx`). |

---

### Exemplos de Execução:

#### 1. Minerando Relógios Automáticos de Safira com Mostrador Limpo (Estéril):
Busca por relógios mecânicos automáticos, exigindo cristal de safira e mostrador estéril (sem logo/sterile), descartando modelos de quartzo ou peças avulsas, e exportando para o Excel:

```bash
python -m src.cli.main --busca "relogio automatico" --incluir "safira, sterile" --excluir "quartz, pulseira" --exportar
```

#### 2. Definindo Teto de Custo e Margem de Lucro Alvo:
Filtrar produtos onde o custo total desembarcado no Brasil (produto + frete + todos os tributos) não passe de R$ 350,00, buscando uma margem líquida de 35%:

```bash
python -m src.cli.main --busca "relogio automatico" --incluir "safira" --max-custo 350 --margem 35 --exportar
```

#### 3. Busca por Fones de Ouvido TWS de Alta Fidelidade:
```bash
python -m src.cli.main --busca "fone bluetooth anc" --incluir "cancelamento ativo" --excluir "capa, case, cabo" --margem 50 --exportar
```

---

## 🧮 Metodologia de Cálculo Financeiro e Tributário

O motor financeiro implementa a legislação tributária brasileira vigente (programa **Remessa Conforme** / Lei 14.902/2024 e convênio ICMS):

### 1. Valor Aduaneiro ($V_{ad}$)
$$V_{ad\text{ (BRL)}} = \text{Preço do Produto} + \text{Frete}$$
$$V_{ad\text{ (USD)}} = \frac{V_{ad\text{ (BRL)}}}{\text{Cotação USD/BRL}}$$

### 2. Imposto de Importação (II)
- **Para remessas até US$ 50,00:**
  $$II = V_{ad\text{ (BRL)}} \times 0{,}20$$
- **Para remessas acima de US$ 50,00:**
  $$II = \max\left(0\,,\; (V_{ad\text{ (BRL)}} \times 0{,}60) - (20{,}00 \times \text{Cotação USD/BRL})\right)$$
  *(Aplica-se alíquota de 60% com a dedução legal de US$ 20,00).*

### 3. ICMS Calculado "Por Dentro" (Grossed-Up)
No Brasil, o ICMS integra a sua própria base de cálculo:
$$\text{Base ICMS} = \frac{V_{ad\text{ (BRL)}} + II}{1 - \text{Alíquota ICMS}}$$
$$\text{Valor ICMS} = \text{Base ICMS} \times \text{Alíquota ICMS}$$

*(A alíquota padrão configurada é de 17%, podendo ser ajustada via `.env`)*.

### 4. Custo Final Desembarcado (Landed Cost)
$$\text{Custo Final} = V_{ad\text{ (BRL)}} + II + \text{ICMS}$$

### 5. Simulação de Preço de Venda, Lucro e ROI
Para obter a margem líquida desejada após o pagamento da comissão da plataforma de venda (Mercado Livre, Shopee, etc.):
$$\text{Preço Sugerido de Venda} = \frac{\text{Custo Final}}{1 - \text{Taxa Marketplace} - \text{Margem Líquida Alvo}}$$
$$\text{Comissão Marketplace (R\$)} = \text{Preço Sugerido} \times \text{Taxa Marketplace}$$
$$\text{Lucro Líquido (R\$)} = \text{Preço Sugerido} - \text{Comissão Marketplace} - \text{Custo Final}$$
$$\text{ROI (\%)} = \left(\frac{\text{Lucro Líquido}}{\text{Custo Final}}\right) \times 100\%$$

---

## 🧪 Execução dos Testes

O projeto conta com cobertura total de testes unitários e de integração utilizando `pytest`.

Para rodar todos os testes do projeto:
```bash
python -m pytest -v
```

Para rodar especificamente o teste de integração ponta a ponta:
```bash
python -m pytest tests/test_integration.py -v
```

*(Dica: se preferir invocar diretamente o comando `pytest`, utilize `pytest -o pythonpath=. -v`).*

---

## 📄 Licença

Projeto desenvolvido para fins educacionais e de pesquisa de mercado. Consulte os termos de serviço e diretrizes do AliExpress ao realizar coletas automatizadas.
