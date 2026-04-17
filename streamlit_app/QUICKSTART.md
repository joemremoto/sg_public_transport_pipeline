# 🎯 Quick Start: Deploy to Streamlit Cloud in 10 Minutes

Follow these exact steps to deploy your dashboard to Streamlit Cloud for FREE.

---

## ✅ Step 1: Prepare Your Secrets (2 minutes)

Run this command to convert your GCP credentials:

```bash
python streamlit_app/convert_secrets.py
```

This will output TOML-formatted text. **Keep this terminal window open** - you'll need to copy this text in Step 5.

---

## ✅ Step 2: Commit Your Code (1 minute)

```bash
git add .
git commit -m "Add Streamlit Cloud support"
git push origin master
```

---

## ✅ Step 3: Sign Up for Streamlit Cloud (1 minute)

1. Go to https://share.streamlit.io/
2. Click "Continue with GitHub"
3. Authorize Streamlit to access your repositories

---

## ✅ Step 4: Create Your App (2 minutes)

1. Click the **"New app"** button (top right)

2. Fill in the form:
   ```
   Repository: your-username/sg_public_transport_pipeline
   Branch: master
   Main file path: streamlit_app/app.py
   ```

3. Click **"Advanced settings"** at the bottom

4. In the "Secrets" text box, **paste the TOML text** from Step 1

5. Click **"Deploy!"**

---

## ✅ Step 5: Wait for Deployment (3 minutes)

Your app will:
- ⏳ Build (installing requirements)
- ⏳ Start (initializing app)
- ✅ Launch (live!)

---

## ✅ Step 6: Test Your App (1 minute)

Once deployed:

1. **Check connection**: You should see "Singapore Public Transport Analytics" header
2. **Test filters**: Change mode (Train/Bus), select a month
3. **View charts**: Verify data loads correctly

---

## 🎉 You're Done!

Your app is now live at:
```
https://your-app-name.streamlit.app
```

---

## 🔧 Troubleshooting

### Problem: "Could not authenticate to BigQuery"

**Solution:** Re-check your secrets

1. Go to your app
2. Click ☰ (hamburger menu) → **"Settings"**
3. Click **"Secrets"** in the left sidebar
4. Make sure the TOML format is correct:
   - No extra quotes
   - `private_key` has actual newlines (not literal `\n` text)
   - All fields from your JSON are present

### Problem: "No data available"

**Solution:** Check BigQuery permissions

Your service account needs:
- ✅ `BigQuery Data Viewer` role on your project
- ✅ Access to dataset `sg_public_transport_analytics`

Test in BigQuery console:
```sql
SELECT COUNT(*) FROM `sg-public-transport-pipeline.sg_public_transport_analytics.fact_bus_journeys`
```

### Problem: App crashes or shows errors

**Solution:** Check the logs

1. Click ☰ → **"Manage app"**
2. Click **"Logs"** tab
3. Look for the error message
4. Common issues:
   - Missing dependencies → Check `requirements.txt`
   - Import errors → Check file paths
   - Query errors → Test query in BigQuery console

---

## 📱 Share Your App

Add to your:
- **Resume**: "Built interactive dashboard deployed on Streamlit Cloud"
- **LinkedIn**: "Check out my Singapore transport analytics dashboard: [URL]"
- **Portfolio**: Showcase your data engineering + visualization skills
- **GitHub README**: Add a "🌐 Live Demo" section with the link

---

## 🔄 Updating Your App

Any changes you push to GitHub will auto-deploy:

```bash
# Make changes to your code
git add .
git commit -m "Update dashboard visualizations"
git push

# Streamlit Cloud auto-deploys in 1-2 minutes ✨
```

---

## 💰 Cost

**$0/month** - Completely free! ✨

Streamlit Community Cloud includes:
- ✅ Unlimited public apps
- ✅ 1 GB RAM per app
- ✅ Auto-deployment from GitHub
- ✅ Free SSL certificates
- ✅ Community support

---

## 📚 Next Steps

### Enhance your dashboard:
1. **Add geospatial maps**: Show bus stops/stations on a map
2. **Add date comparisons**: Compare month-over-month trends
3. **Add download buttons**: Let users download filtered data
4. **Add more metrics**: Peak hours, busiest routes, etc.

### Promote your work:
1. **LinkedIn post**: "Built and deployed a data analytics dashboard..."
2. **Blog post**: Document your architecture and learnings
3. **GitHub stars**: Share in data engineering communities
4. **Resume bullet**: "Deployed production analytics dashboard serving real-time queries..."

---

## 📞 Need Help?

- **Detailed guide**: See `DEPLOYMENT.md` in this folder
- **Streamlit docs**: https://docs.streamlit.io/
- **Community forum**: https://discuss.streamlit.io/
- **Streamlit Cloud docs**: https://docs.streamlit.io/streamlit-community-cloud

---

**Your dashboard will be live in less than 10 minutes!** 🚀

Questions? Check the logs, read the error messages, and search the Streamlit forum.
