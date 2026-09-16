import pytest
from src.competitors.extractors.router import get_extractor_for_url
from src.competitors.extractors.mercadolivre import MercadoLivreExtractor
from src.competitors.extractors.universal import UniversalWebExtractor

def test_router_selects_mercadolivre():
    url = "https://produto.mercadolivre.com.br/MLB-4656717446-oculos-de-sol-masculino-quadrado-_JM"
    extractor = get_extractor_for_url(url)
    assert isinstance(extractor, MercadoLivreExtractor)

def test_router_selects_universal_for_other_sites():
    url = "https://lojaexemplo.com.br/produtos/relogio-safira"
    extractor = get_extractor_for_url(url)
    assert isinstance(extractor, UniversalWebExtractor)

def test_mercadolivre_extractor_parsing():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta property="og:title" content="Óculos De Sol Masculino Quadrado Acetato Uv400 Original - R$ 58,11" />
        <meta property="og:description" content="ÓCULOS DE SOL FINOTI – MODELO QUADRADO ESCURO COM ESTILO E PROTEÇÃO. Acompanha estojo rígido e flanela de limpeza. Armação em acetato leve." />
        <script type="application/ld+json">
        {"@type": "Product", "name": "Óculos De Sol Masculino Quadrado Acetato Uv400 Original", "offers": {"price": 58.11, "priceCurrency": "BRL"}}
        </script>
    </head>
    <body>
        <h1>Óculos De Sol Masculino Quadrado Acetato Uv400 Original</h1>
        <span class="andes-money-amount__fraction">58,11</span>
    </body>
    </html>
    """
    url = "https://produto.mercadolivre.com.br/MLB-4656717446-oculos-de-sol"
    extractor = MercadoLivreExtractor()
    target = extractor.extract(url, html)

    assert "Óculos De Sol" in target.title
    assert target.reference_price_brl == 58.11
    assert target.url == url
    assert "estojo" in target.kit_items or "estojo rígido" in target.kit_items
    assert "flanela" in target.kit_items or "flanela de limpeza" in target.kit_items
    assert "original" not in target.clean_query.lower()

def test_universal_extractor_jsonld():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Relógio Cronógrafo Aço 316L Safira - Loja Alpha</title>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": "Relógio Cronógrafo Aço 316L Safira",
            "description": "Relógio esportivo de luxo com vidro de safira e estojo incluso.",
            "offers": {
                "@type": "Offer",
                "price": 289.90,
                "priceCurrency": "BRL"
            }
        }
        </script>
    </head>
    <body></body>
    </html>
    """
    url = "https://lojaalpha.com.br/relogio"
    extractor = UniversalWebExtractor()
    target = extractor.extract(url, html)

    assert target.title == "Relógio Cronógrafo Aço 316L Safira"
    assert target.reference_price_brl == 289.90
    assert "estojo" in target.kit_items

def test_universal_extractor_opengraph_fallback():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta property="og:title" content="Fone Bluetooth Noise Cancelling Pro" />
        <meta property="og:price:amount" content="149.99" />
        <meta property="og:description" content="Fone sem fio com case de carregamento e cabo incluso." />
    </head>
    <body></body>
    </html>
    """
    url = "https://shoptech.com.br/fone"
    extractor = UniversalWebExtractor()
    target = extractor.extract(url, html)

    assert target.title == "Fone Bluetooth Noise Cancelling Pro"
    assert target.reference_price_brl == 149.99
    assert "case" in target.kit_items or "cabo" in target.kit_items
