# Development Roadmap

## ✅ Completed

- CustomerProfile + Address models, forms, views, tests
- Payment provider refactor: extracted `orders/payments/` → dedicated
  `payments` app
- All checks green: `mypy .`, `ruff check .`, `pytest`

## 🔧 Phase 1 — Unit Tests (per app)

Go through each app and ensure tests are water-tight:

1. **accounts** — models, views, signals, address logic
2. **products** — models, managers, selectors, views
3. **cart** — services, context processors, views
4. **orders** — services, signing, tracking, views
5. **payments** — provider base, PayPal provider, service loader
6. **core** — middleware, views, sitemaps

## 🔗 Phase 2 — Cross-App Integration Tests

Verify contracts between apps hold under real conditions:

- Cart → Orders (stock reservation, race conditions)
- Orders → Payments (provider creation, capture, failure handling)
- Orders → Tracking (paid-only creation, status transitions)
- Accounts → Orders (user orders, guest orders, signed links)

## 🧪 Phase 3 — E2E Tests

Full user flows with Playwright/browser:

- Auth flow (signup → verify → login → logout)
- Shop + checkout flow (browse → cart → pay → confirmation)
- Guest checkout flow (email → pay → signed receipt link)
- Account management (addresses, settings, danger zone)
- UI + accessibility checks

## 🐳 Phase 4 — Docker + Nginx

- Dockerfile (multi-stage: deps → static build → runtime)
- docker-compose (Django + Postgres + Nginx)
- Nginx config (static serving, reverse proxy, headers)
- CI pipeline update (run tests inside container)

## 🎨 Phase 5 — Final Polish

- Template styling pass (consistency, responsive, dark edges)
- Error pages (400, 403, 404, 500)
- Loading states, empty states, toast messages
- Lighthouse audit (performance, a11y, SEO)
- README update with setup instructions