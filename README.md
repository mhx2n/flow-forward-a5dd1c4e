# Probaho Bot

একটি প্রফেশনাল, মডুলার Telegram বট — Render Free Web Service এ ডিপ্লয়যোগ্য, MongoDB persistent backup সহ।

## ফিচার
- 🤖 Multi-AI routing (Gemini, Mistral, Perplexity)
- 🖼️ Mistral OCR (image + PDF)
- 🎙️ ElevenLabs Voice-to-Text
- 📝 Quiz generation ও accuracy fixes
- 👥 Group + Topic support, cross-chat reply
- 💾 MongoDB persistent backup (weekly Sunday 03:00 UTC)
- ❤️ Render-ready health page (`/`, `/healthz`, `/status.json`)

## লোকাল রান
```bash
pip install -r requirements.txt
python main.py
```

## Render Deploy
1. New + → **Blueprint** → এই repo সিলেক্ট
2. **Apply** ক্লিক (`render.yaml` auto-detect হবে)
3. Environment tab এ সেট করুন:
   - `BOT_TOKEN`
   - `OWNER_ID`
   - `MONGO_URI`
   - `GEMINI_API_KEY`
   - `MISTRAL_API_KEY`
   - `ELEVENLABS_API_KEY`
4. Deploy শেষ হলে URL পাবেন: `https://<your-app>.onrender.com`

## Health Endpoints
| Path | Use |
|---|---|
| `/` | Rich HTML status page |
| `/healthz` | UptimeRobot ping (2 byte) |
| `/status.json` | Programmatic JSON status |

> Render Free 15 মিনিট idle হলে sleep হয় — UptimeRobot/cron-job.org দিয়ে `/healthz` প্রতি 5 মিনিটে ping করুন।

## প্রজেক্ট স্ট্রাকচার
```
bot/
  __main__.py        # entrypoint
  config.py          # secrets/config
  sections/          # 48টি মডুলার সেকশন
main.py              # Render entry
render.yaml          # Blueprint
requirements.txt
runtime.txt          # Python 3.11.9
Procfile
```

## License
Private project — © mhx2n
