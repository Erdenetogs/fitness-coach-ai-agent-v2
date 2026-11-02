# Сервер байршуулах (Render.com, үнэгүй)

Багш болон туршигчид линкээр шууд нээх боломжтой болгоно. Хариуцагч: **3-р гишүүн (Backend)**.

## Одоогийн байдал
✅ **https://fitcoach-nl0o.onrender.com** дээр ажиллаж байна (11/2). Render-ийн *Public Git Repository* аргаар холбосон тул `main` шинэчлэгдэхэд **автоматаар шинэчлэгдэхгүй** → Render dashboard → `fitcoach` → **Manual Deploy → Deploy latest commit**.

Env: `ANTHROPIC_API_KEY`, `CLAUDE_MODEL=claude-haiku-5-5`, `PYTHON_VERSION=3.12.7`. Илтгэлийн өмнө `CLAUDE_MODEL`-ийг `claude-sonnet-5-5` болгож болно.

## 1. Нэг удаагийн тохиргоо (Blueprint арга — repo эзэмшигч Render-д эрх өгсөн үед)
1. **render.com** → GitHub-аараа бүртгүүлнэ
2. **New → Blueprint** → `Erdenetogs/fitness-coach-ai-agent-v2` сонгоно
   (repo харагдахгүй бол Erdenetogs Render-д repo-д хандах эрх өгнө)
3. Render `render.yaml`-ийг уншаад `fitcoach` сервис үүсгэнэ → **Apply**
4. `ANTHROPIC_API_KEY` асуувал түлхүүрээ оруулна (байхгүй бол хоосон орхиход демо горимоор ажиллана)

**Шалгах:** 3–5 минутын дараа `https://fitcoach-xxxx.onrender.com` линк гарна. Нээхэд бүртгэлийн хуудас харагдана.

## 2. Дараа нь
`main` руу merge хийх бүрт Render автоматаар дахин байршуулна.

## Анхаарах
- **Үнэгүй сервер 15 минут ашиглаагүй бол унтана.** Дараагийн нээлт ~50 секунд удаан ачаална. Илтгэлийн өмнө линкийг нэг удаа нээж "сэрээгээрэй".
- **Өгөгдөл хадгалагдахгүй.** Үнэгүй сервер дахин асах бүрт `fitcoach.db` устана (бүртгэл, XP шинээр эхэлнэ). Демо хийхэд хангалттай. Байнга хадгалах шаардлагатай бол Render-ийн Disk ($) эсвэл PostgreSQL нэмнэ.
- API түлхүүрийг **зөвхөн Render-ийн Environment** хэсэгт бичнэ. Код, GitHub руу хэзээ ч бүү оруул.
