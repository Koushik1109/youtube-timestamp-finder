# 🚀 QUICK START GUIDE

## ⚡ Fastest Way to Get Running (3 Steps)

### Step 1: Install Everything
```bash
# Install Python packages
pip install -r requirements.txt

# Install ffmpeg
# Ubuntu: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg
```

### Step 2: Set API Key
```bash
# Get free API key from: https://aistudio.google.com/app/apikey
export GOOGLE_API_KEY="your_api_key_here"
```

### Step 3: Run
```bash
python main.py
```

That's it! Server runs on http://localhost:8000

---

## 🧪 Test Your Setup

```bash
# Run the test script
python test_setup.py
```

Or use the auto-start script:
```bash
./start.sh
```

---

## 📡 Test the API

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://youtu.be/dQw4w9WgXcQ",
    "topic": "introduction"
  }'
```

Expected response:
```json
{
  "timestamp": "00:00:15",
  "video_url": "https://youtu.be/dQw4w9WgXcQ",
  "topic": "introduction"
}
```

---

## 🌐 Deploy Online (Choose ONE)

### Option A: ngrok (Easiest for Testing)
```bash
# Terminal 1
python main.py

# Terminal 2
ngrok http 8000
# Copy the https URL and submit it
```

### Option B: Render.com (Free, Permanent)
1. Sign up: https://render.com
2. New Web Service → Connect GitHub
3. Build: `pip install -r requirements.txt && apt-get update && apt-get install -y ffmpeg`
4. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add env var: `GOOGLE_API_KEY`

### Option C: Railway.app (Simplest)
1. Sign up: https://railway.app
2. New Project → Deploy from GitHub
3. Add env var: `GOOGLE_API_KEY`
4. Auto-deploys!

---

## 🐛 Troubleshooting

**API key error?**
```bash
echo $GOOGLE_API_KEY  # Should show your key
export GOOGLE_API_KEY="your_key"
```

**ffmpeg not found?**
```bash
ffmpeg -version  # Should show version
# If not, install ffmpeg first
```

**Dependencies error?**
```bash
pip install -r requirements.txt
```

---

## 📁 Project Structure

```
youtube-timestamp-finder/
├── main.py              # Main FastAPI application ⭐
├── requirements.txt     # Python dependencies
├── README.md           # Full documentation
├── QUICKSTART.md       # This file
├── test_setup.py       # Setup verification script
├── start.sh            # Auto-start script
├── Dockerfile          # For Docker deployment
├── .env.example        # Environment variable template
└── .gitignore         # Git ignore rules
```

---

## 🎯 What You Need to Submit

1. Deploy your server (ngrok or Render or Railway)
2. Get your server URL (e.g., `https://abc-123.ngrok-free.app`)
3. Submit ONLY the base URL (without `/ask`)
4. Validator will call `POST /ask` automatically

**Example:**
- Your server: `https://abc-123.ngrok-free.app`
- Submit: `https://abc-123.ngrok-free.app`
- Validator tests: `https://abc-123.ngrok-free.app/ask`

---

## 💡 Pro Tips

1. **Use ngrok for quick testing** - It's free and instant
2. **Keep ngrok terminal open** - URL expires when closed
3. **Test locally first** - Make sure everything works
4. **Check logs** - `python main.py` shows all details
5. **Gemini 2.0 Flash is best** - Optimized for audio

---

## ⏱️ Expected Processing Time

- Short video (< 5 min): ~10-15 seconds
- Medium video (5-30 min): ~20-40 seconds  
- Long video (30+ min): ~40-90 seconds

---

## 🆘 Still Stuck?

Run diagnostics:
```bash
python test_setup.py
```

Check each step is ✅ green. If any are ❌ red, fix those first.

---

## 📚 Full Documentation

For complete details, see: [README.md](README.md)

---

Good luck! 🎉
