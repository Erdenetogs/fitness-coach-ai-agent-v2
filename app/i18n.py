"""Олон хэл (Монгол / English / 한국어).

- Хэрэглэгчийн сонгосон хэл `fitcoach_lang` cookie-д хадгалагдана. Cookie байхгүй бол
  браузерын Accept-Language-аар (ko → 한국어, en → English), бусад үед Монгол.
- Өгөгдлийн санд (дасгалын нэр, гарагийн нэр, өдрийн гарчиг) Монголоор хадгална,
  харуулахдаа энд орчуулна. Тиймээс хэл солиход хуучин өгөгдөл ч зөв харагдана.
- Шинэ текст нэмэх: STRINGS-д нэг мөр (mn, en, ko) нэмээд template-д {{ t('түлхүүр') }}.
  JavaScript-д хэрэгтэй бол түлхүүрийг "js." -ээр эхлүүлнэ.
"""
from app import planner

LANGS = {"mn": "Монгол", "en": "English", "ko": "한국어"}
SHORT = {"mn": "MN", "en": "EN", "ko": "KO"}
AI_LANG = {"mn": "Mongolian (Монгол хэл)", "en": "English", "ko": "Korean (한국어)"}
DEFAULT = "mn"
COOKIE = "fitcoach_lang"
_I = {"mn": 0, "en": 1, "ko": 2}

STRINGS: dict[str, tuple[str, str, str]] = {
    # ---------- Ерөнхий ----------
    "nav.home": ("Нүүр", "Home", "홈"),
    "nav.workout": ("Дасгал", "Workouts", "운동"),
    "nav.food": ("Хоол", "Meals", "식단"),
    "nav.progress": ("Явц", "Progress", "기록"),
    "nav.profile": ("Би", "Me", "내 정보"),
    "nav.coach": ("Дасгалжуулагч", "Coach", "코치"),
    "nav.main_aria": ("Үндсэн цэс", "Main menu", "메인 메뉴"),
    "nav.chat_aria": ("AI дасгалжуулагчтай ярих", "Talk to your AI coach", "AI 코치와 대화하기"),
    "nav.chat_cta": ("Дасгалжуулагчтай ярих", "Talk to your coach", "코치와 대화하기"),
    "lang.label": ("Хэл", "Language", "언어"),
    "demo": ("Демо горим", "Demo mode", "데모 모드"),
    "demo.title": ("ANTHROPIC_API_KEY тохируулаагүй — агент демо горимоор ажиллаж байна",
                   "No ANTHROPIC_API_KEY set, so the coach is running in demo mode",
                   "ANTHROPIC_API_KEY가 없어 코치가 데모 모드로 작동 중이에요"),
    "ai.live": ("Claude AI агент", "Claude AI agent", "Claude AI 에이전트"),
    "unit.kcal": ("ккал", "kcal", "kcal"),
    "unit.kg": ("кг", "kg", "kg"),
    "unit.g": ("г", "g", "g"),

    # ---------- Coach / XP ----------
    "coach.avatar_aria": ("AI дасгалжуулагч, level {level}", "AI coach, level {level}", "AI 코치, 레벨 {level}"),
    "coach.card_aria": ("Coach-ийн level {level}, {xp} / {need} XP", "Coach level {level}, {xp} of {need} XP",
                        "코치 레벨 {level}, {xp} / {need} XP"),
    "coach.level": ("Level {n}", "Level {n}", "레벨 {n}"),
    "coach.to_next": ("дараагийн level хүртэл {n}", "{n} to next level", "다음 레벨까지 {n}"),
    "coach.streak1": ("өдөр", "day", "일"),
    "coach.streak2": ("дараалан", "streak", "연속"),
    "coach.streak_n": ("{n} өдөр дараалан", "{n}-day streak", "{n}일 연속"),
    "coach.ask_level":("Миний level ямар байна?", "What's my level?", "내 레벨은 어때?"),
    "stage.1": ("Үр", "Seed", "씨앗"),
    "stage.2": ("Нахиа", "Sprout", "새싹"),
    "stage.3": ("Тамирчин", "Athlete", "선수"),
    "stage.4": ("Аварга", "Champion", "챔피언"),
    "xp.workout": ("өнөөдрийн дасгал дууслаа", "today's workout done", "오늘 운동 완료"),
    "xp.meal": ("хоол бүртгэлээ", "meal logged", "식사 기록"),
    "xp.chat": ("өдрийн анхны яриа", "first chat today", "오늘 첫 대화"),

    # ---------- Утгууд ----------
    "goal.lose": ("Жин хасах", "Lose weight", "체중 감량"),
    "goal.gain": ("Булчин нэмэх", "Build muscle", "근육 증가"),
    "goal.fit": ("Эрүүл чийрэг байх", "Stay fit", "건강 유지"),
    "level.beginner": ("Анхан", "Beginner", "초급"),
    "level.intermediate": ("Дунд", "Intermediate", "중급"),
    "level.advanced": ("Ахисан", "Advanced", "고급"),
    "equip.none": ("Багажгүй (гэрт)", "No equipment (home)", "기구 없음 (집)"),
    "equip.dumbbell": ("Гантель", "Dumbbells", "덤벨"),
    "equip.gym": ("Фитнес заал", "Gym", "헬스장"),
    "focus.upper": ("Дээд бие", "Upper body", "상체"),
    "focus.lower": ("Доод бие", "Lower body", "하체"),
    "focus.cardio": ("Кардио", "Cardio", "유산소"),
    "focus.full": ("Бүтэн бие", "Full body", "전신"),
    "focus.rest": ("Амрах өдөр", "Rest day", "휴식일"),
    "focus.recovery": ("Сэргээх өдөр", "Recovery day", "회복일"),
    "focus.custom": ("Шинэчилсэн дасгал", "Updated workout", "변경된 운동"),
    "wd.0": ("Даваа", "Monday", "월요일"), "wd.1": ("Мягмар", "Tuesday", "화요일"),
    "wd.2": ("Лхагва", "Wednesday", "수요일"), "wd.3": ("Пүрэв", "Thursday", "목요일"),
    "wd.4": ("Баасан", "Friday", "금요일"), "wd.5": ("Бямба", "Saturday", "토요일"),
    "wd.6": ("Ням", "Sunday", "일요일"),
    "wds.0": ("Да", "Mon", "월"), "wds.1": ("Мя", "Tue", "화"), "wds.2": ("Лх", "Wed", "수"),
    "wds.3": ("Пү", "Thu", "목"), "wds.4": ("Ба", "Fri", "금"), "wds.5": ("Бя", "Sat", "토"),
    "wds.6": ("Ня", "Sun", "일"),
    "f.male": ("Эр", "Male", "남성"),
    "f.female": ("Эм", "Female", "여성"),

    # ---------- Нүүр ----------
    "page.home": ("Нүүр", "Home", "홈"),
    "home.weekday": ("{day} гараг", "{day}", "{day}"),
    "home.hello": ("Сайн уу, {name}", "Hi, {name}", "안녕하세요, {name}님"),
    "home.done_all": ("Өнөөдрийн дасгал дууслаа. Гайхалтай!", "Today's workout is done. Great job!", "오늘 운동 완료! 멋져요!"),
    "home.left": ("{n} дасгал үлдлээ", "{n} exercises left", "{n}개 남았어요"),
    "home.view": ("Харах", "View", "보기"),
    "home.continue": ("Үргэлжлүүлэх", "Continue", "계속하기"),
    "home.start": ("Эхлэх", "Start", "시작"),
    "home.rest": ("Өнөөдөр амарч, булчингаа сэргээгээрэй.", "Rest today and let your muscles recover.",
                  "오늘은 쉬면서 근육을 회복하세요."),
    "home.week_aria": ("Энэ долоо хоног", "This week", "이번 주"),
    "home.kcal": ("Өдрийн калори", "Daily calories", "하루 칼로리"),
    "home.protein": ("Уураг {n} г", "Protein {n} g", "단백질 {n}g"),
    "home.weight": ("Одоогийн жин", "Current weight", "현재 체중"),
    "home.change": ("Эхлэлээс {x} кг", "{x} kg since start", "시작 대비 {x}kg"),
    "home.goal": ("Зорилго: {goal}", "Goal: {goal}", "목표: {goal}"),
    "home.fridge": ("Хөргөгчөө зургаар авах", "Snap your fridge", "냉장고 사진 찍기"),
    "home.fridge_sub": ("Байгаа орцоор тань зорилгод тохирох жор олно", "Get recipes for your goal from what you have",
                        "있는 재료로 목표에 맞는 레시피를 찾아요"),
    "home.memory": ("Дасгалжуулагч таны тухай мэдэж байгаа", "What your coach knows about you", "코치가 기억하는 내용"),
    "home.all": ("Бүгд", "All", "전체"),
    "home.memory_empty": (
        "Одоогоор хоосон. Гэмтэл, дуртай хоол, хуваариа чатад хэлбэл дасгалжуулагч санаж, төлөвлөгөөндөө тусгана.",
        "Nothing yet. Tell the coach about injuries, favourite foods or your schedule in chat and it will remember and plan around them.",
        "아직 없어요. 부상, 좋아하는 음식, 일정을 채팅으로 알려주면 코치가 기억하고 계획에 반영해요."),

    # ---------- Бүртгэл ----------
    "page.start": ("Эхлэх", "Get started", "시작하기"),
    "ob.tagline": ("Хичээлийн хажуугаар дасгал, хоолоо зохицуулах AI дасгалжуулагч.",
                   "An AI coach that fits workouts and meals around student life.",
                   "학교생활에 맞춰 운동과 식단을 챙겨주는 AI 코치."),
    "ob.tagline_sub": ("Хөргөгчний зургаас жор, долоо хоногийн дасгал, ахиц бүрт өсдөг дасгалжуулагч.",
                       "Recipes from a fridge photo, a weekly plan, and a coach that grows with every workout.",
                       "냉장고 사진으로 레시피, 주간 운동 계획, 운동할수록 성장하는 코치."),
    "ob.h1": ("Сайн уу! Танилцъя.", "Hi! Let's get to know you.", "안녕하세요! 먼저 알려주세요."),
    "ob.sub": ("Таны мэдээллээр AI дасгалжуулагч хувийн төлөвлөгөө гаргана.",
               "Your AI coach builds a personal plan from your answers.",
               "입력한 정보로 AI 코치가 맞춤 계획을 만들어요."),
    "f.name_your": ("Таны нэр", "Your name", "이름"),
    "f.name_ph": ("Жишээ: Баяраа", "e.g. Bayaraa", "예: 바야라"),
    "f.age": ("Нас", "Age", "나이"),
    "f.gender": ("Хүйс", "Gender", "성별"),
    "ob.body": ("Биеийн хэмжээ", "Your body", "신체 정보"),
    "ob.body_sub": ("Өдрийн калорийн хэрэгцээг тооцоход ашиглана.", "Used to work out your daily calories.",
                    "하루 필요 칼로리 계산에 사용해요."),
    "f.height_cm": ("Өндөр (см)", "Height (cm)", "키 (cm)"),
    "f.weight_kg": ("Жин (кг)", "Weight (kg)", "체중 (kg)"),
    "ob.goal_h": ("Таны зорилго юу вэ?", "What's your goal?", "목표가 무엇인가요?"),
    "f.goal": ("Зорилго", "Goal", "목표"),
    "f.experience": ("Дасгалын туршлага", "Training experience", "운동 경험"),
    "ob.sched": ("Хуваарь ба багаж", "Schedule and equipment", "일정과 기구"),
    "ob.days_q": ("Долоо хоногт хэдэн өдөр?", "How many days a week?", "일주일에 며칠?"),
    "ob.equip_q": ("Юу ашиглаж чадах вэ?", "What can you use?", "사용할 수 있는 것은?"),
    "btn.back": ("Буцах", "Back", "이전"),
    "btn.continue": ("Үргэлжлүүлэх", "Continue", "다음"),
    "js.ob_make": ("Төлөвлөгөө гаргах", "Create my plan", "계획 만들기"),
    "js.continue": ("Үргэлжлүүлэх", "Continue", "다음"),
    "js.ob_all": ("Бүх сонголтыг хийнэ үү.", "Please choose an option for each question.", "모든 항목을 선택해 주세요."),
    "js.ob_invalid": ("{label}: зөв утга оруулна уу.", "{label}: enter a valid value.", "{label}: 올바른 값을 입력해 주세요."),
    "js.value": ("Утга", "Value", "값"),
    "js.ob_busy": ("Төлөвлөгөө бэлдэж байна…", "Creating your plan…", "계획을 만드는 중…"),

    # ---------- Дасгал ----------
    "page.workout": ("Дасгал", "Workouts", "운동"),
    "wo.h1": ("Долоо хоногийн дасгал", "This week's workouts", "이번 주 운동"),
    "wo.sub": ("Өнөөдрийн дасгалаа бүгдийг тэмдэглэвэл coach +40 XP авна.",
               "Check off all of today's exercises and your coach gets +40 XP.",
               "오늘 운동을 모두 체크하면 코치가 +40 XP를 받아요."),
    "wo.days_aria": ("Гараг", "Days", "요일"),
    "wo.today": ("Өнөөдөр", "Today", "오늘"),
    "wo.sets": ("{sets} сет × {reps} удаа", "{sets} sets × {reps} reps", "{sets}세트 × {reps}회"),
    "wo.minutes": ("{n} минут", "{n} min", "{n}분"),
    "wo.done_aria": ("{name} хийсэн", "{name} done", "{name} 완료"),
    "wo.only_today": ("Тэмдэглэгээг тухайн өдөр нь хийнэ.", "You can check these off on the day.", "해당 요일에 체크할 수 있어요."),
    "wo.rest_sub": ("Булчин амрах үедээ томордог. Сайн унтаарай.", "Muscles grow while you rest. Sleep well.",
                    "근육은 쉴 때 자라요. 푹 주무세요."),
    "wo.change_q": ("Төлөвлөгөөгөө өөрчлөх үү?", "Want to change your plan?", "계획을 바꾸고 싶나요?"),
    "wo.change_hint": ('Дасгалжуулагчид "хөнгөлөөч", "өвдөг өвдөж байна" гэх мэтээр хэлээрэй',
                       'Tell the coach things like "make it easier" or "my knee hurts"',
                       '코치에게 "쉽게 해줘", "무릎이 아파"처럼 말해 보세요'),
    "wo.change_prompt": ("Өнөөдрийн дасгалаа солимоор байна", "I'd like to change today's workout", "오늘 운동을 바꾸고 싶어요"),
    "js.wo_all": ("Өнөөдрийн дасгал бүгд дууслаа!", "All done for today!", "오늘 운동 모두 완료!"),
    "js.wo_n": ("{n}/{all} дууслаа", "{n}/{all} done", "{n}/{all} 완료"),

    # ---------- Хоол ----------
    "page.food": ("Хоол", "Meals", "식단"),
    "fd.h1": ("Хөргөгчнөөс жор", "Recipes from your fridge", "냉장고 레시피"),
    "fd.target": ("Өдрийн зорилт", "Daily target", "하루 목표"),
    "fd.protein": ("уураг {n} г", "protein {n} g", "단백질 {n}g"),
    "fd.photo": ("Хөргөгчнийхөө зургийг авах", "Take a photo of your fridge", "냉장고 사진 찍기"),
    "fd.photo_sub": ("эсвэл зургийн сангаас сонгох (5MB хүртэл)", "or choose one from your gallery (up to 5 MB)",
                     "또는 앨범에서 선택 (최대 5MB)"),
    "fd.photo_alt": ("Сонгосон зураг", "Selected photo", "선택한 사진"),
    "fd.or_type": ("Эсвэл орцоо бичих", "Or type your ingredients", "또는 재료 입력"),
    "fd.ph": ("өндөг, тахиа, будаа, лууван", "eggs, chicken, rice, carrots", "계란, 닭고기, 밥, 당근"),
    "fd.find": ("Жор олох", "Find recipes", "레시피 찾기"),
    "fd.empty": ("Зураг эсвэл орцоо оруулахад жорууд энд гарна.", "Your recipes will appear here once you add a photo or ingredients.",
                 "사진이나 재료를 넣으면 레시피가 여기에 나타나요."),
    "fd.saved": ("Хадгалсан жорууд", "Saved recipes", "저장한 레시피"),
    "js.fd_big": ("Зураг 5MB-аас бага байх ёстой", "The photo must be under 5 MB", "사진은 5MB 이하여야 해요"),
    "js.fd_busy": ("Агент зургийг шинжилж байна…", "Your coach is looking at the photo…", "코치가 사진을 분석하는 중…"),
    "js.fd_find": ("Жор олох", "Find recipes", "레시피 찾기"),
    "js.fd_save": ("Жорыг хадгалах (+15 XP)", "Save recipe (+15 XP)", "레시피 저장 (+15 XP)"),
    "js.fd_save_title": ("Хадгалах · +15 XP", "Save · +15 XP", "저장 · +15 XP"),
    "js.kcal": ("ккал", "kcal", "kcal"),
    "js.protein_g": ("г уураг", "g protein", "g 단백질"),
    "js.min": ("мин", "min", "분"),
    "js.fd_extra": ("Нэмж авах:", "You'll also need:", "추가로 필요:"),
    "js.fd_how": ("Хийх арга", "How to make it", "만드는 법"),
    "js.fd_found": ("Олдсон орц", "Ingredients found", "찾은 재료"),
    "js.fd_demo": ("Демо горим: API түлхүүр тохируулбал зурагнаас бодит орц таньна.",
                   "Demo mode: with an API key the coach reads the real ingredients from your photo.",
                   "데모 모드: API 키를 설정하면 사진에서 실제 재료를 인식해요."),
    "js.fd_saved": ("Жорыг хадгаллаа", "Recipe saved", "레시피를 저장했어요"),

    # ---------- Явц ----------
    "page.progress": ("Явц", "Progress", "기록"),
    "pr.now": ("Одоо", "Now", "현재"),
    "pr.change": ("Өөрчлөлт", "Change", "변화"),
    "pr.weight_h": ("Жингийн өөрчлөлт", "Weight over time", "체중 변화"),
    "pr.chart_aria": ("Жингийн график", "Weight chart", "체중 그래프"),
    "pr.hint": ("Өөр өдөр дахин жингээ бүртгэхэд өөрчлөлт графикаар харагдана.",
                "Log your weight on another day to see the trend.",
                "다른 날에도 체중을 기록하면 변화가 그래프로 보여요."),
    "pr.today_label": ("Өнөөдрийн жин (кг)", "Today's weight (kg)", "오늘 체중 (kg)"),
    "pr.today_ph": ("Өнөөдрийн жин, кг", "Today's weight, kg", "오늘 체중, kg"),
    "pr.log": ("Бүртгэх", "Log weight", "기록"),
    "pr.4w": ("Сүүлийн 4 долоо хоног", "Last 4 weeks", "최근 4주"),
    "pr.days_aria": ("Дасгал хийсэн өдрүүд", "Workout days", "운동한 날"),
    "pr.n_days": ("{n} өдөр дасгал хийсэн", "{n} workout days", "{n}일 운동"),
    "js.pr_done": ("дасгал хийсэн", "worked out", "운동함"),
    "js.pr_logged": ("{kg} кг бүртгэлээ", "Logged {kg} kg", "{kg}kg 기록했어요"),

    # ---------- Профайл ----------
    "page.profile": ("Профайл", "Profile", "프로필"),
    "pf.sub": ("{goal} · {level} түвшин", "{goal} · {level}", "{goal} · {level}"),
    "pf.saved": ("Хадгаллаа.", "Saved.", "저장했어요."),
    "pf.info": ("Миний мэдээлэл", "My details", "내 정보"),
    "f.name": ("Нэр", "Name", "이름"),
    "f.height": ("Өндөр", "Height", "키"),
    "f.level": ("Түвшин", "Level", "수준"),
    "f.days": ("Өдөр / 7 хоног", "Days per week", "주당 일수"),
    "f.equipment": ("Багаж", "Equipment", "기구"),
    "pf.rebuild": ("Шинэ мэдээллээр дасгалын төлөвлөгөөг дахин гаргах", "Rebuild my workout plan from these details",
                   "이 정보로 운동 계획 다시 만들기"),
    "pf.rebuild_sub": ("Дасгалжуулагчийн хийсэн өөрчлөлтүүд арилна", "Changes your coach made will be replaced",
                       "코치가 바꾼 내용은 사라져요"),
    "pf.save": ("Хадгалах", "Save", "저장"),
    "pf.memory": ("Дасгалжуулагчийн санах ой", "Coach's memory", "코치의 기억"),
    "pf.memory_sub": ("Чатаар хэлсэн зүйлсээс агентын хадгалсан баримтууд. Хэрэггүйг нь устгаж болно.",
                      "Facts the coach saved from your chats. Delete any you don't want kept.",
                      "채팅에서 코치가 저장한 내용이에요. 필요 없는 건 지울 수 있어요."),
    "pf.delete": ("Устгах", "Delete", "삭제"),
    "pf.empty": ("Хоосон байна.", "Nothing saved yet.", "아직 없어요."),
    "pf.kcal": ("Өдрийн калори", "Daily calories", "하루 칼로리"),
    "pf.tdee": ("зарцуулалт {n}", "you burn {n}", "소모 {n}"),
    "pf.protein": ("Уураг", "Protein", "단백질"),
    "pf.disclaimer": ("Mifflin–St Jeor томьёогоор тооцсон ойролцоо утга. Эмчийн зөвлөгөөг орлохгүй.",
                      "Estimated with the Mifflin–St Jeor formula. Not a substitute for medical advice.",
                      "Mifflin–St Jeor 공식으로 계산한 추정값이에요. 의료 조언을 대신하지 않아요."),
    "pf.logout": ("Гарах", "Log out", "로그아웃"),
    "js.pf_deleted": ("Санах ойгоос устгалаа", "Removed from memory", "기억에서 삭제했어요"),

    # ---------- Чат ----------
    "page.chat": ("Дасгалжуулагч", "Coach", "코치"),
    "ch.back": ("Нүүр рүү буцах", "Back to home", "홈으로"),
    "ch.title": ("FitCoach дасгалжуулагч", "FitCoach coach", "FitCoach 코치"),
    "ch.q1": ("Өнөөдрийн дасгалаа хөнгөлөөч", "Make today's workout easier", "오늘 운동 쉽게 해줘"),
    "ch.q2": ("Жин 64.5 кг боллоо", "My weight is 64.5 kg now", "체중이 64.5kg이 됐어"),
    "ch.q3": ("Өдөрт хэдэн калори идэх вэ?", "How many calories should I eat a day?", "하루에 몇 칼로리 먹어야 해?"),
    "ch.q4": ("Энэ долоо хоногийн явц хэр байна?", "How's my progress this week?", "이번 주 진행 상황은 어때?"),
    "ch.q6": ("Зүүн өвдөг өвдөж байна", "My left knee hurts", "왼쪽 무릎이 아파"),
    "ch.msg_label": ("Мессеж", "Message", "메시지"),
    "ch.ph": ("Дасгалжуулагчаас асуух…", "Ask your coach…", "코치에게 물어보기…"),
    "ch.send": ("Илгээх", "Send", "보내기"),
    "js.ch_plan": ("Шинэчилсэн төлөвлөгөөг харах", "See the updated plan", "바뀐 계획 보기"),
    "js.ch_typing": ("Дасгалжуулагч бодож байна", "Coach is thinking", "코치가 생각 중"),
    "js.retry": ("Дахин оролдоно уу.", "Please try again.", "다시 시도해 주세요."),
    "js.net": ("Сервертэй холбогдож чадсангүй ({status})", "Couldn't reach the server ({status})", "서버에 연결할 수 없어요 ({status})"),
    "js.levelup": ("🎉 Level up! Coach одоо Level {level} ({stage})", "🎉 Level up! Your coach is now level {level} ({stage})",
                   "🎉 레벨 업! 코치가 레벨 {level}({stage})이 되었어요"),
    "js.xp": ("+{gained} XP · {reason}", "+{gained} XP · {reason}", "+{gained} XP · {reason}"),

    # ---------- Серверийн алдаа ----------
    "err.register": ("Эхлээд бүртгүүлнэ үү", "Please sign up first", "먼저 가입해 주세요"),
    "err.empty_msg": ("Мессеж хоосон байна", "The message is empty", "메시지가 비어 있어요"),
    "err.photo_big": ("Зураг 5MB-аас бага байх ёстой", "The photo must be under 5 MB", "사진은 5MB 이하여야 해요"),
    "err.photo_type": ("JPG, PNG, WEBP зураг оруулна уу", "Please upload a JPG, PNG or WEBP image", "JPG, PNG, WEBP 이미지를 올려 주세요"),
    "err.need_input": ("Зураг оруулах эсвэл орцоо бичнэ үү", "Add a photo or type your ingredients", "사진을 올리거나 재료를 입력해 주세요"),
    "err.recipe": ("Жорын мэдээлэл буруу байна", "The recipe data is invalid", "레시피 정보가 올바르지 않아요"),
    "err.weight_api": ("Жин 25–300 кг хооронд байх ёстой", "Weight must be between 25 and 300 kg", "체중은 25–300kg 사이여야 해요"),
    "err.name": ("Нэрээ оруулна уу", "Please enter your name", "이름을 입력해 주세요"),
    "err.choice": ("Сонголт буруу байна", "Invalid choice", "잘못된 선택이에요"),
    "err.ranges": ("Нас 14–80, өндөр 120–230 см, долоо хоногт 2–6 өдөр байх ёстой",
                   "Age must be 14–80, height 120–230 cm and 2–6 days a week",
                   "나이 14–80, 키 120–230cm, 주 2–6일이어야 해요"),
    "err.weight_form": ("Жин 30–250 кг хооронд байх ёстой", "Weight must be between 30 and 250 kg", "체중은 30–250kg 사이여야 해요"),

    # ---------- Агентын алхам ----------
    "step.get_user_profile": ("Профайлыг уншсан", "Read your profile", "프로필 확인"),
    "step.get_workout_plan": ("Дасгалын төлөвлөгөөг шалгасан", "Checked your workout plan", "운동 계획 확인"),
    "step.get_workout_history": ("Дасгалын түүхийг шалгасан", "Checked your workout history", "운동 기록 확인"),
    "step.get_progress": ("Жингийн явцыг шалгасан", "Checked your weight trend", "체중 변화 확인"),
    "step.update_workout_day": ("{day} гарагийн дасгалыг өөрчилсөн", "Changed {day}'s workout", "{day} 운동 변경"),
    "step.log_weight": ("Жинг бүртгэсэн: {kg} кг", "Logged weight: {kg} kg", "체중 기록: {kg}kg"),
    "step.save_memory": ("Санах ойд хадгалсан: {fact}", "Saved to memory: {fact}", "기억에 저장: {fact}"),
    "step.plan_created": ("Долоо хоногийн төлөвлөгөө үүсгэсэн", "Created your weekly plan", "주간 계획 생성"),
    "step.f_profile": ("Профайл, калорийн зорилтыг уншсан", "Read your profile and calorie target", "프로필과 칼로리 목표 확인"),
    "step.f_memory": ("Санах ой (харшил, дуршил)-г шалгасан", "Checked memory (allergies, preferences)", "기억(알레르기, 선호) 확인"),
    "step.f_photo": ("Зурагнаас орц таньсан", "Recognised ingredients in the photo", "사진에서 재료 인식"),
    "step.f_list": ("Орцын жагсаалтыг уншсан", "Read your ingredient list", "재료 목록 확인"),
    "step.f_recipes": ("{n} жор боловсруулсан", "Prepared {n} recipes", "레시피 {n}개 준비"),
    "step.f_error": ("AI алдаа ({e}) — демо хариу", "AI error ({e}), showing a demo answer", "AI 오류({e}), 데모 답변 표시"),
    "step.f_demo_photo": ("Орц таньсан (демо)", "Recognised ingredients (demo)", "재료 인식 (데모)"),
    "step.f_suggested": ("{n} жор санал болгосон", "Suggested {n} recipes", "레시피 {n}개 추천"),

    # ---------- Агентын (демо) хариу ----------
    "m.greeting": ("Сайн уу, {name}! Би чиний FitCoach. {d} өдрийн төлөвлөгөөг чинь бэлдлээ. "
                   "Дасгал солих, жингээ бүртгэх, хоолны талаар асуух бол энд бичээрэй.",
                   "Hi {name}! I'm your FitCoach. Your {d}-day plan is ready. "
                   "Write here to change exercises, log your weight or ask about food.",
                   "안녕하세요, {name}님! 저는 FitCoach예요. 주 {d}일 계획을 준비했어요. "
                   "운동 변경, 체중 기록, 식단 질문은 여기에 남겨 주세요."),
    "m.weight_logged": ("{kg} кг гэж бүртгэлээ. {trend} Ингээд тогтмол үргэлжлүүлээрэй!",
                        "Logged {kg} kg. {trend} Keep it up!", "{kg}kg으로 기록했어요. {trend} 꾸준히 이어가요!"),
    "m.trend_change": ("Эхлэлээс хойш {d} кг {dir} байна.", "That's {d} kg {dir} since you started.", "시작 이후 {d}kg {dir}했어요."),
    "m.dir_down": ("буурсан", "down", "감소"),
    "m.dir_up": ("нэмэгдсэн", "up", "증가"),
    "m.trend_first": ("Энэ бол эхний бүртгэл — цаашид өөрчлөлтийг графикаар харуулна.",
                      "This is your first entry. Future changes will show on the chart.",
                      "첫 기록이에요. 앞으로 변화가 그래프에 표시돼요."),
    "m.pain": ("Ойлголоо. Үүнийг санах ойдоо хадгаллаа, цаашид төлөвлөгөө гаргахдаа анхаарна. "
               "Өнөөдрийн ({day}) дасгалыг сунгалт, хөнгөн алхалт бүхий сэргээх өдөр болгож өөрчиллөө. "
               "Өвдөлт 2–3 хоногоос удаан үргэлжилбэл эмчид үзүүлээрэй.",
               "Got it. I saved this to memory and will plan around it. "
               "I changed today's ({day}) workout to a recovery day with stretching and an easy walk. "
               "If the pain lasts more than 2–3 days, see a doctor.",
               "알겠어요. 기억에 저장했고 앞으로 계획에 반영할게요. "
               "오늘({day}) 운동을 스트레칭과 가벼운 걷기로 된 회복일로 바꿨어요. "
               "통증이 2–3일 넘게 계속되면 병원에 가 보세요."),
    "m.harder": ("{day} гарагийн дасгал бүрт нэг сет (эсвэл 5 минут) нэмлээ. Хэт ядарвал хэлээрэй, буцааж тохируулна.",
                 "I added one set (or 5 minutes) to every exercise on {day}. Tell me if it's too much and I'll adjust it back.",
                 "{day} 운동마다 1세트(또는 5분)를 추가했어요. 너무 힘들면 말해 주세요. 다시 조정할게요."),
    "m.easier": ("{day} гарагийн дасгалыг хөнгөлж, сет бүрийг нэгээр цөөлөв. Дасгал хуудаснаас шинэчилсэн хувилбарыг харж болно.",
                 "I made {day}'s workout easier by removing one set from each exercise. See the updated plan on the Workouts page.",
                 "{day} 운동을 운동마다 1세트씩 줄여 가볍게 했어요. 운동 페이지에서 바뀐 계획을 볼 수 있어요."),
    "m.rest_today": ("Өнөөдөр ({day}) амрах өдөр байна. Хүсвэл хөнгөн сунгалт хийгээрэй.",
                     "Today ({day}) is a rest day. Some light stretching is fine if you like.",
                     "오늘({day})은 휴식일이에요. 원하면 가벼운 스트레칭을 해 보세요."),
    "m.level": ("Чиний coach одоо Level {level} ({stage}) байна, нийт {total} XP. "
                "Дараагийн level хүртэл {left} XP үлдлээ — нэг өдрийн дасгал дуусгахад +40 XP. ",
                "Your coach is level {level} ({stage}) with {total} XP in total. "
                "{left} XP to the next level, and finishing a day's workout gives +40 XP. ",
                "코치는 지금 레벨 {level}({stage})이고 총 {total} XP예요. "
                "다음 레벨까지 {left} XP 남았고, 하루 운동을 끝내면 +40 XP를 받아요. "),
    "m.streak_yes": ("{n} өдөр дараалан идэвхтэй байна, тасралтгүй үргэлжлүүлээрэй!",
                     "You've been active {n} days in a row. Keep the streak going!", "{n}일 연속 활동 중이에요. 계속 이어가요!"),
    "m.streak_no": ("Өнөөдөр нэг дасгал хийгээд streak-ээ эхлүүлье!", "Do one workout today to start a streak!",
                    "오늘 운동 하나로 연속 기록을 시작해요!"),
    "m.food": ("Таны зорилго ({goal})-д өдөрт ойролцоогоор {kcal} ккал, {p} г уураг хэрэгтэй. "
               "Хоол хуудсанд хөргөгчнийхөө зургийг оруулбал байгаа орцоор чинь жор санал болгоно.",
               "For your goal ({goal}) you need about {kcal} kcal and {p} g of protein a day. "
               "Upload a fridge photo on the Meals page and I'll suggest recipes from what you have.",
               "목표({goal})에는 하루 약 {kcal}kcal, 단백질 {p}g이 필요해요. "
               "식단 페이지에 냉장고 사진을 올리면 있는 재료로 레시피를 추천해 드려요."),
    "m.progress": ("Сүүлийн 7 хоногт {n} өдөр дасгал хийжээ. Жин эхлэлээс {ch} кг. ",
                   "You worked out on {n} of the last 7 days. Weight {ch} kg since you started. ",
                   "최근 7일 중 {n}일 운동했어요. 체중은 시작 대비 {ch}kg이에요. "),
    "m.prog_good": ("Сайн байна, хэмнэлээ хадгалаарай!", "Nice, keep the rhythm going!", "좋아요, 이 페이스를 유지해요!"),
    "m.prog_push": ("Энэ долоо хоногт дор хаяж 3 өдөр хийхийг зорьё.", "Let's aim for at least 3 days this week.",
                    "이번 주에는 최소 3일을 목표로 해요."),
    "m.today_ex": ("Өнөөдрийн дасгал ({title}): {names}. Дасгал солих, хөнгөлөх, жингээ бүртгэх, хоолны зөвлөгөө авах бол надад хэлээрэй.",
                   "Today's workout ({title}): {names}. Tell me if you want to change it, make it easier, log your weight or get food advice.",
                   "오늘 운동({title}): {names}. 운동 변경, 강도 조절, 체중 기록, 식단 조언이 필요하면 말해 주세요."),
    "m.today_rest": ("Өнөөдөр амрах өдөр. Сайн унтаж, ус сайн уугаарай. Асуух зүйл байвал хэлээрэй.",
                     "Today is a rest day. Sleep well and drink plenty of water. Ask me anything.",
                     "오늘은 휴식일이에요. 푹 자고 물을 충분히 마셔요. 궁금한 게 있으면 물어보세요."),
    "m.hello": ("Сайн уу, {name}! {msg}", "Hi {name}! {msg}", "안녕하세요, {name}님! {msg}"),
    "m.fail": ("Уучлаарай, энэ асуултыг дуусгаж чадсангүй. Арай өөрөөр асууж үзээрэй.",
               "I couldn't finish answering that. Try asking another way.",
               "이 질문에는 답을 끝내지 못했어요. 다르게 물어봐 주세요."),
    "m.ai_error": ("(AI холболтод алдаа гарсан тул демо хариу өглөө: {e})",
                   "(The AI connection failed, so this is a demo answer: {e})",
                   "(AI 연결 오류로 데모 답변을 보여드려요: {e})"),
}

# Дасгалын сангийн нэр (өгөгдлийн санд Монголоор) → (English, 한국어)
EXERCISES: dict[str, tuple[str, str]] = {
    "Түлхэлт (push-up)": ("Push-ups", "푸시업"),
    "Сандал дээр трицепс": ("Chair triceps dips", "의자 트라이셉스 딥스"),
    "Планк": ("Plank", "플랭크"),
    "Пайк түлхэлт": ("Pike push-ups", "파이크 푸시업"),
    "Суулт (squat)": ("Squats", "스쿼트"),
    "Лунж": ("Lunges", "런지"),
    "Гүүр (glute bridge)": ("Glute bridge", "글루트 브릿지"),
    "Тугалын өргөлт": ("Calf raises", "카프 레이즈"),
    "Үсрэлт (jumping jack)": ("Jumping jacks", "점핑 잭"),
    "Уулчин (mountain climber)": ("Mountain climbers", "마운틴 클라이머"),
    "Бёрпи": ("Burpees", "버피"),
    "Хурдан алхалт": ("Brisk walk", "빠르게 걷기"),
    "Гантель цээжний түлхэлт": ("Dumbbell chest press", "덤벨 체스트 프레스"),
    "Гантель мөрний түлхэлт": ("Dumbbell shoulder press", "덤벨 숄더 프레스"),
    "Нэг гартай татлага": ("One-arm row", "원암 덤벨 로우"),
    "Бицепс нугалалт": ("Biceps curl", "바이셉스 컬"),
    "Гоблет суулт": ("Goblet squat", "고블릿 스쿼트"),
    "Румын татлага": ("Romanian deadlift", "루마니안 데드리프트"),
    "Гантельтай лунж": ("Dumbbell lunges", "덤벨 런지"),
    "Гүүр": ("Glute bridge", "글루트 브릿지"),
    "Гантель свинг": ("Dumbbell swing", "덤벨 스윙"),
    "Үсрэлт": ("Jumping jacks", "점핑 잭"),
    "Уулчин": ("Mountain climbers", "마운틴 클라이머"),
    "Штанга цээжний түлхэлт": ("Barbell bench press", "바벨 벤치 프레스"),
    "Lat pulldown": ("Lat pulldown", "랫 풀다운"),
    "Мөрний түлхэлт": ("Shoulder press", "숄더 프레스"),
    "Кабель трицепс": ("Cable triceps pushdown", "케이블 트라이셉스 푸시다운"),
    "Штанга суулт": ("Barbell squat", "바벨 스쿼트"),
    "Leg press": ("Leg press", "레그 프레스"),
    "Leg curl": ("Leg curl", "레그 컬"),
    "Гүйлтийн зам": ("Treadmill", "러닝머신"),
    "Дугуй": ("Exercise bike", "실내 자전거"),
    "Гиребны машин": ("Rowing machine", "로잉 머신"),
    "Шат": ("Stair climber", "스텝밀"),
    "Сунгалт": ("Stretching", "스트레칭"),
    "Хөнгөн алхалт": ("Easy walk", "가벼운 걷기"),
}

# Өгөгдлийн санд хадгалагдсан өдрийн гарчиг → орчуулгын түлхүүр
_TITLES = {"Амрах өдөр": "focus.rest", "Сэргээх өдөр": "focus.recovery", "Шинэчилсэн дасгал": "focus.custom",
           **{v: f"focus.{k}" for k, v in planner.FOCUS_NAMES.items()}}

# Демо горимын жор
DEMO_INGREDIENTS = {
    "mn": ["Өндөг", "Тахианы мах", "Будаа", "Брокколи", "Сонгино", "Вандуй"],
    "en": ["Eggs", "Chicken", "Rice", "Broccoli", "Onion", "Peas"],
    "ko": ["계란", "닭고기", "밥", "브로콜리", "양파", "완두콩"],
}
DEMO_RECIPES = {
    "mn": [
        {"title": "Тахиатай брокколи шарсан будаа", "uses": ["Тахианы мах", "Брокколи", "Будаа", "Өндөг"],
         "extra": ["Шар буурцгийн сүмс"],
         "steps": ["Тахианы махыг жижиглэн хайруулд 6 мин шарна", "Брокколи, сонгино нэмж 3 мин хутгана",
                   "Хүйтэн будаа, өндөг нэмээд сүмсээр амтлана"],
         "why": "Уураг ихтэй, нэг таваг хоолоор өдрийн уургийн гуравны нэгийг авна."},
        {"title": "Ногоотой өндөгний омлет", "uses": ["Өндөг", "Сонгино", "Вандуй"], "extra": [],
         "steps": ["3 өндгийг давстай хольж хутгана", "Сонгино, вандуйг 2 мин шарна", "Өндгөө хийж таглаад 4 мин болгоно"],
         "why": "Хурдан, хямд, өглөөний дасгалын дараа тохиромжтой."},
    ],
    "en": [
        {"title": "Chicken and broccoli fried rice", "uses": ["Chicken", "Broccoli", "Rice", "Eggs"], "extra": ["Soy sauce"],
         "steps": ["Dice the chicken and fry it for 6 minutes", "Add the broccoli and onion and stir for 3 minutes",
                   "Add cold rice and the eggs, then season with soy sauce"],
         "why": "High in protein: one plate gives about a third of your daily protein."},
        {"title": "Vegetable omelette", "uses": ["Eggs", "Onion", "Peas"], "extra": [],
         "steps": ["Beat 3 eggs with a pinch of salt", "Fry the onion and peas for 2 minutes",
                   "Pour in the eggs, cover and cook for 4 minutes"],
         "why": "Quick and cheap, and a good fit after a morning workout."},
    ],
    "ko": [
        {"title": "닭고기 브로콜리 볶음밥", "uses": ["닭고기", "브로콜리", "밥", "계란"], "extra": ["간장"],
         "steps": ["닭고기를 작게 썰어 6분간 볶아요", "브로콜리와 양파를 넣고 3분간 볶아요", "식은 밥과 계란을 넣고 간장으로 간해요"],
         "why": "단백질이 많아 한 접시로 하루 단백질의 약 3분의 1을 채워요."},
        {"title": "채소 오믈렛", "uses": ["계란", "양파", "완두콩"], "extra": [],
         "steps": ["계란 3개에 소금을 약간 넣고 풀어요", "양파와 완두콩을 2분간 볶아요", "계란물을 붓고 뚜껑을 덮어 4분간 익혀요"],
         "why": "빠르고 저렴해서 아침 운동 후에 딱이에요."},
    ],
}


def norm(lang: str | None) -> str:
    return lang if lang in LANGS else DEFAULT


def t(key: str, lang: str = DEFAULT, **kw) -> str:
    row = STRINGS.get(key)
    if row is None:
        return key
    s = row[_I[norm(lang)]]
    return s.format(**kw) if kw else s


def from_request(request) -> str:
    """Cookie → Accept-Language → Монгол."""
    c = request.cookies.get(COOKIE)
    if c in LANGS:
        return c
    for part in request.headers.get("accept-language", "").split(","):
        code = part.split(";")[0].strip().lower()[:2]
        if code in LANGS:
            return code
    return DEFAULT


def weekday(day_mn: str, lang: str, short: bool = False) -> str:
    """Өгөгдлийн сан дахь Монгол гарагийн нэрийг орчуулна."""
    if day_mn not in planner.WEEKDAYS:
        return day_mn
    return t(("wds." if short else "wd.") + str(planner.WEEKDAYS.index(day_mn)), lang)


def day_title(day: dict, lang: str) -> str:
    focus = (day or {}).get("focus")
    if focus in ("upper", "lower", "cardio", "full", "rest"):
        return t(f"focus.{focus}", lang)
    title = (day or {}).get("title") or ""
    if not title:
        return t("focus.rest", lang)
    return t(_TITLES[title], lang) if title in _TITLES else title


def exercise(name: str, lang: str) -> str:
    lang = norm(lang)
    if lang == "mn" or name not in EXERCISES:
        return name
    return EXERCISES[name][0 if lang == "en" else 1]


def js_strings(lang: str) -> dict:
    return {k: v[_I[norm(lang)]] for k, v in STRINGS.items() if k.startswith("js.")}
