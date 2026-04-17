# 🚀 Deploying to Streamlit Cloud

This guide walks you through deploying the Singapore Public Transport Analytics dashboard to Streamlit Cloud (FREE).

## Prerequisites

- GitHub account
- Your repository must be pushed to GitHub
- GCP service account JSON file with BigQuery access

---

## Step 1: Prepare Your Repository

### 1.1 Make sure sensitive files are ignored

Check that your `.gitignore` includes:
```
*.json
.env
.streamlit/secrets.toml
credentials/
```

### 1.2 Commit and push your code

```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin master
```

---

## Step 2: Sign Up for Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Click "Sign up" or "Sign in with GitHub"
3. Authorize Streamlit to access your GitHub repositories

---

## Step 3: Create New App

1. Click "New app" button
2. Fill in the form:
   - **Repository**: Select `your-username/sg_public_transport_pipeline`
   - **Branch**: `master` (or `main`)
   - **Main file path**: `streamlit_app/app.py`
   - **App URL** (optional): Choose a custom subdomain

3. Click "Advanced settings" (⚙️ icon)

---

## Step 4: Add Secrets (GCP Credentials)

### 4.1 Get your service account JSON

Open your GCP service account JSON file:
```
credentials/gcp-service-account.json
```

### 4.2 Format for Streamlit Secrets

In the "Secrets" section of Advanced settings, paste:

```toml
[gcp_service_account]
type = "service_account"
project_id = "sg-public-transport-pipeline"
private_key_id = "your-private-key-id-here"
private_key = "-----BEGIN PRIVATE KEY-----\nYour\nPrivate\nKey\nHere\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@sg-public-transport-pipeline.iam.gserviceaccount.com"
client_id = "your-client-id-here"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40sg-public-transport-pipeline.iam.gserviceaccount.com"
```

**Important:**
- Copy values from your actual service account JSON
- Keep the `private_key` value with `\n` for newlines (don't replace them)
- Wrap the entire private key in quotes

### 4.3 Quick way to convert JSON to TOML

You can use this Python script to convert:

```python
import json

# Read your service account JSON
with open('credentials/gcp-service-account.json') as f:
    sa = json.load(f)

# Print in TOML format
print("[gcp_service_account]")
for key, value in sa.items():
    if isinstance(value, str) and '\n' in value:
        # Handle multiline strings (like private_key)
        print(f'{key} = """{value}"""')
    else:
        print(f'{key} = "{value}"')
```

---

## Step 5: Deploy!

1. Click "Deploy!" button
2. Wait 2-3 minutes for deployment
3. Your app will be live at: `https://your-app-name.streamlit.app`

---

## Step 6: Verify It Works

1. Visit your app URL
2. Check that:
   - ✅ No credential errors
   - ✅ Data loads from BigQuery
   - ✅ Filters work correctly
   - ✅ Charts display properly

---

## Troubleshooting

### Error: "Could not authenticate to BigQuery"

**Solution:** Check your secrets formatting
- Make sure `private_key` has `\n` characters preserved
- Verify all fields from your service account JSON are present
- Check for typos in the TOML syntax

### Error: "No data available"

**Solution:** Verify BigQuery permissions
- Service account needs `BigQuery Data Viewer` role
- Check that your dataset `sg_public_transport_analytics` exists
- Run test query in BigQuery console with that service account

### App is slow

**Solution:** Already optimized with caching!
- All queries cached for 1 hour (`@st.cache_data(ttl=3600)`)
- First load may be slow, subsequent loads are instant
- Consider adding more specific date ranges

---

## Updating Your App

After deploying, any push to your GitHub repository will automatically redeploy:

```bash
# Make changes
git add .
git commit -m "Update dashboard"
git push

# Streamlit Cloud auto-deploys in 1-2 minutes
```

---

## Managing Your App

### Reboot app
```
Settings → Reboot app
```

### View logs
```
☰ Menu → Manage app → Logs
```

### Update secrets
```
Settings → Secrets → Edit
```

### Delete app
```
Settings → Delete app
```

---

## Cost

**Streamlit Cloud Community:** FREE ✨
- Unlimited public apps
- 1 GB RAM per app
- Shared resources
- Community support

**Limitations:**
- App must be in public GitHub repo
- May sleep after 7 days of inactivity
- Limited to 3 apps on free tier

---

## Next Steps

### Make it better:
1. Add more visualizations
2. Add geospatial maps (use `pydeck` or `folium`)
3. Add download buttons for data
4. Add comparison views (month-over-month)

### Share it:
- Add URL to your resume
- Share on LinkedIn
- Include in portfolio

---

## Support

- **Streamlit Docs:** https://docs.streamlit.io/
- **Streamlit Forum:** https://discuss.streamlit.io/
- **This project:** Check the main README.md

---

**Your app will be live at:**
`https://your-app-name.streamlit.app` 🎉
