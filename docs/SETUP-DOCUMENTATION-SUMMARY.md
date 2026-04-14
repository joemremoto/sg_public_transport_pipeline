# Setup Documentation Summary

This document provides an overview of all setup documentation created for cloning and running this project on a new machine.

**Created:** 2026-03-31  
**Purpose:** Enable easy project setup on new machines (personal laptop, collaborators, etc.)

---

## Documentation Overview

### 1. **Quick Reference Documents**

| Document | Purpose | Time Required | Audience |
|----------|---------|---------------|----------|
| [`QUICKSTART.md`](QUICKSTART.md) | Fast-track setup with essential commands | 15 minutes | Experienced developers |
| [`SETUP-GUIDE.md`](SETUP-GUIDE.md) | Complete step-by-step setup instructions | 1-2 hours | All users, especially newcomers |
| [`SETUP-CHECKLIST.md`](SETUP-CHECKLIST.md) | Interactive checklist to track progress | Varies | All users (print or use as reference) |

### 2. **Configuration Templates**

| File | Location | Purpose |
|------|----------|---------|
| `.env.example` | Project root | Template for main environment variables |
| `.env.example` | `streamlit_app/` | Template for Streamlit-specific environment variables |

### 3. **Main Documentation**

| Document | Purpose |
|----------|---------|
| [`README.md`](../README.md) | Project overview, quick start, and navigation hub |
| [`architecture.md`](architecture.md) | System design and data flow |
| [`current-status.md`](current-status.md) | Project progress and phase details |

---

## Setup Workflow

```
1. Read README.md
   ↓
2. Choose path:
   - Fast: QUICKSTART.md (15 min)
   - Detailed: SETUP-GUIDE.md (1-2 hrs)
   ↓
3. Use SETUP-CHECKLIST.md to track progress
   ↓
4. Configure using .env.example templates
   ↓
5. Test each phase
   ↓
6. Success! 🎉
```

---

## What Each Document Contains

### QUICKSTART.md (15 Minutes)

**For:** Experienced developers who want to get started fast

**Contents:**
- Minimal prerequisites
- Copy-paste commands for setup
- Essential configuration only
- Quick validation steps
- Troubleshooting for common issues

**Use when:** You're familiar with GCP, Python, and data pipelines

---

### SETUP-GUIDE.md (1-2 Hours)

**For:** Anyone setting up on a new machine, especially newcomers

**Contents:**
- Detailed prerequisites with download links
- Step-by-step GCP account setup
- Complete gcloud CLI installation and configuration
- Terraform resource provisioning
- Service account creation and credential setup
- Environment variable explanation
- LTA API registration guide
- Testing procedures for each phase
- Comprehensive troubleshooting section
- Quick reference commands

**Use when:** You want complete instructions with explanations

---

### SETUP-CHECKLIST.md (Interactive Tracking)

**For:** Everyone (works alongside QUICKSTART or SETUP-GUIDE)

**Contents:**
- Interactive checkbox list
- Organized by setup stage
- Verification commands for each step
- Space for recording project-specific info (IDs, paths)
- Common issue solutions
- Final verification steps

**Use when:** You want to track progress and ensure nothing is missed

---

## .env.example Templates

### Project Root `.env.example`

**Purpose:** Main environment variables for:
- Data extraction scripts
- GCS upload scripts
- BigQuery load scripts
- dbt transformation
- Airflow (optional)

**Key variables:**
```bash
GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-service-account.json
GCP_PROJECT_ID=sg-public-transport-pipeline
LTA_ACCOUNT_KEY=YOUR_KEY_HERE
```

### Streamlit `.env.example`

**Purpose:** Streamlit-specific environment variables

**Key difference:** Uses relative path from `streamlit_app/` directory
```bash
GOOGLE_APPLICATION_CREDENTIALS=../credentials/gcp-service-account.json
```

---

## Setup Steps Summary

### 1. Prerequisites (5 min)
- Git, Python 3.10+, pip
- Google account
- GCP account with billing

### 2. Clone & Install (5 min)
```bash
git clone https://github.com/YOUR_USERNAME/sg_public_transport_pipeline.git
cd sg_public_transport_pipeline
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -e .
```

### 3. GCP Setup (15-20 min)
- Install gcloud CLI
- Create GCP project
- Enable APIs
- Run Terraform
- Create service account key

### 4. Configuration (10 min)
- Copy `.env.example` to `.env`
- Get LTA API key
- Update environment variables
- Configure dbt `profiles.yml`

### 5. Testing (10-20 min)
- Test API access
- Test data extraction
- Test GCS upload
- Test BigQuery load
- Test Streamlit dashboard

### 6. Optional: Full Pipeline Test (30-40 min)
- Extract journey data (10-15 min)
- Upload to GCS (1-2 min)
- Load to BigQuery (2-3 min)
- Run dbt transformations (3-5 min)
- View dashboard with full data

---

## Common Setup Scenarios

### Scenario 1: Moving from Work Laptop to Personal Laptop

**Situation:** You (the project creator) are moving to a new machine with a new GCP account

**Follow:**
1. Clone repo on new machine
2. Create new GCP account/project
3. Follow **QUICKSTART.md** (you're familiar with the project)
4. Copy over LTA API key (or register new one)
5. Run Terraform to recreate resources
6. Test pipeline

**Time:** ~15-30 minutes

---

### Scenario 2: New Collaborator Joining

**Situation:** Someone wants to contribute or learn from your project

**Follow:**
1. Share repo URL
2. Direct them to **README.md** first
3. Then to **SETUP-GUIDE.md** for detailed setup
4. Provide them with:
   - LTA API key (or guide to register)
   - GCP project access (if sharing project)
   - OR guide to create their own GCP project

**Time:** 1-2 hours (first time)

---

### Scenario 3: Zoomcamp Reviewer/Evaluator

**Situation:** DataTalks.Club mentor reviewing your capstone

**Follow:**
1. Share repo URL
2. Direct to **README.md** for overview
3. Provide **QUICKSTART.md** for fast evaluation
4. Include pre-populated `.env` file (without secrets)
5. OR provide your GCP project ID for read-only access

**Time:** 15-30 minutes

---

### Scenario 4: Fresh Developer (Learning)

**Situation:** Someone new to data engineering wants to learn

**Follow:**
1. Start with **README.md** for project overview
2. Use **SETUP-GUIDE.md** with detailed explanations
3. Print/use **SETUP-CHECKLIST.md** to track progress
4. Read phase-specific documentation for deep dives
5. Join Zoomcamp Slack for questions

**Time:** 2-3 hours (with learning)

---

## Critical Files for New Machine Setup

### Must Have (created during setup)
- ✅ `credentials/gcp-service-account.json` (from GCP)
- ✅ `.env` (copy from `.env.example`)
- ✅ `streamlit_app/.env` (copy from `streamlit_app/.env.example`)
- ✅ `~/.dbt/profiles.yml` (create from template in SETUP-GUIDE)

### Will Be Generated (don't worry if missing)
- `data/` directory (created when extracting data)
- `.venv/` directory (created with `python -m venv .venv`)
- `sg_transport_dbt/target/` (created when running dbt)
- `airflow/logs/` (created when running Airflow)

### Must Not Commit (already in .gitignore)
- ❌ `.env` (contains secrets)
- ❌ `credentials/` (contains GCP key)
- ❌ `data/` (too large)
- ❌ `.venv/` (environment-specific)

---

## Troubleshooting Resources

### Quick Fixes

**"Credentials not found"**
→ Check path in `.env` matches actual file location

**"Permission denied" from GCP**
→ Grant BigQuery Admin and Storage Admin roles to service account

**"LTA API returns 401"**
→ Verify API key in LTA DataMall account, update `.env`

**"Module not found"**
→ Activate virtual environment, reinstall with `pip install -e .`

**"dbt connection failed"**
→ Check `~/.dbt/profiles.yml` has absolute path to keyfile

### Detailed Help

- **SETUP-GUIDE.md:** Comprehensive troubleshooting section
- **Phase-specific docs:** `phase6-airflow-setup.md`, `phase7-streamlit-setup.md`
- **Quick references:** `QUICKREF-phase*.md` files

---

## Setup Validation

### How to Know Setup is Complete

Run this validation script:

```bash
# 1. Check virtual environment
which python  # Should show .venv path

# 2. Check credentials
ls credentials/gcp-service-account.json

# 3. Check environment variables
cat .env | grep -E "GCP_PROJECT_ID|LTA_ACCOUNT_KEY"

# 4. Check GCP resources
gcloud storage buckets list
bq ls

# 5. Test API access
python -c "from dotenv import load_dotenv; import os, requests; load_dotenv(); print('OK' if requests.get('http://datamall2.mytransport.sg/ltaodataservice/BusStops?$top=1', headers={'AccountKey': os.getenv('LTA_ACCOUNT_KEY')}).status_code == 200 else 'FAIL')"

# 6. Test dbt connection
cd sg_transport_dbt && dbt debug

# 7. Run Streamlit
cd ../streamlit_app && streamlit run app.py
```

If all steps pass, setup is complete! ✅

---

## Document Maintenance

### When to Update

Update these docs when:
- Adding new dependencies
- Changing GCP resource names
- Adding new environment variables
- Changing authentication methods
- Adding new setup steps

### What to Update

- **SETUP-GUIDE.md:** Add new steps, update commands
- **QUICKSTART.md:** Update quick command sequences
- **SETUP-CHECKLIST.md:** Add new checklist items
- **.env.example:** Add new environment variables
- **README.md:** Update quick start if major changes

---

## Additional Resources

### Phase-Specific Documentation

- **Phase 1-5:** See `phase*-*.md` files for individual phase details
- **Phase 6 (Airflow):** `phase6-airflow-setup.md`, `PHASE6-COMPLETE.md`
- **Phase 7 (Streamlit):** `phase7-streamlit-setup.md`, `PHASE7-COMPLETE.md`

### Quick References

- **Phase 4:** `QUICKREF-phase4.md` (BigQuery commands)
- **Phase 5:** `QUICKREF-phase5.md` (dbt commands)
- **Phase 6:** `QUICKREF-phase6.md` (Airflow commands)
- **Phase 7:** `QUICKREF-phase7.md` (Streamlit commands)

### Project Documentation

- **Architecture:** `architecture.md` (system design)
- **Current Status:** `current-status.md` (progress tracking)
- **Glossary:** `glossary.md` (terminology)

---

## Success Metrics

### Setup is Successful When:

- ✅ Repository cloned
- ✅ Virtual environment created and activated
- ✅ Dependencies installed
- ✅ GCP project created and configured
- ✅ Service account created with credentials
- ✅ Environment variables configured
- ✅ LTA API access working
- ✅ Reference data extracted and loaded
- ✅ dbt connection working
- ✅ Streamlit dashboard running

### Optional Success (Full Pipeline):

- ✅ Journey data extracted (at least 1 month)
- ✅ Journey data uploaded to GCS
- ✅ Journey data loaded to BigQuery
- ✅ dbt transformations completed
- ✅ Dashboard showing full data with filters
- ✅ (Optional) Airflow running in Docker

---

## Contact & Support

- **GitHub Issues:** For bugs or questions
- **Project Documentation:** `docs/` directory
- **Zoomcamp Slack:** #course-data-engineering channel
- **LTA DataMall:** https://datamall.lta.gov.sg/ (for API issues)

---

## Quick Links

| Document | Direct Link |
|----------|-------------|
| Main README | [`../README.md`](../README.md) |
| Quick Start | [`QUICKSTART.md`](QUICKSTART.md) |
| Setup Guide | [`SETUP-GUIDE.md`](SETUP-GUIDE.md) |
| Setup Checklist | [`SETUP-CHECKLIST.md`](SETUP-CHECKLIST.md) |
| Architecture | [`architecture.md`](architecture.md) |
| Current Status | [`current-status.md`](current-status.md) |

---

**Last Updated:** 2026-03-31  
**Version:** 1.0

*This documentation suite enables anyone to clone and run the Singapore Public Transport Analytics Pipeline on a new machine, from scratch, in 15 minutes to 2 hours depending on experience level.*
