# Radar web

User delegated implementation and design decisions, with validation after delivery.

React/Vite/Recharts and shadcn controls. Python FastAPI serves the built app at /radar/ on api.monvix.me and reads XLSX reports in reports/ (excluding smoke). Automatically pick up newly completed reports, poll every minute, allow bounded manual upload and deduplicate by run ID. No changes to collector required. Raw OAuth credentials never enter API responses.

Authenticated private surface, session cookie issued from a separately generated dashboard access key. Import requires same-origin and authenticated session. Upload limits on compressed and expanded sizes. Reject malformed schema, invalid dates, IDs and score ranges. Atomic import, server-defined paths. Run details include collection coverage and missing data. No invented historical values.

Viewport: overview heading, compact summary rail, demand/brand scatterplot as principal workspace, category comparison, time series and searchable product table; detail drawer exposes evidence and product history. History uses actual run timestamps; a single run shows one observation and explanatory copy. Dense desktop layout stacks on mobile. Readable Portuguese labels and keyboard controls.

Visual direction candidates: market terminal, product catalog, research journal, market research notebook, supply chain atlas, commercial report, showroom. Assigned index 4: market research notebook. Off-white paper, forest ink, broad chart area, thin rules. Challengers declined: coded catalog sacrifices readable names; bureau prospectus overweights decoration; origami sequential ritual is inappropriate for filtering; iridescence lacks persistent states; one-bit sacrifices accessible chart series. Retained disciplines: chart ownership, precise spacing, recoverable controls, explicit uncertainty, dense keyboard-friendly tables.

Validation: parser/auth/import tests; production build; desktop/mobile browser review with real workbook; deploy isolated service behind existing proxy; verify existing services and new route.
