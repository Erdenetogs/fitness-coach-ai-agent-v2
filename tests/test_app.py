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
               goal="lose", level="beginner", days_per_week=6, equipment="none")


def new_client(**overrides) -> tuple[TestClient, int]:
    """Шинэ хэрэглэгч бүртгүүлээд (client, user_id) буцаана."""
    c = TestClient(app)
    r = c.post("/onboarding", data={**PROFILE, **overrides}, follow_redirects=False)
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
                r = TestClient(app).post("/onboarding", data={**PROFILE, **bad}, follow_redirects=False)
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


if __name__ == "__main__":
    unittest.main()
