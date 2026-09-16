// @ts-check
// `@type` JSDoc annotations allow editor autocompletion and type checking

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'AliExpress & Alibaba Finder',
  tagline: 'Mineração de Produtos, Inteligência de Concorrência e Calculadora Tributária Brasileira (B2C & B2B)',
  favicon: 'img/favicon.ico',

  url: 'https://iuryalmeidadev.github.io',
  baseUrl: '/',

  organizationName: 'IuryAlmeidaDev',
  projectName: 'aliexpress-finder',

  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  markdown: {
    mermaid: true,
  },
  themes: ['@docusaurus/theme-mermaid'],

  i18n: {
    defaultLocale: 'pt-BR',
    locales: ['pt-BR'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          routeBasePath: '/',
          sidebarPath: './sidebars.js',
          editUrl: 'https://github.com/IuryAlmeidaDev/aliexpress-finder/tree/master/docs/',
          exclude: ['superpowers/**'],
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: 'img/social-card.jpg',
      colorMode: {
        defaultMode: 'dark',
        respectPrefersColorScheme: true,
      },
      navbar: {
        title: 'AliExpress & Alibaba Finder',
        logo: {
          alt: 'AliExpress Finder Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Documentação',
          },
          {
            href: 'https://github.com/IuryAlmeidaDev/aliexpress-finder',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Módulos Principais',
            items: [
              {
                label: 'Visão Geral',
                to: '/',
              },
              {
                label: 'AliExpress B2C & Choice',
                to: '/mineracao-aliexpress',
              },
              {
                label: 'Alibaba B2B & Atacado',
                to: '/atacado-alibaba',
              },
              {
                label: 'Inteligência de Concorrência',
                to: '/inteligencia-concorrencia',
              },
            ],
          },
          {
            title: 'Fiscal & Estratégia',
            items: [
              {
                label: 'Motor Tributário Brasileiro',
                to: '/motor-tributario-financeiro',
              },
              {
                label: 'Radar Mercado Livre',
                to: '/radar-mercado-livre',
              },
              {
                label: 'Guia de Comandos CLI',
                to: '/guia-cli-comandos',
              },
            ],
          },
          {
            title: 'Comunidade & Código',
            items: [
              {
                label: 'GitHub do Projeto',
                href: 'https://github.com/IuryAlmeidaDev/aliexpress-finder',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} AliExpress & Alibaba Finder. Construído com Docusaurus.`,
      },
      prism: {
        theme: require('prism-react-renderer').themes.github,
        darkTheme: require('prism-react-renderer').themes.dracula,
        additionalLanguages: ['bash', 'python', 'json'],
      },
    }),
};

module.exports = config;
