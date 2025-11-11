# Vercel Configuration Rules

> **Critical context for preventing deployment failures**

## ⚠️ MUST NOT

1. **Never use legacy `routes` key in `vercel.json`**
   ```json
   // ❌ WRONG - causes "mixed routing" error
   { "routes": [...] }
   
   // ✅ CORRECT - use modern keys
   { "rewrites": [...] }
   ```

2. **Never use floating Node versions in `package.json`**
   ```json
   // ❌ WRONG - causes auto-upgrades
   "engines": { "node": ">=22" }
   "engines": { "node": "^22" }
   
   // ✅ CORRECT - pinned LTS
   "engines": { "node": "22.x" }
   ```

3. **Never use @vercel/node v4 or lower**
   ```json
   // ❌ WRONG - doesn't support Node 22
   "@vercel/node": "^3.0.0"
   "@vercel/node": "^4.0.0"
   
   // ✅ CORRECT - supports Node 22
   "@vercel/node": "^5.5.5"
   ```

## ✅ MUST DO

Before every deploy:
```bash
npm run validate  # Runs all 5 critical checks
```

## 📋 Validation Scripts

- `validate:json` — Ensures valid JSON (no comments/trailing commas)
- `validate:vercel` — Blocks legacy `routes` key
- `validate:node` — Enforces pinned Node versions
- `validate:packages` — Blocks problematic @vercel/* versions
- `validate:build` — Verifies output directory exists

## 🔒 Automated Guards

- **Pre-commit**: `npm run precommit` (validates config changes)
- **CI/CD**: `.github/workflows/validate.yml` (blocks invalid merges)
- **Deploy**: `npm run deploy` (runs validation automatically)

---

**Current Config** (verified clean):
- ✅ Node: `22.x` (pinned LTS, required by Vercel)
- ✅ @vercel/node: `^5.5.5` (Node 22 compatible)
- ✅ @vercel/static-build: `^2.8.5` (Node 22 compatible)
- ✅ Routing: Modern `rewrites` only (no legacy `routes`)

