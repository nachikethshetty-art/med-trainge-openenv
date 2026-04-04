# 🚀 HF SPACES DEPLOYMENT - QUICK START

## ⚠️ The Problem You're Seeing

**Error:** "No application file"

**Reason:** HF Spaces can't find `app_server.py` at the root level (it was nested in uploaded ZIP)

**Solution:** Delete everything from your HF Space and upload the correct files

---

## 📋 Files to Upload (CRITICAL ORDER)

Upload these files to your HF Space at the **ROOT level** (not in a subfolder):

### 1. **Configuration Files** (Upload FIRST)
- ✅ `README.md` ← Use SPACES_README.md content
- ✅ `Dockerfile` ← NEW - created for you
- ✅ `requirements.txt` ← UPDATED - added Flask, GROQ, GEMINI

### 2. **Application Files** (Upload SECOND)
- ✅ `app_server.py` ← NEW - Flask web server on port 7860
- ✅ `openenv.yaml` ← Environment spec
- ✅ `environment/` (folder with files inside)
- ✅ `baseline/` (folder with files inside)

### 3. **Optional Files** (Upload if you want)
- ⭕ `tasks/` (folder)
- ⭕ `tests/` (folder)
- ⭕ `api/` (folder)

---

## 🎯 Step-by-Step Instructions

### Step 1: CLEAR Your HF Space (if it has old files)

1. Go to: https://huggingface.co/spaces/nachikethshetty/med-trainge-openenv
2. Click **"Settings"** ⚙️ (top right)
3. Click **"Delete this space"** at the bottom (WARNING: deletes everything!)
4. Click **"Delete"** to confirm
5. Wait 30 seconds
6. Create a NEW space with the SAME name:
   - Click **"Create new space"**
   - Name: `med-trainge-openenv`
   - License: `openrail`
   - SDK: **`Docker`** ← IMPORTANT!
   - Click **"Create space"**

### Step 2: Upload Files to NEW Space

1. Go to new space: https://huggingface.co/spaces/nachikethshetty/med-trainge-openenv
2. Click **"Files"** tab
3. Click **"+"** button (top right corner)
4. Click **"Upload files"**
5. Select these files from `/Users/amshumathshetty/Desktop/med-triage-openenv/`:
   - `README.md` (or rename SPACES_README.md to README.md first)
   - `Dockerfile`
   - `requirements.txt`
   - `app_server.py`
   - `openenv.yaml`
   - Entire `environment/` folder
   - Entire `baseline/` folder

6. Click **"Upload"**
7. Wait for upload to complete ✓

### Step 3: Add API Key Secrets

1. Click **"Settings"** ⚙️
2. Click **"Secrets and tokens"** on left sidebar
3. Click **"New secret"**
4. Add first secret:
   - Name: `GROQ_API_KEY`
   - Value: (Your GROQ API key from https://console.groq.com)
   - Click **"Save"**

5. Click **"New secret"** again
6. Add second secret:
   - Name: `GEMINI_API_KEY`
   - Value: (Your Google Gemini API key from https://aistudio.google.com/apikey)
   - Click **"Save"**

**Note:** Both APIs have free tiers, so you won't be charged!

### Step 4: Watch the Build

1. Click **"Logs"** tab
2. Wait 10-15 minutes for Docker build to complete
3. You'll see: `✓ Build finished`
4. Then it will say: `Running... on port 7860`

### Step 5: Access Your App

1. Click **"App"** tab
2. You should see your web UI with test buttons!
3. Click **"🟢 Easy Task"** to test
4. Watch the agent triage a support ticket 🎉

---

## 📁 File Structure (at HF Space root)

After uploading, your HF Space should look like:

```
README.md                    ← Space description
Dockerfile                   ← HF Spaces will use this to build container
requirements.txt             ← Dependencies
app_server.py                ← Flask app on port 7860 (HF Spaces runs this)
openenv.yaml                 ← Environment config
environment/
  ├── __init__.py
  └── med_triage_env.py
baseline/
  ├── __init__.py
  └── agent.py
```

---

## 🔧 Troubleshooting

### Issue: "Configuration error" or "No application file"
**Solution:** Make sure `app_server.py` and `Dockerfile` are at the ROOT level, not nested

### Issue: Build fails with dependency errors
**Solution:** Make sure `requirements.txt` has all packages (Flask, pydantic, groq, google-generativeai)

### Issue: App shows but has no API access
**Solution:** Go to Settings → Secrets and add `GROQ_API_KEY` and `GEMINI_API_KEY`

### Issue: "Port 7860 not responding"
**Solution:** Check Logs tab - look for errors in Flask startup

---

## 🎯 Quick Copy-Paste Commands

If you want to use git instead:

```bash
cd /Users/amshumathshetty/Desktop/med-triage-openenv

# Add HF Space as remote
git remote add hf https://huggingface.co/spaces/nachikethshetty/med-trainge-openenv

# Push to HF Space
git push hf main
```

---

## ✅ When You're Done

Your app will:
- 🟢 Show "Ready" status
- 🟡 Display GROQ/GEMINI status
- 🔴 Have working test buttons
- 📊 Show episode results and scores
- ⚡ Use free APIs (no costs!)

Enjoy! 🎉
