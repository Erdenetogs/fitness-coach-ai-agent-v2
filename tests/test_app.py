"""FitCoach автомат тест.

Ажиллуулах (repo-гийн үндсэн хавтаснаас):  python -m unittest -v
API түлхүүр шаардлагагүй — агентыг демо горимоор болон "хуурамч Claude"-аар шалгана.
"""
import os
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from types import SimpleNamespace as NS

# Тест бүр өөрийн түр өгөгдлийн сантай байна (app-ийг import хийхээс ӨМНӨ тохируулна)
_TMP = tempfile.mkdtemp()
os.environ["FITCOACH_DB"] = os.path.join(_TMP, "test.db")
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from app import db, planner, xp  # noqa: E402
from app.agent import llm  # noqa: E402
from app.main import app  # noqa: E402

PROFILE = dict(name="Тест", age=21, gender="female", height_cm=165, weight_kg=62,
               goal="lose", level="beginner", days_per_week=6, equipment="none", password="secret-pass-1")
_emails = iter(range(10 ** 6))


def fresh_email() -> str:
    return f"user{next(_emails)}@test.mn"


def new_client(**overrides) -> tuple[TestClient, int]:
    """Шинэ хэрэглэгч бүртгүүлээд (client, user_id) буцаана."""
    c = TestClient(app)
    r = c.post("/onboarding", data={**PROFILE, "email": fresh_email(), **overrides}, follow_redirects=False)
    assert r.status_code == 303
    token = r.cookies.get("fitcoach_token") or c.cookies.get("fitcoach_token")
    return c, db.get_user_by_token(token)["id"]


class PagesTest(unittest.TestCase):
    def test_redirects_to_onboarding_without_user(self):
        r = TestClient(app).get("/", follow_redirects=False)
        self.assertEqual(r.status_code, 303)
        self.assertEqual(r.headers["location"], "/onboarding")

    def test_all_pages_render(self):
        c, _ = new_client()
        for path in ["/", "/workout", "/food", "/progress", "/profile", "/chat"]:
            with self.subTest(path=path):
                r = c.get(path)
                self.assertEqual(r.status_code, 200)
                self.assertIn("FitCoach", r.text)

    def test_healthz(self):
        self.assertEqual(TestClient(app).get("/healthz").json(), {"ok": True})

    def test_api_requires_user(self):
        r = TestClient(app).post("/api/chat", json={"message": "hi"})
        self.assertEqual(r.status_code, 401)


class PlannerTest(unittest.TestCase):
    def test_plan_has_requested_training_days(self):
        for days in range(2, 7):
            with self.subTest(days=days):
                plan = planner.build_plan({**PROFILE, "days_per_week": days})
                active = [d for d in plan.values() if d["exercises"]]
                self.assertEqual(len(active), days)
                self.assertEqual(set(plan), set(planner.WEEKDAYS))

    def test_nutrition_goal_direction(self):
        lose = planner.nutrition({**PROFILE, "goal": "lose"})
        gain = planner.nutrition({**PROFILE, "goal": "gain"})
        self.assertLess(lose["kcal"], lose["tdee"])
        self.assertGreater(gain["kcal"], gain["tdee"])


class ApiTest(unittest.TestCase):
    def test_weight_validation_and_log(self):
        c, _ = new_client()
        self.assertEqual(c.post("/api/weight", json={"kg": 10}).status_code, 400)
        r = c.post("/api/weight", json={"kg": 61.4}).json()
        self.assertEqual(r["weights"][-1]["kg"], 61.4)

    def test_fridge_needs_input(self):
        c, _ = new_client()
        self.assertEqual(c.post("/api/fridge", data={"ingredients": ""}).status_code, 400)

    def test_fridge_demo_returns_recipes_and_steps(self):
        c, _ = new_client()
        r = c.post("/api/fridge", data={"ingredients": "өндөг, тахиа"}).json()
        self.assertTrue(r["demo"])
        self.assertGreaterEqual(len(r["recipes"]), 1)
        self.assertTrue(r["agent_steps"])

    def test_fridge_rejects_non_image(self):
        c, _ = new_client()
        r = c.post("/api/fridge", files={"photo": ("a.txt", b"hello", "text/plain")})
        self.assertEqual(r.status_code, 400)

    def test_memory_delete(self):
        c, uid = new_client()
        db.add_memory(uid, "Өвдөг өвддөг")
        mid = db.get_memories(uid)[0]["id"]
        self.assertTrue(c.delete(f"/api/memory/{mid}").json()["ok"])
        self.assertEqual(db.get_memories(uid), [])


class DemoAgentTest(unittest.TestCase):
    """API түлхүүргүй үед агент бодит хэрэгслүүдийг дуудаж өгөгдлийг өөрчилдөг эсэх."""

    def test_pain_saves_memory_and_changes_plan(self):
        c, uid = new_client()
        r = c.post("/api/chat", json={"message": "Зүүн өвдөг өвдөж байна"}).json()
        self.assertTrue(r["plan_changed"])
        self.assertIn("Зүүн өвдөг", db.get_memories(uid)[0]["text"])
        today = db.get_plan(uid)[planner.today_name()]
        self.assertEqual(today["title"], "Сэргээх өдөр")

    def test_weight_message_logs_weight(self):
        c, uid = new_client()
        c.post("/api/chat", json={"message": "Жин 60.5 кг боллоо"})
        self.assertEqual(db.get_weights(uid)[-1]["kg"], 60.5)

    def test_every_reply_has_steps(self):
        c, _ = new_client()
        for msg in ["сайн уу", "калори хэд вэ", "явц хэр байна", "level ямар"]:
            with self.subTest(msg=msg):
                r = c.post("/api/chat", json={"message": msg}).json()
                self.assertTrue(r["reply"])
                self.assertTrue(r["agent_steps"])


class LiveAgentLoopTest(unittest.TestCase):
    """Claude API-г хуурамч client-ээр орлуулж agent loop (tool_use → tool_result → хариу)-г шалгана."""

    def setUp(self):
        self.calls = []
        calls = self.calls

        class Messages:
            def create(self, **kw):
                calls.append(kw)
                if len(calls) == 1:
                    return NS(stop_reason="tool_use", content=[
                        NS(type="tool_use", id="t1", name="get_workout_plan", input={})])
                if len(calls) == 2:
                    return NS(stop_reason="tool_use", content=[
                        NS(type="tool_use", id="t2", name="update_workout_day",
                           input={"day": "Даваа", "title": "Хөнгөн", "reason": "test",
                                  "exercises": [{"name": "Алхалт", "duration_min": 20}]}),
                        NS(type="tool_use", id="t3", name="save_memory", input={"fact": "Нуруу өвддөг"})])
                return NS(stop_reason="end_turn", content=[NS(type="text", text="Даваа гарагийг хөнгөлөв.")])

        self._saved = llm._client
        llm._client = NS(messages=Messages())

    def tearDown(self):
        llm._client = self._saved

    def test_tool_loop_changes_data(self):
        c, uid = new_client()
        r = c.post("/api/chat", json={"message": "нуруу өвдөж байна, даваагийн дасгалыг хөнгөлөөч"}).json()
        self.assertEqual(r["reply"], "Даваа гарагийг хөнгөлөв.")
        self.assertEqual(len(r["agent_steps"]), 3)
        self.assertTrue(r["plan_changed"])
        self.assertEqual(db.get_plan(uid)["Даваа"]["exercises"][0]["name"], "Алхалт")
        self.assertEqual(db.get_memories(uid)[0]["text"], "Нуруу өвддөг")
        # Хэрэгслийн үр дүнг Claude-д буцааж өгсөн эсэх
        self.assertEqual(self.calls[1]["messages"][-1]["content"][0]["type"], "tool_result")

    def test_english_user_gets_plan_in_english(self):
        """Англи хэрэглэгчид AI монгол үг холихгүйн тулд: заавар + төлөвлөгөөний англи нэрс."""
        c, _ = new_client()
        c.get("/lang/en")
        c.post("/api/chat", json={"message": "make Monday easier"})
        self.assertIn("write your entire reply in English only", self.calls[0]["system"])
        # get_workout_plan (t1)-ийн үр дүн. messages жагсаалт дуудлага бүрт өсдөг тул id-аар нь хайна.
        tool_result = next(part["content"] for m in self.calls[-1]["messages"] if isinstance(m["content"], list)
                           for part in m["content"] if isinstance(part, dict) and part.get("tool_use_id") == "t1")
        self.assertIn("plan_in_user_language", tool_result)
        self.assertIn('"day": "Monday"', tool_result)
        self.assertIn("Push-ups", tool_result)


class XpTest(unittest.TestCase):
    def test_level_math(self):
        self.assertEqual(xp.from_total(0)["level"], 1)
        self.assertEqual(xp.from_total(99)["level"], 1)
        self.assertEqual(xp.from_total(100)["level"], 2)
        self.assertEqual(xp.from_total(300)["level"], 3)
        self.assertEqual(xp.from_total(1000)["stage"], "Тамирчин")

    def test_chat_xp_once_per_day(self):
        c, _ = new_client()
        self.assertEqual(c.post("/api/chat", json={"message": "сайн уу"}).json()["xp"]["gained"], 5)
        self.assertIsNone(c.post("/api/chat", json={"message": "сайн уу"}).json()["xp"])

    def test_workout_xp_only_when_all_done(self):
        c, uid = new_client(days_per_week=6)
        exercises = db.get_plan(uid)[planner.today_name()]["exercises"]
        if not exercises:
            self.skipTest("Өнөөдөр амрах өдөр")
        results = [c.post("/api/workout/done", json={"exercise": e["name"], "done": True}).json()["xp"]
                   for e in exercises]
        self.assertTrue(all(x is None for x in results[:-1]))
        self.assertEqual(results[-1]["gained"], 40)

    def test_meal_xp_not_duplicated(self):
        c, _ = new_client()
        recipe = {"title": "Омлет", "kcal": 300}
        self.assertEqual(c.post("/api/recipes", json={"recipe": recipe}).json()["xp"]["gained"], 15)
        self.assertIsNone(c.post("/api/recipes", json={"recipe": recipe}).json()["xp"])

    def test_streak_counts_consecutive_days(self):
        _, uid = new_client()
        con = sqlite3.connect(db.DB_PATH)
        for i in [0, 1, 2, 4]:  # 3 хоног дараалан + 1 тасарсан өдөр
            d = (date.today() - timedelta(days=i)).isoformat()
            con.execute("INSERT INTO xp_events (user_id, day, kind, amount, key) VALUES (?,?,?,?,?)",
                        (uid, d, "chat", 5, d))
        con.commit()
        con.close()
        self.assertEqual(xp.streak(uid), 3)


class SecurityAndValidationTest(unittest.TestCase):
    def test_cookie_is_random_token_not_user_id(self):
        c, uid = new_client()
        token = c.cookies.get("fitcoach_token")
        self.assertNotEqual(token, str(uid))
        self.assertGreater(len(token), 30)
        # Хэрэглэгчийн дугаарыг cookie-д тавиад бусдын мэдээлэлд нэвтэрч болохгүй
        forged = TestClient(app)
        forged.cookies.set("fitcoach_token", str(uid))
        self.assertEqual(forged.get("/", follow_redirects=False).status_code, 303)
        self.assertEqual(forged.get("/api/progress").status_code, 401)

    def test_onboarding_rejects_bad_values(self):
        for bad in [dict(goal="hack"), dict(age=5), dict(weight_kg=999), dict(days_per_week=9), dict(name="  ")]:
            with self.subTest(bad=bad):
                r = TestClient(app).post("/onboarding", data={**PROFILE, "email": fresh_email(), **bad},
                                         follow_redirects=False)
                self.assertEqual(r.status_code, 400)

    def test_recipe_needs_title(self):
        c, _ = new_client()
        self.assertEqual(c.post("/api/recipes", json={"recipe": {}}).status_code, 400)

    def test_agent_tools_validate_input(self):
        from app.agent.tools import run_tool
        _, uid = new_client()
        self.assertIn("error", run_tool(uid, "update_workout_day", {"day": "Friday", "exercises": [], "reason": "x"}))
        self.assertIn("error", run_tool(uid, "log_weight", {"kg": 999}))
        self.assertIn("error", run_tool(uid, "save_memory", {"fact": "  "}))
        self.assertEqual(run_tool(uid, "log_weight", {"kg": 61.44})["kg"], 61.4)

    def test_demo_does_not_log_days_as_weight(self):
        from app.agent import coach
        _, uid = new_client()
        before = db.get_weights(uid)
        coach.chat(uid, "Жин хасахад 30 хоног хангалттай юу?")
        self.assertEqual(db.get_weights(uid), before)

    def test_history_uses_local_date(self):
        _, uid = new_client()
        db.set_exercise_done(uid, "Суулт", True)
        self.assertEqual(db.get_workout_history(uid, 1)[-1]["day"], date.today().isoformat())


class LanguageTest(unittest.TestCase):
    """Хэл солих товч ба 3 хэлний орчуулга."""

    def test_switch_sets_cookie_and_translates_pages(self):
        c, _ = new_client()
        r = c.get("/lang/en?next=/workout", follow_redirects=False)
        self.assertEqual((r.status_code, r.headers["location"]), (303, "/workout"))
        page = c.get("/workout").text
        self.assertIn('lang="en"', page)
        self.assertIn("This week&#39;s workouts", page)
        c.get("/lang/ko")
        self.assertIn("이번 주 운동", c.get("/workout").text)

    def test_unknown_language_and_unsafe_next_are_ignored(self):
        c = TestClient(app)
        r = c.get("/lang/xx?next=//evil.example.com", follow_redirects=False)
        self.assertEqual(r.headers["location"], "/")
        self.assertNotIn("fitcoach_lang", r.headers.get("set-cookie", ""))

    def test_accept_language_picks_default(self):
        r = TestClient(app).get("/onboarding", headers={"Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"})
        self.assertIn('lang="ko"', r.text)
        self.assertIn('lang="mn"', TestClient(app).get("/onboarding").text)

    def test_demo_coach_answers_in_chosen_language(self):
        c, uid = new_client()
        c.get("/lang/en")
        r = c.post("/api/chat", json={"message": "My weight is 63.5 kg"}).json()
        self.assertIn("Logged 63.5 kg", r["reply"])
        self.assertEqual(db.get_weights(uid)[-1]["kg"], 63.5)
        c.get("/lang/ko")
        r = c.post("/api/chat", json={"message": "왼쪽 무릎이 아파"}).json()
        self.assertTrue(r["plan_changed"])
        self.assertIn("회복일", r["reply"])
        # Өгөгдлийн санд Монголоор хадгалагдана — хэл солиход ч зөв харагдана
        self.assertEqual(db.get_plan(uid)[planner.today_name()]["title"], "Сэргээх өдөр")

    def test_api_errors_and_xp_follow_language(self):
        c, _ = new_client()
        c.get("/lang/ko")
        self.assertEqual(c.post("/api/chat", json={"message": " "}).json()["error"], "메시지가 비어 있어요")
        r = c.post("/api/recipes", json={"recipe": {"title": "오믈렛", "kcal": 300}}).json()
        self.assertEqual(r["xp"]["reason"], "식사 기록")
        self.assertEqual(r["xp"]["stage"], "씨앗")

    def test_every_string_has_three_languages(self):
        from app import i18n
        for key, row in i18n.STRINGS.items():
            with self.subTest(key=key):
                self.assertEqual(len(row), 3)
                self.assertTrue(all(row))
        self.assertEqual(i18n.exercise("Суулт (squat)", "en"), "Squats")
        self.assertEqual(i18n.weekday("Даваа", "ko"), "월요일")



class ChatFormatTest(unittest.TestCase):
    def test_bold_rendered_and_html_escaped(self):
        from app.main import _md
        out = str(_md("Target **1,380 kcal** <script>x</script>"))
        self.assertIn("<strong>1,380 kcal</strong>", out)
        self.assertNotIn("<script>", out)


class DemoUserTest(unittest.TestCase):
    def test_demo_login_has_history(self):
        c = TestClient(app)
        r = c.post("/demo", follow_redirects=False)
        self.assertEqual(r.status_code, 303)
        for path in ["/", "/workout", "/food", "/progress", "/profile", "/chat"]:
            with self.subTest(path=path):
                self.assertEqual(c.get(path).status_code, 200)
        st = c.get("/api/xp").json()
        self.assertGreaterEqual(st["level"], 3)
        self.assertGreaterEqual(st["streak"], 5)
        prog = c.get("/api/progress").json()
        self.assertGreaterEqual(len(prog["weights"]), 7)
        self.assertGreaterEqual(len(prog["history"]), 8)
        self.assertLess(prog["weights"][-1]["kg"], prog["weights"][0]["kg"])

    def test_each_demo_click_is_separate_user(self):
        a, b = TestClient(app), TestClient(app)
        a.post("/demo"); b.post("/demo")
        a.post("/api/weight", json={"kg": 70})
        self.assertNotEqual(b.get("/api/progress").json()["weights"][-1]["kg"], 70)

    def test_demo_chat_matches_demo_data(self):
        """Урьдчилан бичсэн чат өгөгдөлтэйгээ таарах ёстой — эс бөгөөс жинхэнэ AI зөрүүг олоод
        "өмнө нь буруу хэлсэн" гэж хариулдаг."""
        c = TestClient(app)
        c.post("/demo")
        uid = db.get_user_by_token(c.cookies.get("fitcoach_token"))["id"]
        plan = db.get_plan(uid)
        cardio = [d for d in planner.WEEKDAYS if plan[d]["focus"] == "cardio"]
        self.assertEqual(len(cardio), 1)
        names = [e["name"] for e in plan[cardio[0]]["exercises"]]
        for jumping in ("Үсрэлт (jumping jack)", "Бёрпи", "Уулчин (mountain climber)"):
            self.assertNotIn(jumping, names)  # чатад "үсрэлт, бёрпиг хасав" гэсэн

        prog = c.get("/api/progress").json()
        change = round(prog["weights"][-1]["kg"] - prog["weights"][0]["kg"], 1)
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        trained = len([h for h in db.get_workout_history(uid, 7) if h["day"] >= week_ago])
        streak = c.get("/api/xp").json()["streak"]
        progress_msg = [m for m in db.get_messages(uid) if m["role"] == "assistant"][-1]["content"]
        self.assertIn(f"{change:+.1f}".replace("-", "−") + " кг", progress_msg)
        self.assertIn(f"{trained} өдөр дасгал", progress_msg)
        self.assertIn(f"{streak} өдөр дараалан", progress_msg)

    def test_demo_in_korean(self):
        c = TestClient(app)
        c.get("/lang/ko")
        c.post("/demo")
        page = c.get("/chat").text
        self.assertIn("데모 학생", c.get("/profile").text)
        self.assertIn("목요일 운동 변경", page)
        self.assertIn("닭고기 브로콜리 볶음밥", c.get("/food").text)


class LoginTest(unittest.TestCase):
    """Имэйл + нууц үгээр бүртгүүлж, өөр төхөөрөмжөөс (шинэ client) нэвтрэх."""

    def test_signup_then_login_from_another_device(self):
        email = fresh_email()
        c1, uid = new_client(email=email.upper())  # том үсгээр бичсэн ч жижиг болгож хадгална
        row = db.get_user(uid)
        self.assertEqual(row["email"], email)
        self.assertNotIn("secret-pass-1", row["password_hash"])  # нууц үгийг шууд хадгалахгүй
        self.assertTrue(row["password_hash"].startswith("scrypt$"))

        c1.get("/logout")
        self.assertEqual(c1.get("/", follow_redirects=False).status_code, 303)

        c2 = TestClient(app)  # өөр утас
        r = c2.post("/login", data={"email": f"  {email} ", "password": "secret-pass-1"}, follow_redirects=False)
        self.assertEqual((r.status_code, r.headers["location"]), (303, "/"))
        self.assertIn("Тест", c2.get("/").text)
        self.assertEqual(c2.get("/api/xp").status_code, 200)

    def test_wrong_password_and_unknown_email_look_the_same(self):
        email = fresh_email()
        new_client(email=email)
        bad_pw = TestClient(app).post("/login", data={"email": email, "password": "wrong-password"})
        no_user = TestClient(app).post("/login", data={"email": fresh_email(), "password": "wrong-password"})
        self.assertEqual(bad_pw.status_code, 401)
        self.assertEqual(no_user.status_code, 401)
        self.assertIn("Имэйл эсвэл нууц үг буруу байна", bad_pw.text)
        self.assertIn("Имэйл эсвэл нууц үг буруу байна", no_user.text)
        self.assertIn(f'value="{email}"', bad_pw.text)  # имэйлээ дахин бичих шаардлагагүй

    def test_too_many_attempts_are_blocked(self):
        email = fresh_email()
        new_client(email=email)
        c = TestClient(app)
        for _ in range(5):
            c.post("/login", data={"email": email, "password": "nope-nope"})
        r = c.post("/login", data={"email": email, "password": "secret-pass-1"}, follow_redirects=False)
        self.assertEqual(r.status_code, 429)  # зөв нууц үг ч 15 минут хаагдана

    def test_signup_validates_email_and_password(self):
        email = fresh_email()
        new_client(email=email)
        cases = [({"email": "not-an-email"}, 400), ({"password": "short"}, 400), ({"email": email}, 409)]
        for override, status in cases:
            with self.subTest(override=override):
                data = {**PROFILE, "email": fresh_email(), **override}
                r = TestClient(app).post("/onboarding", data=data, follow_redirects=False)
                self.assertEqual(r.status_code, status)
                self.assertIsInstance(r.json()["detail"], str)  # JS энэ текстийг харуулна

    def test_login_page_in_three_languages(self):
        for code, word in [("mn", "Нэвтрэх"), ("en", "Sign in"), ("ko", "로그인")]:
            c = TestClient(app)
            c.get(f"/lang/{code}")
            with self.subTest(lang=code):
                self.assertIn(word, c.get("/login").text)
                self.assertIn('href="/login"', c.get("/onboarding").text)

    def test_old_database_gets_new_columns(self):
        """Нэвтрэх систем нэмэгдэхээс өмнөх fitcoach.db ажилласаар байх ёстой."""
        path = os.path.join(_TMP, "old.db")
        c = sqlite3.connect(path)
        with c:
            c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, age INTEGER,"
                      " gender TEXT, height_cm REAL, weight_kg REAL, goal TEXT, level TEXT, days_per_week INTEGER,"
                      " equipment TEXT, created_at TEXT)")
            c.execute("INSERT INTO users (name) VALUES ('Хуучин')")
        c.close()
        saved, db.DB_PATH = db.DB_PATH, path
        try:
            db.init_db()
            c = sqlite3.connect(path)
            cols = {r[1] for r in c.execute("PRAGMA table_info(users)")}
            c.close()
            self.assertTrue({"token", "email", "password_hash"} <= cols)
        finally:
            db.DB_PATH = saved


class StaticCacheTest(unittest.TestCase):
    def test_static_links_carry_version(self):
        """CSS/JS холбоос дээр файлын hash байх ёстой — deploy-ийн дараа браузер хуучин JS ашиглахгүй."""
        from app.main import STATIC_V
        page = TestClient(app).get("/onboarding").text
        self.assertRegex(STATIC_V, r"^[0-9a-f]{8}$")
        self.assertIn(f"/static/js/common.js?v={STATIC_V}", page)
        self.assertIn(f"/static/css/app.css?v={STATIC_V}", page)


class AgentHistoryTest(unittest.TestCase):
    """Жинхэнэ Claude дээр олдсон алдаанууд: түүхэнд хийсэн үйлдэл алга, BadRequest."""

    def _fake(self, behaviour):
        calls = []

        class BadRequestError(Exception):
            pass

        class Messages:
            def create(self, **kw):
                calls.append(kw)
                return behaviour(len(calls), kw, BadRequestError)

        saved = llm._client
        llm._client = NS(messages=Messages())
        self.addCleanup(setattr, llm, "_client", saved)
        return calls

    def test_history_tells_claude_which_actions_ran(self):
        calls = self._fake(lambda n, kw, E: NS(stop_reason="end_turn", content=[NS(type="text", text="ok")]))
        c, uid = new_client()
        db.add_message(uid, "user", "өвдөг өвдөж байна")
        db.add_message(uid, "assistant", "Өөрчиллөө.", [{"icon": "x", "text": "Даваа гарагийн дасгалыг өөрчилсөн"}])
        c.post("/api/chat", json={"message": "баярлалаа"})
        msgs = calls[0]["messages"]
        self.assertTrue(any("Хийсэн үйлдэл: Даваа гарагийн дасгалыг өөрчилсөн" in m["content"]
                            for m in msgs if m["role"] == "assistant"))
        roles = [m["role"] for m in msgs]
        self.assertEqual(roles[0], "user")
        self.assertTrue(all(a != b for a, b in zip(roles, roles[1:])), roles)

    def test_bad_request_retries_without_history(self):
        def behaviour(n, kw, E):
            if n == 1:
                raise E("history broke it")
            return NS(stop_reason="end_turn", content=[NS(type="text", text="дахин оролдоод болсон")])
        calls = self._fake(behaviour)
        c, uid = new_client()
        db.add_message(uid, "user", "өмнөх асуулт")
        db.add_message(uid, "assistant", "өмнөх")
        r = c.post("/api/chat", json={"message": "сайн уу"}).json()
        self.assertEqual(r["reply"], "дахин оролдоод болсон")
        self.assertEqual(len(calls[1]["messages"]), 1)

    def test_empty_text_blocks_not_sent_back(self):
        def behaviour(n, kw, E):
            if n == 1:
                return NS(stop_reason="tool_use", content=[NS(type="text", text=""),
                                                           NS(type="tool_use", id="t1", name="get_workout_plan", input={})])
            return NS(stop_reason="end_turn", content=[NS(type="text", text="ok")])
        calls = self._fake(behaviour)
        c, _ = new_client()
        c.post("/api/chat", json={"message": "төлөвлөгөө"})
        assistant = calls[1]["messages"][-2]
        self.assertEqual([b["type"] for b in assistant["content"]], ["tool_use"])

if __name__ == "__main__":
    unittest.main()
