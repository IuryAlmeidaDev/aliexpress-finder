---
id: instalacao-e-configuracao
title: Instalação e Configuração
sidebar_position: 2
---

# Instalação e Configuração

Este guia orienta a configuração do ambiente para rodar o **AliExpress & Alibaba Finder** no seu computador ou servidor.

---

## 📋 Pré-requisitos

* **Python:** Versão 3.10, 3.11 ou 3.12 instalada ([python.org](https://www.python.org/downloads/)).
* **Git:** Para clonar o repositório.
* **Sistema Operacional:** Windows, Linux ou macOS.

---

## 🛠️ Passo a Passo de Instalação

### 1. Clonar o Repositório
```bash
git clone https://github.com/IuryAlmeidaDev/aliexpress-finder.git
cd aliexpress-finder
```

### 2. Criar e Ativar o Ambiente Virtual

Recomendamos utilizar um ambiente virtual (`venv`) para isolar as bibliotecas:

* **No Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
* **No Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 4. Executar os Testes Unitários
Para validar se todos os módulos, scrapers e motores matemáticos estão operando corretamente:
```bash
pytest
```
*Deverá exibir 86 testes passando (100% de cobertura).*

---

## ⚙️ Variáveis de Ambiente (`.env`)

Copie o arquivo de exemplo para criar sua configuração local:

```bash
cp .env.example .env
```

Abra o arquivo `.env` para ajustar os parâmetros econômicos conforme sua realidade:

| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `DEFAULT_USD_BRL` | `5.50` | Cotação padrão do Dólar Americano em Reais para conversão de custos e tetos de importação. |
| `DEFAULT_ICMS_RATE` | `0.17` | Alíquota de ICMS do estado de destino (ex: 0.17 para 17% ou 0.20 para 20%). |
| `DEFAULT_MARKETPLACE_FEE` | `0.16` | Taxa média de comissão dos marketplaces (16% é a média do Mercado Livre Premium e Shopee). |
| `DEFAULT_TARGET_MARGIN` | `0.40` | Margem líquida mínima padrão desejada sobre o preço de venda (40%). |

### Credenciais Opcionais

* **API TOP do AliExpress (`ALIEXPRESS_APP_KEY`, `ALIEXPRESS_APP_SECRET`):**
  * *Opcional:* Se deixadas vazias, o sistema automaticamente utiliza o **Scraper Stealth com impersonação de navegador Chrome 124 (`curl_cffi`)**, funcionando imediatamente sem necessidade de chaves de desenvolvedor.
* **Radar Mercado Livre (`MERCADO_LIVRE_CLIENT_ID`, `MERCADO_LIVRE_CLIENT_SECRET`):**
  * Necessário apenas se você desejar autenticar a API oficial de desenvolvedor do Mercado Livre para análise em lote de categorias internas. A busca por concorrência funciona independentemente dessas credenciais.
