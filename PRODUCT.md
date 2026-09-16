# Radar de Marcas Brasil
<!-- impeccable:product-schema 1 -->

## Platform
web

## Stack
Delegated by the user: React and Vite frontend; Python API alongside the existing collector on Oracle VPS. XLSX reports are the integration boundary.

## Users
Iury researches Brazilian product demand and private-label opportunities. He wants automatic discovery and visual analysis without opening spreadsheets.

## Product Purpose
Explore best sellers, demand evidence and brand potential over time. Compare observations, not foreign supplier prices. Brand potential is a hypothesis, not proof of importation or an investment recommendation.

## Operating Context
Manual and weekly Mercado Livre collection produces XLSX files on the VPS. The dashboard reads completed reports automatically and accepts compatible manual uploads.

## Constraints
Missing reviews, prices, URLs and history must remain missing. Partial collection coverage must be visible. Do not fabricate historical points or growth. Keep OAuth credentials exclusively on the server. Existing unrelated Monvix services must keep running.

## Evidence on Hand
Real report with 100 products, no priorities, demand coverage 40%. Four workbook sheets: Oportunidades, Investigar, Evidências, Execução. Existing logo assets/mercado-livre-radar-logo.png.

## Decisions delegated for this implementation
Portuguese dashboard, desktop and mobile, private access, automatic refresh, product detail and filters. User explicitly requests implementation without additional questions and will validate afterwards.
