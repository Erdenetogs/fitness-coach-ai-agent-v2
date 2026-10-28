# API гэрээ (Frontend ↔ Backend)

Бүх API нь `fitcoach_token` cookie-оор хэрэглэгчийг таньдаг (onboarding бөглөхөд тавигдана). Cookie-д хэрэглэгчийн id биш, санамсаргүй token хадгалагдана. Cookie байхгүй эсвэл буруу бол `401 {"error": "..."}`.
Алдааны үед бүх API `{"error": "Монгол тайлбар"}` буцаана.

## Агентын алхам (`agent_steps`)
```json
[{"icon": "edit_calendar", "text": "Бямба гарагийн дасгалыг өөрчилсөн"}]
```
`icon` нь [Material Symbols](https://fonts.google.com/icons) нэр.

## POST /api/chat
Хүсэлт: `{"message": "Өвдөг өвдөж байна"}`
Хариу:
```json
{"reply": "…", "agent_steps": [...], "plan_changed": true}
```

## POST /api/fridge  (multipart/form-data)
Талбар: `photo` (jpg/png/webp, ≤5MB) ба/эсвэл `ingredients` ("өндөг, тахиа")
Хариу:
```json
{
  "ingredients": ["Өндөг", "Тахиа"],
  "recipes": [{"title": "", "kcal": 420, "protein_g": 38, "time_min": 20,
               "uses": [], "extra": [], "steps": [], "why": ""}],
  "agent_steps": [...], "target": {"kcal": 1990, "protein_g": 99, "tdee": 2390},
  "demo": false
}
```

## POST /api/recipes
`{"recipe": {...дээрх recipe объект}}` → `{"ok": true}`

## POST /api/workout/done
`{"exercise": "Суулт (squat)", "done": true}` → `{"ok": true, "done_today": ["..."]}`

## POST /api/weight
`{"kg": 61.4}` → `{"ok": true, "weights": [{"day": "2026-10-24", "kg": 61.4}]}`

## GET /api/progress
`{"weights": [...], "history": [{"day": "2026-10-24", "done_count": 3, "exercises": "..."}]}`

## DELETE /api/memory/{id}
→ `{"ok": true}`

## XP (`xp`)
`/api/chat`, `/api/recipes`, `/api/workout/done` хариунд `xp` талбар нэмэгдэнэ. XP өгөөгүй бол `null`.
```json
{"gained": 40, "reason": "өнөөдрийн дасгал дууслаа", "leveled_up": false,
 "level": 2, "xp": 15, "need": 200, "total": 115, "stage": "Үр", "pct": 8, "streak": 3}
```

## GET /api/xp
Дээрхтэй ижил, `gained/reason/leveled_up`-гүй.

## GET /api/status
`{"ai_live": true, "model": "claude-sonnet-5-5"}`

## Төлөвлөгөөний бүтэц (`plans.plan_json`)
```json
{"Даваа": {"focus": "upper", "title": "Дээд бие",
           "exercises": [{"name": "Түлхэлт", "icon": "fitness_center", "sets": 3, "reps": 12}]},
 "Ням":   {"focus": "rest", "title": "Амрах өдөр", "exercises": []}}
```
Кардио дасгал `sets/reps`-ийн оронд `duration_min`-тэй.
