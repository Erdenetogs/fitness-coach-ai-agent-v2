# FitCoach — AI фитнесс дасгалжуулагч агент

Капстоун дизайн 2026-2 · 4 хүний баг

Хэрэглэгчийн зорилгоор долоо хоногийн дасгалын төлөвлөгөө гаргаж, чатаар хүссэн өөрчлөлтийг **агент өөрөө хэрэгсэл дуудаж** хийдэг, хөргөгчний зургаас жор санал болгодог веб апп.

## Асаах (Windows, VS Code terminal)

```bash
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # Mac/Linux: cp .env.example .env
uvicorn app.main:app --reload
```

- Сайт: http://127.0.0.1:8000
- Тест: `pip install -r requirements-dev.txt` → `python -m unittest -v` (PR бүрт GitHub Actions автоматаар ажиллуулна)
- Сервер байршуулах: [DEPLOY.md](DEPLOY.md)
- API туршилт: http://127.0.0.1:8000/docs

`.env` дотор `ANTHROPIC_API_KEY` байхгүй бол агент **демо горим**-оор ажиллана: бодит хэрэгслүүдийг дуудаж өгөгдлийн санг өөрчилдөг ч хариуг энгийн дүрмээр гаргана. Түлхүүр тавимагц Claude жинхэнэ агент болж ажиллана.

## Бүтэц

```
app/
  main.py            Хуудас ба API route-ууд (FastAPI)
  db.py              SQLite өгөгдлийн сан (fitcoach.db файл үүснэ)
  planner.py         Анхны дасгалын төлөвлөгөө, калорийн тооцоо (дүрэмд суурилсан)
  agent/
    llm.py           Claude API холболт
    tools.py         Агентын хэрэгслүүд + "агентын алхам"-ын текст
    coach.py         Чатын агент (tool-use loop) + демо горим
    fridge.py        Зураг → орц → жор (vision + structured output)
  templates/         Jinja2 хуудсууд (base.html + 7 хуудас)
  static/css/app.css Дизайн токенууд (Figma-тай ижил)
  static/js/common.js fetch, toast, агентын алхам харуулах
```

## Агент юугаараа энгийн чатботоос ялгаатай вэ

| Шинж | Хаана |
|---|---|
| **Хэрэгсэл ашиглах** — төлөвлөгөө унших/өөрчлөх, жин бүртгэх, түүх шалгах | `agent/tools.py` |
| **Төлөвлөх ба давталт** — хэрэгслийн үр дүнг хараад дахин шийдвэр гаргана (6 хүртэл алхам) | `agent/coach.py` → `_chat_live` |
| **Санах ой** — гэмтэл, дуршлыг хадгалж дараагийн хариунд ашиглана | `save_memory`, system prompt |
| **Харагдах байдал** — дуудсан хэрэгсэл бүр чат дээр "агентын алхам" болж харагдана | `agent_steps` |

## XP ба level

Coach хэрэглэгчтэй хамт "өсдөг" (санаа: Erdenetogs-ийн Spring Boot хувилбар, `app/xp.py`).

- Өнөөдрийн дасгалыг бүгдийг дуусгах **+40 XP** · Жор хадгалах **+15 XP** · Өдрийн анхны чат **+5 XP**
- Level N → N+1: N × 100 XP. Шат: Үр (1–2), Нахиа (3–4), Тамирчин (5–7), Аварга (8+)
- Level бүрт coach-д навч нэмэгдэнэ (5 хүртэл), level 5-аас толгойн тууз гарна (`templates/_coach.html`)
- Өгөгдлийн санд (`xp_events`) хадгална — ижил үйлдлээр давхар XP авахгүй. Агент `get_user_profile`-оор level-ийг мэднэ.

## Багийн ажлын хуваарь

| Гишүүн | Гол файлууд | Branch |
|---|---|---|
| 1 — UI/UX | `templates/`, `static/css/app.css`, Figma | `frontend-ui` |
| 2 — Frontend JS | `static/js/`, хуудас бүрийн `{% block scripts %}` | `frontend-js` |
| 3 — Backend | `main.py`, `db.py`, deploy | `backend` |
| 4 — AI агент | `agent/`, `planner.py` | `ai-agent` |

API-ийн хүсэлт/хариуны хэлбэрийг [DATA.md](DATA.md)-аас харна. Хэлбэр өөрчлөх бол DATA.md-г шинэчлээд багтаа мэдэгдэнэ.
