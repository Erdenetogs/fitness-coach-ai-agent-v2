# FitCoach AI — Fitness Coach AI Agent (Capstone)

Хөргөгчний зургаас хоол санал болгох, долоо хоногийн дасгалын төлөвлөгөө гаргах,
AI coach-тай чатлах, идэвхээрээ XP цуглуулж agent-ийн level ахиулдаг вэб апп.

## Бүтэц

```
fitcoach-app/
├── pom.xml                                   Spring Boot 3, Java 17
└── src/main/
    ├── java/com/fitcoach/
    │   ├── FitCoachApplication.java          програм эхлүүлэх
    │   ├── ApiController.java                REST API (/api/...)
    │   ├── AiService.java                    Claude API дуудах
    │   ├── DemoData.java                     API key байхгүй үеийн жишээ хариу
    │   └── ApiExceptionHandler.java          алдааг JSON болгох
    └── resources/
        ├── application.properties
        └── static/index.html                 бүх frontend (HTML + CSS + JS)
```

## Ажиллуулах 3 арга

**1. Зөвхөн frontend (хамгийн хялбар).** `src/main/resources/static/index.html`-ийг
browser дээр шууд нээнэ. "Demo mode" гэж гарч жишээ хариугаар ажиллана.
Frontend хийж байгаа гишүүнд хангалттай.

**2. Backend-тэй, demo горимд (зардалгүй).**
```bash
mvn spring-boot:run
```
http://localhost:8080 нээнэ. API key тавиагүй бол backend жишээ хариу буцаана.

**3. Жинхэнэ AI-тай.**
```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-..."
mvn spring-boot:run

# macOS / Linux / Codespaces
export ANTHROPIC_API_KEY="sk-ant-..."
mvn spring-boot:run
```
Дээд буланд "AI connected" гэж гарна. Model-ийг `ANTHROPIC_MODEL` хувьсагчаар солино
(анхдагч: `claude-haiku-5-5`). Model-ийн нэрийг docs.claude.com дээрээс шалгаарай.

> API key-г код, `application.properties`, GitHub руу хэзээ ч бүү оруул.
> console.anthropic.com дээр сарын зарцуулалтын хязгаар (spending limit) тавиарай.

## API

| Method | Path | Оролт | Гаралт |
|---|---|---|---|
| GET | `/api/status` | | `{live, model}` |
| POST | `/api/food/analyze` | multipart: `image`, `goal` | `{ingredients[], note, meals[{name, calories, protein_g, minutes, uses[], steps[]}]}` |
| POST | `/api/workout/plan` | JSON: `{goal, daysPerWeek, fitnessLevel}` | `{summary, sessions[{name, minutes, exercises[{name, sets, reps}]}]}` |
| POST | `/api/coach/chat` | JSON: `{message, goal, level, streak}` | `{reply}` |

## XP ба level

- Дасгал дуусгах: +40 XP · Хоол бүртгэх: +15 XP · Өдрийн анхны чат: +5 XP
- Level N-ээс N+1 рүү: N × 100 XP. Шат: Seedling (1–2), Sprout (3–4), Athlete (5–7), Champion (8+)
- Level ахих тусам coach-ийн толгойн навч нэмэгдэж, level 5-аас толгойн тууз гарна.

## Одоогоор хийгдээгүй (дараагийн алхам)

- Профайл, XP, төлөвлөгөө browser-ийн localStorage-д хадгалагдаж байна.
  MySQL + жинхэнэ нэвтрэлт (Spring Security) нэмбэл олон төхөөрөмж дээр ажиллана
  (User, FoodLog, WorkoutPlan, WorkoutLog, AgentProgress хүснэгтүүд).
- Сануулга (notification) байхгүй.
