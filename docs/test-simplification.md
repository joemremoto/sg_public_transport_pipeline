# Test Simplification Summary

**Date:** 2026-03-30  
**Decision:** Option 1 - Keep only critical tests

---

## What Was Removed

### Staging Layer (removed ~40 tests)
- ❌ Range checks on lat/lon
- ❌ Not null checks on obvious fields
- ❌ Accepted values checks (WEEKDAY/WEEKEND)
- ❌ Range checks on hour (0-23)
- ❌ Relationship tests to reference data

**Rationale:** LTA API provides clean, validated data. These tests add runtime without catching real bugs.

### Dimension Layer (removed ~30 tests)
- ❌ Range checks on date components (month 1-12, day 1-31)
- ❌ Accepted values on time period categories
- ❌ Not null checks on descriptive fields

**Rationale:** Generated dimensions (date, time) are deterministic. Reference dimensions come from clean staging.

### Fact Layer (removed ~20 tests)
- ❌ Accepted values on day_type
- ❌ Range checks on trip_count (> 1)
- ❌ Not null on degenerate dimensions

**Rationale:** Already filtered in staging. These are duplicate validations.

---

## What Was Kept (Essential Tests Only)

### Staging Layer (4 tests)
✅ `stg_bus_stops.bus_stop_code` - unique, not_null  
✅ `stg_train_stations.station_code` - unique, not_null

**Why:** Ensures no duplicate reference data keys.

### Dimension Layer (8 tests)
✅ All surrogate keys (`bus_stop_key`, `station_key`, `date_key`, `time_period_key`)
  - unique
  - not_null

✅ All natural keys (`bus_stop_code`, `station_code`)
  - unique
  - not_null

**Why:** Primary key integrity is critical for joins.

### Fact Layer (12 tests) - **MOST IMPORTANT**
✅ Both fact tables:
  - Primary key (unique, not_null)
  - **4 relationship tests per fact table** (origin FK, destination FK, date FK, time FK)

**Why:** These catch the most common bugs:
- Orphaned fact records (failed joins)
- Missing dimension data
- Invalid foreign keys

---

## Impact Summary

**Before:**
- ~100+ tests
- Test runtime: ~60 seconds
- Verbose output

**After:**
- ~24 tests
- Test runtime: ~15 seconds (estimated)
- Focused on join integrity

---

## Test Coverage Now

```
Raw Data (LTA API)
    ↓ [trusted clean]
Staging (4 tests)
    ↓ [key uniqueness verified]
Dimensions (8 tests)
    ↓ [all PKs validated]
Facts (12 tests)
    ↓ [referential integrity enforced]
Analytics Ready ✅
```

---

## Commands

```powershell
cd sg_transport_dbt

# Run all models
uv run dbt run

# Run essential tests only (much faster now!)
uv run dbt test

# Expected output:
# - 10 models built successfully
# - 24 tests passed
```

---

## If You Need to Add Tests Later

You can always add specific tests back if you encounter issues:

```yaml
# Example: Add back a relationship test to staging
- name: origin_bus_stop_code
  tests:
    - relationships:
        to: ref('stg_bus_stops')
        field: bus_stop_code
```

But start minimal - add only when debugging specific issues.

---

**Philosophy:** Test what can break, not what's already guaranteed by upstream processes.
