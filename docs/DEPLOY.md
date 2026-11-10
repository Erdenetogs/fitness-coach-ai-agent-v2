# Сервер байршуулах (Render.com, үнэгүй)

Багш болон туршигчид линкээр шууд нээх боломжтой болгоно. Хариуцагч: **3-р гишүүн (Backend)**.

## Одоогийн байдал
✅ **https://fitcoach-nl0o.onrender.com** дээр ажиллаж байна (11/2). Render-ийн *Public Git Repository* аргаар холбосон тул `main` шинэчлэгдэхэд **автоматаар шинэчлэгдэхгүй** → Render dashboard → `fitcoach` → **Manual Deploy → Deploy latest commit**.

Env: `ANTHROPIC_API_KEY`, `CLAUDE_MODEL=claude-haiku-5-5`, `PYTHON_VERSION=3.12.7`. Илтгэлийн өмнө `CLAUDE_MODEL`-ийг `claude-sonnet-5-5` болгож болно.

## Өгөгдөл хадгалах: Neon (PostgreSQL, үнэгүй)
`DATABASE_URL` тохируулаагүй бол апп `fitcoach.db` (SQLite) файл ашигладаг. Render-ийн үнэгүй сервер **дахин байршуулах, дахин асах, унтах бүрт тэр файл устдаг** — бүртгэл, нууц үг, түүх бүгд алга болно.
Neon холбосны дараа өгөгдөл Neon дээр хадгалагдаж, deploy хийсэн ч устахгүй. Код өөрчлөх шаардлагагүй, хүснэгтүүд апп асахад автоматаар үүснэ.

1. **neon.tech** → **Sign up** (GitHub-аараа)
2. **Create project** → нэр `fitcoach` → **Region**-ийг Render сервисийнхтэй ойр сонгоно
   (Render → `fitcoach` → Settings → Region. Oregon бол *AWS US West 2 (Oregon)*, Singapore бол *AWS Asia Pacific (Singapore)*)
3. Project dashboard → **Connect** → холбох хаягийг хуулна: `postgresql://...@ep-....neon.tech/neondb?sslmode=require...`
4. Render → `fitcoach` → **Environment** → **Add Environment Variable** → Key: `DATABASE_URL`, Value: хуулсан хаяг → **Save, rebuild, and deploy**
5. **Шалгах:** сайтад имэйлээр бүртгүүлнэ → Render дээр **Manual Deploy** → дуусмагц `/login`-оор нэвтэрнэ. Акаунт хэвээр байвал болсон.

- ⚠️ `DATABASE_URL` дотор нууц үг бий. GitHub, багийн чат руу **бүү** тавь — зөвхөн Render-ийн Environment-д.
- Neon 5 минут ашиглаагүй бол унтдаг тул түүний дараах эхний хүсэлт 1–2 секунд удаан байж болно.
- Локал, Codespaces дээр `DATABASE_URL` хоосон бол өмнөх шигээ SQLite ашиглана.

## Сэрүүн байлгах ба демо
1. **Сэрүүн байлгах:** Үнэгүй сервер 15 минут хүсэлтгүй бол унтаж, дараагийн нээлт ~50 секунд удаан болно. `.github/workflows/keepalive.yml` 10 минут тутам `/healthz` руу хандана. Илүү найдвартай болгох бол **cron-job.org** → Create cronjob → URL `https://fitcoach-nl0o.onrender.com/healthz`, Every 5 minutes.
2. **Демо хэрэглэгч:** бүртгэл, нэвтрэх хуудасны **"Бүртгүүлэхгүйгээр демо хэрэглэгчээр үзэх"** товч 3 долоо хоногийн түүхтэй хэрэглэгч үүсгэнэ (`app/demo.py`). Илтгэлд үүнийг ашиглана.

## 1. Нэг удаагийн тохиргоо (Blueprint арга — repo эзэмшигч Render-д эрх өгсөн үед)
1. **render.com** → GitHub-аараа бүртгүүлнэ
2. **New → Blueprint** → `Erdenetogs/fitness-coach-ai-agent-v2` сонгоно
   (repo харагдахгүй бол Erdenetogs Render-д repo-д хандах эрх өгнө)
3. Render `render.yaml`-ийг уншаад `fitcoach` сервис үүсгэнэ → **Apply**
4. `ANTHROPIC_API_KEY` асуувал түлхүүрээ оруулна (байхгүй бол хоосон орхиход демо горимоор ажиллана)

**Шалгах:** 3–5 минутын дараа `https://fitcoach-xxxx.onrender.com` линк гарна. Нээхэд бүртгэлийн хуудас харагдана.

## 2. Дараа нь
Одоогийн сервис *Public Git Repository* аргаар холбогдсон тул `main` руу merge хийсний дараа **Manual Deploy → Deploy latest commit** дарна (Blueprint аргаар холбосон бол автоматаар байршина).

## Анхаарах
- **Үнэгүй сервер 15 минут ашиглаагүй бол унтана.** Дараагийн нээлт ~50 секунд удаан ачаална. Илтгэлийн өмнө линкийг нэг удаа нээж "сэрээгээрэй".
- **Өгөгдөл:** `DATABASE_URL` (Neon) тохируулаагүй бол сервер дахин асах бүрт бүх бүртгэл устна. Дээрх Neon хэсгийг үз.
- API түлхүүрийг **зөвхөн Render-ийн Environment** хэсэгт бичнэ. Код, GitHub руу хэзээ ч бүү оруул.
