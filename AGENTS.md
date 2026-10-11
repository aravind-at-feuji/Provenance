# Provenance AI Agent Guidelines & Rules

## 🚫 MANDATORY RULE: ZERO DUMMY / MOCK DATA POLICY
**Must and Should Follow Rule for All AI Coding Agents:**

1. **NO DUMMY / MOCK / FAKE DATA**:
   - Under no circumstances should the codebase contain hardcoded dummy records, mock entity arrays, fake fallback topologies, fabricated metrics, or placeholder datasets in runtime application code or frontend UI.
   - Never use mock arrays as "offline fallbacks" or "disconnected fallbacks".

2. **ALL DATA MUST BE FETCHED VIA LIVE API OR USER INPUT**:
   - Every metric, table, card, chart, graph node, relationship, citation, alert, and entity displayed in the UI must come from a live backend API call or explicit user input.
   - If a backend service returns empty data, render an authentic empty state (e.g., *"No items found. Click 'Add' or upload documents to get started."*).
   - When loading, use genuine loading skeletons or spinners.

3. **TRUTHFUL ERROR HANDLING**:
   - If an API request fails or is unreachable, the application must present a clear, truthful error message or retry alert banner.
   - Never silently swallow errors and substitute fake records to make the UI look populated.

4. **DYNAMIC COMPUTED METRICS**:
   - Dashboard KPIs, percentages, counts, and spend numbers must be computed dynamically from actual API responses and live database records, never hardcoded static literals.

## 🚫 MANDATORY RULE: NO "9 REGULATORY FEEDS LIVE" OR FEED/SOURCE COUNT BADGES IN UI
**Must and Should Follow Rule for All AI Coding Agents:**

1. **PROHIBITION OF LIVE FEED / SOURCE COUNT BADGES IN ALL PAGES**:
   - Under no circumstances should the codebase contain badges, pills, or status chips such as `"9 REGULATORY FEEDS LIVE"`, `"9 Sources Active"`, `"LIVE REGULATORY INGESTION ACTIVE"`, `"SYSTEM OPERATIONAL · 9 FEEDS SYNCHRONIZED"`, `"9 Live Feeds"`, or any artificial feed/source count badges anywhere in the UI.
   - This rule applies across **ALL** pages throughout the entire application: landing page, app shell headers, navigation bars, sidebars, dashboard overviews, footers, modals, preview cards, and widgets.
   - Never place promotional or pulsing status badges (e.g. green ping dots with active feed counts) indicating the number of live regulatory feeds or ingestion sources.

2. **CLEAN HEADERS, NAVIGATION & FOOTERS**:
   - Keep headers, navigation bars, and footers uncluttered, professional, and free from artificial live-feed indicators or pulsing count chips.
   - Headers should display clean platform typography and functional elements (e.g., persona switcher, user profile) without fake status counters.

---

For design, antislop, and simplicity guidelines, refer to:
- `.agents/rules/antislop.md`
- `.agents/rules/ponytail.md`
- `.agents/skills/antislop/SKILL.md`
