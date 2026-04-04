# API Keys Setup Guide

## Quick Summary

Your project now uses **FREE APIs** with automatic fallback:
- **GROQ** (Primary) - ⚡ Fastest, $5/month free
- **GEMINI** (Fallback) - 🔄 Reliable backup, 60 req/min free

**Total Cost: $0** for hackathon/testing

---

## Setup Steps

### Step 1: Get GROQ API Key (Free)

1. Go to: https://console.groq.com
2. Sign up (no credit card needed)
3. Click "API Keys" in sidebar
4. Create new API key
5. Copy the key

**Example:**
```
gsk_AbC123XyZ...
```

---

### Step 2: Get GEMINI API Key (Free)

1. Go to: https://aistudio.google.com/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key

**Example:**
```
AIzaSyD_7...
```

---

## Deployment to HF Spaces

### When Pushing to HF Spaces

In your HF Space settings, add these two secrets:

**Secret 1:**
- Name: `GROQ_API_KEY`
- Value: `gsk_AbC123XyZ...` (your GROQ key)

**Secret 2:**
- Name: `GEMINI_API_KEY`
- Value: `AIzaSyD_7...` (your GEMINI key)

**Note:** You can add just ONE key if you only have one. The system will use whichever is available.

---

## Local Testing

### Option A: Both APIs

```bash
export GROQ_API_KEY="gsk_AbC123XyZ..."
export GEMINI_API_KEY="AIzaSyD_7..."
python inference.py
```

### Option B: GROQ Only (Recommended)

```bash
export GROQ_API_KEY="gsk_AbC123XyZ..."
python inference.py
```

### Option C: GEMINI Only

```bash
export GEMINI_API_KEY="AIzaSyD_7..."
python inference.py
```

---

## How It Works

1. **GROQ tries first** (fastest, ~50ms response)
   - If successful → uses GROQ
   - If rate limited → falls back to GEMINI
   - If failed → falls back to GEMINI

2. **GEMINI as fallback** (reliable backup)
   - Takes over if GROQ fails
   - 60 requests/minute free
   - Great for reliability

3. **Logging shows which API** is used:
   ```
   [STEP] {..., "model_used": "groq", ...}
   [END] {..., "model_used": "groq", ...}
   ```

---

## Free Tier Limits

### GROQ Free Tier
- **Rate:** ~30 requests/minute
- **Cost:** $0/month (or $5 free credits)
- **Credit card:** Not required

### GEMINI Free Tier  
- **Rate:** 60 requests/minute
- **Cost:** $0/month
- **Credit card:** Not required

### Combined
- **Total capacity:** 90 requests/minute
- **Total cost:** $0/month ✅
- **Perfect for:** Hackathon + competition

---

## Troubleshooting

### Error: "At least one API key required"
**Solution:** Set either `GROQ_API_KEY` or `GEMINI_API_KEY`

### Error: "GROQ failed..."
**Solution:** This is normal! System automatically falls back to GEMINI

### Error: "Both initialization failed"
**Solution:** 
1. Check API keys are correct
2. Install packages: `pip install groq google-generativeai`
3. Make sure environment variables are set

### GROQ is rate limited
**Solution:** Automatic! System switches to GEMINI

### GEMINI is not responding
**Solution:** Check internet connection, verify API key

---

## Monitoring

Each step logs which model was used:

```json
[STEP] {
    "action": {...},
    "reward": 0.60,
    "model_used": "groq"
}
```

This helps you see:
- ✅ Which API succeeded
- 📊 Fallback happened
- 🔄 System redundancy working

---

## Package Dependencies

Make sure these are installed:

```bash
pip install groq>=0.4.0
pip install google-generativeai>=0.3.0
```

Or all at once:
```bash
pip install -r requirements.txt
```

---

## Cost Guarantees

For your hackathon project:

| Scenario | Cost |
|----------|------|
| 100 test episodes | $0 ✅ |
| Full week testing | $0 ✅ |
| Competition run | $0 ✅ |
| Only if 1M+ tokens/month | $1-5 |

**Bottom line:** You'll stay in free tier ✅

---

## Next Steps

1. ✅ Get GROQ key from https://console.groq.com
2. ✅ Get GEMINI key from https://aistudio.google.com/apikey
3. ✅ Set environment variables
4. ✅ Test locally: `python inference.py`
5. ✅ Deploy to HF Spaces with secrets
6. ✅ Submit to OpenEnv competition

---

## Support

If you need to revert to OpenAI:
- Create a new branch
- Update `inference.py` with OpenAI client
- Or contact support

Current system is production-ready and tested ✅
