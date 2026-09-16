// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    {
      type: 'category',
      label: '🚀 Começando',
      collapsed: false,
      items: [
        'intro',
        'instalacao-e-configuracao',
      ],
    },
    {
      type: 'category',
      label: '🔎 Prospecção & Mineração',
      collapsed: false,
      items: [
        'mineracao-aliexpress',
        'atacado-alibaba',
        'radar-mercado-livre',
      ],
    },
    {
      type: 'category',
      label: '⚔️ Inteligência & Benchmarking',
      collapsed: false,
      items: [
        'inteligencia-concorrencia',
      ],
    },
    {
      type: 'category',
      label: '💰 Gestão Financeira & Fiscal',
      collapsed: false,
      items: [
        'motor-tributario-financeiro',
      ],
    },
    {
      type: 'category',
      label: '💻 Referência da Ferramenta',
      collapsed: false,
      items: [
        'guia-cli-comandos',
      ],
    },
  ],
};

module.exports = sidebars;
