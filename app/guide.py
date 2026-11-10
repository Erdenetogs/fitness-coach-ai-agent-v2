"""Дасгалын заавар: зураг (хөдөлгөөний эхлэл → төгсгөл) + хэрхэн хийх алхмууд, 3 хэлээр.

Зураг нь файл биш — үе мөчний координатаас SVG болгож зурдаг "шугаман хүн". Ингэснээр
зураг татах, лиценз шалгах шаардлагагүй, харанхуй горимд өнгө нь өөрөө тохирно.

Шинэ дасгал нэмэх:
  1. POSES-д түлхүүр нэмж 1 эсвэл 2 байрлал өгнө (үе мөчийн координат, 120×100 талбай, шал y=88)
  2. TEXT-д алхмууд ба зөвлөгөөг (mn, en, ko) бичнэ
  3. BY_NAME-д өгөгдлийн сан дахь Монгол нэрийг тэр түлхүүртэй холбоно
"""
from markupsafe import Markup

FLOOR = 88


def _stand(dx=0, dy=0, **over):
    """Хажуугаас харсан зогсож буй хүн. over-оор үе мөчийг дарж бичнэ."""
    p = {"head": (60, 17), "sh": (60, 28), "hip": (60, 52), "knee": (62, 70), "foot": (63, 88),
         "knee2": (58, 70), "foot2": (56, 88), "elbow": (66, 40), "hand": (68, 52)}
    p = {k: (x + dx, y + dy) for k, (x, y) in p.items()}
    p.update(over)
    return p


def _wt(pose, r=4):
    """Гарт барьсан жин (гантель)."""
    return {**pose, "props": pose.get("props", []) + [("weight", *pose["hand"], r)]}


_PUSH_UP = {"head": (97, 53), "sh": (88, 58), "hip": (58, 70), "knee": (40, 78), "foot": (22, 86), "elbow": (88, 72), "hand": (88, 86)}
_SQUAT_DOWN = {"head": (66, 34), "sh": (62, 44), "hip": (50, 66), "knee": (74, 72), "foot": (60, 88), "elbow": (74, 48), "hand": (86, 46)}
_HINGE = {"head": (88, 47), "sh": (78, 50), "hip": (50, 54), "knee": (58, 70), "foot": (60, 88), "elbow": (78, 62), "hand": (78, 74)}
_LYING = {"head": (28, 64), "sh": (38, 66), "hip": (66, 66), "knee": (82, 68), "foot": (84, 88)}
_BENCH = ("rect", 22, 70, 56, 4)
_SEATED = {"head": (56, 29), "sh": (56, 40), "hip": (56, 66), "knee": (72, 66), "foot": (72, 88)}
_SEAT = ("rect", 44, 68, 22, 4)
_WALK = {"head": (62, 17), "sh": (61, 28), "hip": (60, 52), "knee": (67, 70), "foot": (72, 88), "knee2": (55, 70), "foot2": (46, 86),
         "elbow": (55, 40), "hand": (63, 48), "elbow2": (67, 40), "hand2": (61, 51)}

# Түлхүүр → [байрлал 1, байрлал 2]. Нэг л байрлалтай бол "барьж тогтох" дасгал.
POSES = {
    "pushup": [_PUSH_UP, {"head": (98, 73), "sh": (88, 76), "hip": (58, 79), "knee": (40, 82), "foot": (22, 86), "elbow": (77, 68), "hand": (88, 86)}],
    "pike": [{"head": (84, 75), "sh": (78, 66), "hip": (52, 46), "knee": (40, 67), "foot": (30, 86), "elbow": (82, 76), "hand": (86, 86)},
             {"head": (90, 82), "sh": (81, 74), "hip": (52, 48), "knee": (40, 68), "foot": (30, 86), "elbow": (72, 82), "hand": (86, 86)}],
    "dip": [{"head": (55, 27), "sh": (54, 38), "hip": (60, 60), "knee": (80, 62), "foot": (84, 88), "elbow": (52, 49), "hand": (50, 60), "props": [("rect", 28, 60, 22, 4), ("line", 30, 64, 30, 88), ("line", 48, 64, 48, 88)]},
            {"head": (57, 39), "sh": (56, 50), "hip": (62, 72), "knee": (82, 66), "foot": (86, 88), "elbow": (43, 52), "hand": (50, 60), "props": [("rect", 28, 60, 22, 4), ("line", 30, 64, 30, 88), ("line", 48, 64, 48, 88)]}],
    "plank": [{"head": (95, 61), "sh": (86, 66), "hip": (56, 72), "knee": (38, 79), "foot": (20, 86), "elbow": (86, 86), "hand": (99, 86)}],
    "squat": [_stand(), _SQUAT_DOWN],
    "goblet": [_wt(_stand(elbow=(63, 42), hand=(69, 34)), 5), _wt({**_SQUAT_DOWN, "elbow": (66, 58), "hand": (72, 50)}, 5)],
    "bsquat": [{**_stand(elbow=(66, 36), hand=(63, 27)), "props": [("weight", 57, 27, 5)]},
               {**_SQUAT_DOWN, "elbow": (68, 52), "hand": (65, 43), "props": [("weight", 59, 43, 5)]}],
    "lunge": [_stand(), {"head": (60, 27), "sh": (60, 38), "hip": (60, 62), "knee": (78, 70), "foot": (78, 88), "knee2": (50, 82), "foot2": (36, 86), "elbow": (62, 50), "hand": (63, 61)}],
    "bridge": [{"head": (22, 82), "sh": (32, 84), "hip": (62, 84), "knee": (80, 66), "foot": (90, 86), "elbow": (44, 86), "hand": (56, 86)},
               {"head": (22, 82), "sh": (32, 82), "hip": (62, 67), "knee": (82, 64), "foot": (90, 86), "elbow": (44, 86), "hand": (56, 86)}],
    "calf": [{**_stand(), "props": [("line", 63, 88, 71, 88)]},
             {**_stand(dy=-6), "props": [("line", 63, 82, 70, 88), ("line", 56, 82, 63, 88)]}],
    "jack": [{"front": True, "head": (60, 17), "sh": (60, 28), "hip": (60, 52), "knee": (57, 70), "foot": (56, 88), "knee2": (63, 70), "foot2": (64, 88),
              "elbow": (52, 40), "hand": (50, 52), "elbow2": (68, 40), "hand2": (70, 52)},
             {"front": True, "head": (60, 20), "sh": (60, 31), "hip": (60, 55), "knee": (51, 71), "foot": (43, 87), "knee2": (69, 71), "foot2": (77, 87),
              "elbow": (45, 21), "hand": (50, 7), "elbow2": (75, 21), "hand2": (70, 7)}],
    "climber": [_PUSH_UP, {**_PUSH_UP, "knee2": (72, 73), "foot2": (60, 85)}],
    "burpee": [{"head": (75, 55), "sh": (66, 62), "hip": (46, 70), "knee": (62, 72), "foot": (50, 88), "elbow": (68, 74), "hand": (70, 86)},
               {**_stand(dy=-7, elbow=(70, 13), hand=(75, 3)), "props": [("line", 50, 88, 70, 88)]}],
    "walk": [_WALK],
    "treadmill": [{**_WALK, "head": (65, 17), "sh": (63, 28), "knee": (70, 68), "foot": (74, 86), "knee2": (54, 72), "foot2": (42, 80),
                   "props": [("rect", 30, 88, 64, 3), ("line", 94, 88, 100, 50), ("line", 100, 50, 90, 50)]}],
    "stairs": [{"head": (64, 12), "sh": (63, 23), "hip": (60, 47), "knee": (72, 58), "foot": (72, 76), "knee2": (56, 68), "foot2": (50, 88),
                "elbow": (57, 35), "hand": (65, 43), "props": [("line", 62, 76, 104, 76), ("line", 62, 76, 62, 88), ("line", 84, 64, 104, 64), ("line", 84, 64, 84, 76)]}],
    "chest_press": [{**_LYING, "elbow": (38, 52), "hand": (38, 38), "props": [_BENCH, ("weight", 38, 38, 4)]},
                    {**_LYING, "elbow": (47, 72), "hand": (46, 57), "props": [_BENCH, ("weight", 46, 57, 4)]}],
    "shoulder_press": [_wt(_stand(elbow=(73, 38), hand=(72, 25))), _wt(_stand(elbow=(68, 17), hand=(69, 6)))],
    "row": [_wt({"head": (88, 48), "sh": (78, 52), "hip": (48, 58), "knee": (62, 72), "foot": (60, 88), "elbow": (78, 64), "hand": (78, 76)}),
            _wt({"head": (88, 48), "sh": (78, 52), "hip": (48, 58), "knee": (62, 72), "foot": (60, 88), "elbow": (66, 46), "hand": (75, 57)})],
    "curl": [_wt(_stand()), _wt(_stand(elbow=(65, 41), hand=(75, 31)))],
    "rdl": [_wt(_stand()), _wt(_HINGE)],
    "swing": [_wt({**_HINGE, "elbow": (70, 60), "hand": (60, 66)}, 5), _wt(_stand(elbow=(72, 30), hand=(85, 30)), 5)],
    "pulldown": [{**_SEATED, "elbow": (60, 24), "hand": (62, 10), "props": [_SEAT, ("line", 50, 10, 74, 10), ("line", 62, 10, 62, 0)]},
                 {**_SEATED, "elbow": (66, 50), "hand": (64, 36), "props": [_SEAT, ("line", 52, 36, 76, 36), ("line", 64, 36, 64, 0)]}],
    "pushdown": [{**_stand(elbow=(64, 42), hand=(74, 33)), "props": [("line", 74, 33, 78, 2)]},
                 {**_stand(elbow=(64, 42), hand=(69, 56)), "props": [("line", 69, 56, 78, 2)]}],
    "legpress": [{"head": (18, 43), "sh": (24, 52), "hip": (40, 70), "knee": (56, 52), "foot": (70, 62), "elbow": (34, 64), "hand": (42, 72), "props": [("line", 14, 46, 36, 76), ("line", 36, 76, 48, 76), ("line", 66, 50, 76, 72)]},
                 {"head": (18, 43), "sh": (24, 52), "hip": (40, 70), "knee": (63, 62), "foot": (86, 56), "elbow": (34, 64), "hand": (42, 72), "props": [("line", 14, 46, 36, 76), ("line", 36, 76, 48, 76), ("line", 82, 44, 92, 66)]}],
    "legcurl": [{"head": (22, 64), "sh": (32, 70), "hip": (62, 70), "knee": (84, 70), "foot": (104, 68), "elbow": (30, 80), "hand": (20, 80), "props": [("rect", 24, 74, 66, 4)]},
                {"head": (22, 64), "sh": (32, 70), "hip": (62, 70), "knee": (84, 70), "foot": (90, 50), "elbow": (30, 80), "hand": (20, 80), "props": [("rect", 24, 74, 66, 4)]}],
    "bike": [{"head": (66, 20), "sh": (61, 31), "hip": (48, 52), "knee": (66, 60), "foot": (62, 78), "knee2": (58, 66), "foot2": (52, 82), "elbow": (70, 42), "hand": (80, 44),
              "props": [("ring", 40, 76, 11), ("ring", 88, 76, 11), ("line", 48, 56, 46, 66), ("line", 80, 44, 86, 66)]}],
    "rower": [{"head": (56, 42), "sh": (52, 53), "hip": (46, 74), "knee": (60, 56), "foot": (78, 74), "elbow": (62, 60), "hand": (72, 62), "props": [("line", 20, 80, 100, 80), ("line", 72, 62, 96, 66)]},
              {"head": (27, 39), "sh": (29, 50), "hip": (36, 74), "knee": (57, 70), "foot": (78, 74), "elbow": (31, 64), "hand": (43, 60), "props": [("line", 20, 80, 100, 80), ("line", 43, 60, 96, 66)]}],
    "stretch": [{"head": (72, 62), "sh": (62, 66), "hip": (40, 84), "knee": (64, 85), "foot": (88, 84), "elbow": (74, 73), "hand": (86, 79), "props": [("line", 88, 84, 90, 76)]}],
}

# Түлхүүр → (алхмууд, зөвлөгөө). Мөр бүр (Монгол, English, 한국어).
TEXT = {
    "pushup": ([("Гараа мөрнөөс арай өргөн тавьж, биеэ толгойноос өсгий хүртэл шулуун барина.", "Hands a little wider than shoulders, body straight from head to heels.", "손을 어깨보다 조금 넓게 짚고 머리부터 발뒤꿈치까지 일직선을 만들어요."),
                ("Тохойгоо нугалж цээжээ шалнаас нэг алга дээр хүртэл буулгана.", "Bend your elbows and lower your chest to a hand's width above the floor.", "팔꿈치를 굽혀 가슴을 바닥에서 손바닥 하나 높이까지 내려요."),
                ("Шалыг түлхэж эхний байрлалдаа буцна.", "Push the floor away to return to the start.", "바닥을 밀어 처음 자세로 돌아와요.")],
               ("Хэцүү бол өвдгөө шалан дээр тавьж хийгээрэй.", "Too hard? Do it with your knees on the floor.", "어렵다면 무릎을 바닥에 대고 하세요.")),
    "pike": ([("Гар, хөлөө шалан дээр тавьж ташаагаа дээш өргөн урвуу V хэлбэр үүсгэнэ.", "Hands and feet on the floor, hips high in an upside-down V.", "손과 발을 바닥에 두고 엉덩이를 높이 들어 뒤집힌 V자를 만들어요."),
              ("Тохойгоо нугалж толгойн оройгоо гарын хооронд шал руу ойртуулна.", "Bend your elbows and lower the top of your head toward the floor between your hands.", "팔꿈치를 굽혀 정수리를 두 손 사이 바닥 쪽으로 내려요."),
              ("Мөрөөрөө түлхэж буцаж өргөгдөнө.", "Press back up through your shoulders.", "어깨 힘으로 밀어 올라와요.")],
             ("Ташаа өндөр байх тусам мөрөнд илүү ачаалал очно.", "The higher your hips, the more your shoulders work.", "엉덩이가 높을수록 어깨에 자극이 더 가요.")),
    "dip": ([("Тогтвортой сандлын ирмэгээс гараараа барьж, ташаагаа урагш гаргана.", "Grip the edge of a sturdy chair and slide your hips off the front.", "튼튼한 의자 모서리를 잡고 엉덩이를 앞으로 빼요."),
             ("Тохойгоо арагш чиглүүлэн 90° хүртэл нугалж биеэ буулгана.", "Lower yourself by bending your elbows straight back to about 90°.", "팔꿈치를 뒤로 향하게 90도까지 굽혀 몸을 내려요."),
             ("Гараа тэнийлгэн түлхэж өргөгдөнө.", "Push up until your arms are straight.", "팔을 펴며 밀어 올라와요.")],
            ("Сандал гулгахгүй байгааг эхлээд шалгаарай.", "Check first that the chair can't slide.", "의자가 미끄러지지 않는지 먼저 확인하세요.")),
    "plank": ([("Шуугаа шалан дээр, тохойгоо мөрний яг доор тавина.", "Forearms on the floor, elbows right under your shoulders.", "팔뚝을 바닥에 대고 팔꿈치를 어깨 바로 아래에 둬요."),
               ("Хөлөө арагш тэнийлгэж, биеэ шулуун шугам болгоно.", "Step your feet back so your body forms one straight line.", "다리를 뒤로 뻗어 몸을 일직선으로 만들어요."),
               ("Гэдэс, өгзөгөө чангалж, тайван амьсгалан барина.", "Tighten your abs and glutes, breathe calmly and hold.", "복부와 엉덩이에 힘을 주고 편하게 호흡하며 버텨요.")],
              ("Ташаа унжих юм уу хэт өргөгдөж болохгүй.", "Don't let your hips sag or pike up.", "엉덩이가 처지거나 너무 올라가지 않게 하세요.")),
    "squat": ([("Хөлөө мөрний өргөнтэй тавьж, хурууны үзүүрээ бага зэрэг гадагш харуулна.", "Feet shoulder-width apart, toes turned slightly out.", "발을 어깨너비로 벌리고 발끝을 살짝 바깥으로 향하게 해요."),
               ("Сандалд суух гэж байгаа мэт ташаагаа арагш явуулж, гуя шалтай зэрэгцэх хүртэл сууна.", "Sit your hips back as if onto a chair until your thighs are level with the floor.", "의자에 앉듯 엉덩이를 뒤로 빼며 허벅지가 바닥과 평행할 때까지 앉아요."),
               ("Өсгийгөөрөө шалыг түлхэж босно.", "Push through your heels to stand up.", "발뒤꿈치로 바닥을 밀며 일어나요.")],
              ("Өвдөг хурууны үзүүрийн чиглэлд явна, дотогш унагаж болохгүй.", "Knees track over your toes; don't let them cave in.", "무릎은 발끝 방향으로, 안쪽으로 모이지 않게 하세요.")),
    "goblet": ([("Гантелийг хоёр гараараа цээжний өмнө босоо барина.", "Hold one dumbbell upright against your chest with both hands.", "덤벨 하나를 두 손으로 가슴 앞에 세워 잡아요."),
                ("Цээжээ өргөсөн чигээр ташаагаа арагш явуулж сууна.", "Keeping your chest up, sit your hips back and down.", "가슴을 편 채 엉덩이를 뒤로 빼며 앉아요."),
                ("Өсгийгөөрөө түлхэж босно.", "Drive through your heels to stand.", "발뒤꿈치로 밀며 일어나요.")],
               ("Тохой өвдөгний дотор талд орж ирвэл гүн нь зөв.", "Depth is right when your elbows reach inside your knees.", "팔꿈치가 무릎 안쪽에 닿으면 깊이가 알맞아요.")),
    "bsquat": ([("Штангыг хүзүүн дээр биш, мөрний дээд булчин дээр тавьж чанга барина.", "Rest the bar on your upper-back muscles, not your neck, and grip it firmly.", "바벨을 목이 아닌 등 위쪽 근육에 올리고 단단히 잡아요."),
                ("Амьсгаа аваад гэдсээ чангалж, гуя шалтай зэрэгцэх хүртэл сууна.", "Breathe in, brace your core and squat until your thighs are level.", "숨을 들이마시고 복부에 힘을 준 뒤 허벅지가 평행할 때까지 앉아요."),
                ("Нуруугаа шулуун байлгаж өсгийгөөрөө түлхэж босно.", "Keep your back straight and drive up through your heels.", "등을 곧게 유지하고 발뒤꿈치로 밀며 일어나요.")],
               ("Хүнд жинд хамгаалалтын тулгуур эсвэл туслах хүнтэй хийгээрэй.", "For heavy sets use safety bars or a spotter.", "무거운 중량은 안전바나 보조자와 함께 하세요.")),
    "lunge": ([("Шулуун зогсоод нэг хөлөөрөө урагш том алхана.", "Stand tall and take a big step forward with one leg.", "똑바로 서서 한 발을 크게 앞으로 내디뎌요."),
               ("Хоёр өвдгөө 90° хүртэл нугалж, арын өвдгөө шалд ойртуулна.", "Bend both knees to about 90°, back knee close to the floor.", "양 무릎을 90도로 굽혀 뒤쪽 무릎을 바닥 가까이 내려요."),
               ("Урд хөлөөрөө түлхэж буцаад, хөлөө солино.", "Push off the front foot to return, then switch legs.", "앞발로 밀어 돌아온 뒤 다리를 바꿔요.")],
              ("Их биеэ босоо байлгаж, урд өвдөг хурууны үзүүрээс бүү хэтрүүл.", "Keep your torso upright and your front knee behind your toes.", "상체를 세우고 앞 무릎이 발끝을 넘지 않게 하세요.")),
    "bridge": ([("Нуруугаараа хэвтэж өвдгөө нугалан, тавхайгаа шалан дээр тавина.", "Lie on your back with knees bent and feet flat on the floor.", "등을 대고 누워 무릎을 세우고 발바닥을 바닥에 붙여요."),
                ("Өсгийгөөрөө түлхэж ташаагаа мөр, өвдөгтэй нэг шугамд ортол өргөнө.", "Push through your heels and lift your hips until shoulders, hips and knees line up.", "발뒤꿈치로 밀어 어깨, 엉덩이, 무릎이 일직선이 될 때까지 엉덩이를 들어요."),
                ("Дээр нь өгзөгөө 1 секунд чангалаад аажуухан буулгана.", "Squeeze your glutes for a second at the top, then lower slowly.", "위에서 엉덩이를 1초 조인 뒤 천천히 내려요.")],
               ("Бэлхүүсээ хэт нугалахгүй, хүчийг өгзөгөөрөө гаргана.", "Don't over-arch your lower back; let your glutes do the work.", "허리를 과하게 꺾지 말고 엉덩이 힘으로 올리세요.")),
    "calf": ([("Хөлөө ташааны өргөнтэй тавьж шулуун зогсоно. Хэрэгтэй бол хананаас түшнэ.", "Stand tall, feet hip-width apart. Hold a wall for balance if needed.", "발을 골반 너비로 벌리고 똑바로 서요. 필요하면 벽을 짚어요."),
              ("Өсгийгөө аль болох өндөр өргөж, хурууны үзүүр дээрээ зогсоно.", "Rise onto the balls of your feet, lifting your heels as high as you can.", "발뒤꿈치를 최대한 높이 들어 발끝으로 서요."),
              ("1 секунд бариад аажуухан буулгана.", "Hold for a second, then lower slowly.", "1초 버틴 뒤 천천히 내려요.")],
             ("Шатны ирмэг дээр хийвэл хөдөлгөөний далайц нэмэгдэнэ.", "Doing it on a step edge gives a bigger range of motion.", "계단 끝에서 하면 가동 범위가 더 커져요.")),
    "jack": ([("Хөлөө нийлүүлж, гараа хажуудаа буулган зогсоно.", "Stand with feet together and arms at your sides.", "발을 모으고 팔을 옆에 내린 채 서요."),
              ("Үсэрч хөлөө хажуу тийш дэлгэн, гараа толгой дээрээ өргөнө.", "Jump your feet out wide while raising your arms overhead.", "점프하며 다리를 벌리고 팔을 머리 위로 올려요."),
              ("Дахин үсэрч эхний байрлалдаа буцна. Жигд хэмнэлээр үргэлжлүүлнэ.", "Jump back to the start and keep a steady rhythm.", "다시 점프해 처음 자세로 돌아오고 일정한 리듬을 유지해요.")],
             ("Хурууны үзүүр дээрээ зөөлөн бууж, өвдгөө бага зэрэг нугална.", "Land softly on the balls of your feet with knees slightly bent.", "발끝으로 부드럽게 착지하고 무릎을 살짝 굽히세요.")),
    "climber": ([("Түлхэлтийн дээд байрлалд орно: гар мөрний доор, бие шулуун.", "Start at the top of a push-up: hands under shoulders, body straight.", "푸시업 시작 자세: 손은 어깨 아래, 몸은 일직선으로 해요."),
                 ("Нэг өвдгөө цээж рүүгээ хурдан татна.", "Drive one knee quickly toward your chest.", "한쪽 무릎을 가슴 쪽으로 빠르게 당겨요."),
                 ("Гүйж байгаа мэт хөлөө ээлжлэн солино.", "Switch legs as if running in place.", "달리듯 다리를 번갈아 바꿔요.")],
                ("Ташаагаа өргөхгүй, мөрөө бугуйн дээр байлгана.", "Keep your hips down and shoulders over your wrists.", "엉덩이를 들지 말고 어깨를 손목 위에 두세요.")),
    "burpee": ([("Зогсоогоос суугаад гараа шалан дээр тавина.", "From standing, squat down and put your hands on the floor.", "선 자세에서 앉으며 손을 바닥에 짚어요."),
                ("Хөлөө арагш үсэргэн планк болж, буцаан гар руугаа үсэрнэ.", "Jump your feet back to a plank, then jump them back to your hands.", "발을 뒤로 뛰어 플랭크를 만든 뒤 다시 손 쪽으로 뛰어와요."),
                ("Босож гараа дээш өргөн үсэрнэ.", "Stand up and jump with your arms overhead.", "일어나며 팔을 위로 뻗고 점프해요.")],
               ("Өвдөг эмзэг бол үсрэхгүйгээр хөлөө нэг нэгээр нь алхуулж хийнэ.", "Sore knees? Step your feet back and forward instead of jumping.", "무릎이 불편하면 점프 대신 한 발씩 걸어서 하세요.")),
    "walk": ([("Мөрөө сулруулж, урагшаа харан шулуун алхана.", "Walk tall with relaxed shoulders, looking ahead.", "어깨에 힘을 빼고 정면을 보며 곧게 걸어요."),
              ("Тохойгоо бага зэрэг нугалж, гараа алхамтайгаа хамт савна.", "Bend your elbows a little and swing your arms with each step.", "팔꿈치를 살짝 굽히고 걸음에 맞춰 팔을 흔들어요."),
              ("Ярьж чадах ч дуулж чадахгүй хэмжээний хурдыг барина.", "Keep a pace where you can talk but couldn't sing.", "말은 할 수 있지만 노래는 못 할 정도의 속도를 유지해요.")],
             ("Өсгийгөөр бууж, хурууны үзүүрээр түлхэнэ.", "Land on your heel and push off your toes.", "발뒤꿈치로 딛고 발끝으로 밀어내세요.")),
    "treadmill": ([("Эхний 3–5 минут удаан алхаж биеэ халаана.", "Warm up with an easy walk for the first 3–5 minutes.", "처음 3–5분은 천천히 걸으며 몸을 풀어요."),
                   ("Хурдаа аажмаар нэмж, туузны дунд хэсэгт гүйнэ.", "Raise the speed gradually and run in the middle of the belt.", "속도를 조금씩 올리고 벨트 가운데에서 달려요."),
                   ("Төгсгөлд 2–3 минут удаашруулан алхаж зүрхний цохилтоо буулгана.", "Finish with 2–3 minutes of slow walking to bring your heart rate down.", "마지막 2–3분은 천천히 걸으며 심박수를 낮춰요.")],
                  ("Бариулаас бүү зуур, аюулгүйн оосрыг хувцсандаа хавчаарай.", "Don't hang on to the rails, and clip the safety key to your clothes.", "손잡이에 매달리지 말고 안전 클립을 옷에 꽂으세요.")),
    "stairs": ([("Шулуун зогсож, бариулаас зөвхөн тэнцвэрийн төлөө хөнгөн барина.", "Stand tall and hold the rails lightly, only for balance.", "곧게 서서 손잡이는 균형을 위해 가볍게만 잡아요."),
                ("Тавхайгаа бүтнээр нь гишгүүр дээр тавьж, өсгийгөөрөө түлхэнэ.", "Place your whole foot on each step and push through your heel.", "발 전체를 계단에 올리고 발뒤꿈치로 밀어요."),
                ("Жигд хэмнэлээр, урагш бөхийхгүй үргэлжлүүлнэ.", "Keep a steady rhythm without leaning forward.", "앞으로 숙이지 말고 일정한 리듬을 유지해요.")],
               ("Бариулд жингээ тулбал ачаалал багасна.", "Leaning your weight on the rails makes it easier than it should be.", "손잡이에 체중을 실으면 운동 효과가 줄어요.")),
    "chest_press": ([("Сандал (эсвэл шал) дээр хэвтэж, жинг цээжний дээр гараа тэнийлгэн барина.", "Lie on a bench (or the floor) and hold the weights above your chest with straight arms.", "벤치(또는 바닥)에 누워 팔을 펴고 중량을 가슴 위에 들어요."),
                     ("Тохойгоо биеэсээ 45° орчим зайтай нугалж, жинг цээжний түвшинд буулгана.", "Lower the weights to chest level, elbows about 45° from your body.", "팔꿈치를 몸에서 45도 정도 벌려 중량을 가슴 높이까지 내려요."),
                     ("Амьсгаагаа гаргаж дээш түлхэнэ.", "Breathe out and press back up.", "숨을 내쉬며 위로 밀어 올려요.")],
                    ("Далаа хооронд нь ойртуулж, тавхайгаа шалан дээр бат тавина.", "Pinch your shoulder blades together and keep your feet planted.", "견갑골을 모으고 발을 바닥에 단단히 붙이세요.")),
    "shoulder_press": ([("Жинг мөрний түвшинд, алгаа урагш харуулан барина.", "Hold the weights at shoulder height, palms facing forward.", "중량을 어깨 높이에서 손바닥이 앞을 보게 잡아요."),
                        ("Гараа тэнийтэл толгой дээгүүрээ шууд дээш түлхэнэ.", "Press straight overhead until your arms are extended.", "팔이 펴질 때까지 머리 위로 곧게 밀어 올려요."),
                        ("Мөрний түвшин хүртэл аажуухан буулгана.", "Lower slowly back to shoulder height.", "어깨 높이까지 천천히 내려요.")],
                       ("Бэлхүүсээ бүү нугал. Гэдэс, өгзөгөө чангална.", "Don't arch your lower back; tighten your abs and glutes.", "허리를 꺾지 말고 복부와 엉덩이에 힘을 주세요.")),
    "row": ([("Нэг гараараа сандал түшиж, нуруугаа шалтай бараг зэрэгцүүлэн бөхийнө.", "Lean on a bench with one hand, back nearly level with the floor.", "한 손으로 벤치를 짚고 등이 바닥과 거의 평행이 되게 숙여요."),
             ("Гантелийг тохойгоо биедээ ойр байлган ташаа руугаа татна.", "Pull the dumbbell toward your hip, elbow close to your body.", "팔꿈치를 몸에 붙인 채 덤벨을 골반 쪽으로 당겨요."),
             ("Аажуухан буулгаад, давталтаа дуусгаж гараа солино.", "Lower slowly, finish your reps, then switch arms.", "천천히 내리고 반복을 마친 뒤 팔을 바꿔요.")],
            ("Мөрөөрөө биш, далны булчингаараа татаж байгаагаа мэдрээрэй.", "Feel your back doing the pull, not your shoulder shrugging.", "어깨가 아니라 등 근육으로 당기는 느낌을 찾으세요.")),
    "curl": ([("Гантелийг алгаа урагш харуулан барьж, тохойгоо хавирганд наан зогсоно.", "Stand holding dumbbells, palms forward, elbows by your ribs.", "덤벨을 손바닥이 앞을 보게 잡고 팔꿈치를 옆구리에 붙이고 서요."),
              ("Тохойгоо хөдөлгөлгүйгээр жинг мөр рүүгээ нугална.", "Curl the weights toward your shoulders without moving your elbows.", "팔꿈치를 고정한 채 덤벨을 어깨 쪽으로 들어 올려요."),
              ("Аажуухан буулгана.", "Lower slowly.", "천천히 내려요.")],
             ("Биеэ савлуулж өргөж байвал жин хүндэдсэн байна.", "If you have to swing your body, the weight is too heavy.", "몸을 흔들어야 올라간다면 중량이 너무 무거운 거예요.")),
    "rdl": ([("Жинг гуяны өмнө барьж, өвдгөө бага зэрэг нугалан зогсоно.", "Stand holding the weights in front of your thighs, knees slightly bent.", "중량을 허벅지 앞에 들고 무릎을 살짝 굽혀 서요."),
             ("Нуруугаа шулуун байлган ташаагаа арагш түлхэж, жинг шилбэний дунд хүртэл буулгана.", "Push your hips back with a flat back and lower the weights to mid-shin.", "등을 편 채 엉덩이를 뒤로 밀며 중량을 정강이 중간까지 내려요."),
             ("Өгзөгөө чангалж ташаагаа урагш түлхэн босно.", "Squeeze your glutes and drive your hips forward to stand.", "엉덩이를 조이며 골반을 앞으로 밀어 일어나요.")],
            ("Жин хөлд ойр явна. Нуруу бөгтийж эхэлбэл тэндээ зогсоно.", "Keep the weights close to your legs and stop if your back starts to round.", "중량을 다리에 가깝게 유지하고 등이 굽기 시작하면 멈추세요.")),
    "swing": ([("Хөлөө мөрнөөс өргөн тавьж, гантелийг хоёр гараараа барина.", "Feet wider than shoulders, one dumbbell held in both hands.", "발을 어깨보다 넓게 벌리고 덤벨 하나를 두 손으로 잡아요."),
               ("Нуруугаа шулуун байлган ташаагаараа бөхийж, жинг хөлийн хооронд арагш савна.", "Hinge at your hips with a flat back and swing the weight back between your legs.", "등을 편 채 골반을 접으며 덤벨을 다리 사이 뒤로 보내요."),
               ("Ташаагаа огцом урагш түлхэж, жинг цээжний түвшин хүртэл савна.", "Snap your hips forward to swing the weight up to chest height.", "골반을 힘차게 앞으로 밀어 덤벨을 가슴 높이까지 올려요.")],
              ("Хүч гарнаас биш, ташаанаас гарна.", "The power comes from your hips, not your arms.", "힘은 팔이 아니라 골반에서 나와요.")),
    "pulldown": ([("Суугаад гуяа дэрний доор бэхэлж, бариулыг мөрнөөс өргөн барина.", "Sit with your thighs under the pads and grip the bar wider than your shoulders.", "앉아서 허벅지를 패드 아래 고정하고 바를 어깨보다 넓게 잡아요."),
                  ("Цээжээ өргөж, тохойгоо доош татан бариулыг цээжний дээд хэсэг рүү татна.", "Lift your chest and pull the bar to your upper chest, driving your elbows down.", "가슴을 펴고 팔꿈치를 아래로 당겨 바를 가슴 윗부분까지 내려요."),
                  ("Гараа тэнийтэл аажуухан буцаана.", "Return slowly until your arms are straight.", "팔이 펴질 때까지 천천히 돌려보내요.")],
                 ("Хойш хэт налж, биеэрээ татаж болохгүй.", "Don't lean far back and use your bodyweight to pull.", "몸을 뒤로 크게 젖혀 반동으로 당기지 마세요.")),
    "pushdown": ([("Кабелийн өмнө зогсож, бариулыг тохойгоо хавирганд наан барина.", "Face the cable and hold the handle with your elbows tucked to your ribs.", "케이블 앞에 서서 팔꿈치를 옆구리에 붙이고 손잡이를 잡아요."),
                  ("Тохойгоо хөдөлгөлгүйгээр гараа тэнийтэл доош түлхэнэ.", "Push down until your arms are straight, elbows staying put.", "팔꿈치를 고정한 채 팔이 펴질 때까지 아래로 밀어요."),
                  ("Шуу шалтай зэрэгцэх хүртэл аажуухан буцаана.", "Return slowly until your forearms are level with the floor.", "팔뚝이 바닥과 평행이 될 때까지 천천히 올려요.")],
                 ("Мөр, их бие хөдөлгөөнгүй — зөвхөн шуу хөдөлнө.", "Shoulders and torso stay still; only your forearms move.", "어깨와 상체는 고정하고 팔뚝만 움직이세요.")),
    "legpress": ([("Суудалд нуруугаа бүтэн наан сууж, хөлөө тавцан дээр мөрний өргөнтэй тавина.", "Sit with your back flat against the pad, feet shoulder-width on the platform.", "등을 패드에 완전히 붙이고 앉아 발을 어깨너비로 발판에 올려요."),
                  ("Түгжээг суллаж, өвдгөө 90° хүртэл нугалан тавцанг буулгана.", "Release the safety and lower the platform until your knees reach about 90°.", "안전장치를 풀고 무릎이 90도가 될 때까지 발판을 내려요."),
                  ("Өсгийгөөрөө түлхэж хөлөө бараг тэнийтэл түлхэнэ.", "Push through your heels until your legs are almost straight.", "발뒤꿈치로 밀어 다리가 거의 펴질 때까지 올려요.")],
                 ("Өвдгөө бүрэн түгжиж болохгүй, ууц суудлаас бүү хөндий.", "Never lock your knees, and keep your hips on the seat.", "무릎을 완전히 잠그지 말고 엉덩이가 시트에서 뜨지 않게 하세요.")),
    "legcurl": ([("Түрүүлгээ харан хэвтэж, дэрийг шагайны яг дээр байрлуулна.", "Lie face down with the pad just above your ankles.", "엎드려 누워 패드를 발목 바로 위에 둬요."),
                 ("Ташаагаа суудалд наасан чигээр өсгийгөө өгзөг рүүгээ татна.", "Keeping your hips down, curl your heels toward your glutes.", "골반을 붙인 채 발뒤꿈치를 엉덩이 쪽으로 당겨요."),
                 ("Аажуухан буцааж тэнийлгэнэ.", "Lower slowly back to straight.", "천천히 다시 펴요.")],
                ("Буулгах хэсгийг 2–3 секундээр удаан хийвэл үр дүнтэй.", "Taking 2–3 seconds on the way down makes it more effective.", "내릴 때 2–3초에 걸쳐 천천히 하면 효과가 커요.")),
    "bike": ([("Суудлын өндрийг тааруулна: дөрөө доор байхад өвдөг бага зэрэг нугалагдсан байна.", "Set the seat so your knee is slightly bent at the bottom of the pedal stroke.", "페달이 가장 아래일 때 무릎이 살짝 굽도록 안장 높이를 맞춰요."),
              ("Эхний 3 минут хөнгөн эсэргүүцэлтэй жийж халаана.", "Pedal with light resistance for 3 minutes to warm up.", "처음 3분은 가벼운 저항으로 페달을 밟아 몸을 풀어요."),
              ("Эсэргүүцлээ нэмж, жигд хэмнэлээр үргэлжлүүлнэ.", "Add resistance and keep a steady rhythm.", "저항을 올리고 일정한 리듬을 유지해요.")],
             ("Мөрөө сулруулж, бариулыг хэт чанга бүү атга.", "Relax your shoulders and don't grip the bars too hard.", "어깨에 힘을 빼고 손잡이를 너무 세게 쥐지 마세요.")),
    "rower": ([("Хөлөө оосорлож, өвдгөө нугалан урагш бөхийж бариулыг барина.", "Strap your feet in, bend your knees and reach forward to take the handle.", "발을 고정하고 무릎을 굽혀 앞으로 숙이며 손잡이를 잡아요."),
               ("Эхлээд хөлөөрөө түлхэж, дараа нь биеэ хойш налуулж, эцэст нь бариулыг хавирга руугаа татна.", "Push with your legs first, then lean back, then pull the handle to your ribs.", "먼저 다리로 밀고, 상체를 뒤로 기울인 다음, 손잡이를 갈비뼈 쪽으로 당겨요."),
               ("Урвуу дарааллаар буцна: гар → их бие → хөл.", "Return in reverse order: arms, body, then legs.", "반대 순서로 돌아와요: 팔 → 상체 → 다리.")],
              ("Хүчний ихэнх нь хөлөөс гарна. Нуруугаа бүү бөгтийлгө.", "Most of the power comes from your legs. Don't round your back.", "힘의 대부분은 다리에서 나와요. 등을 굽히지 마세요.")),
    "stretch": ([("Булчин дулаацсан үед (дасгалын дараа) хийнэ.", "Stretch when your muscles are warm, after the workout.", "근육이 따뜻할 때(운동 후) 해요."),
                 ("Булчин зөөлөн татагдахыг мэдэртэл аажуухан сунгана. Өвдөх ёсгүй.", "Ease into each stretch until you feel a gentle pull, never pain.", "부드럽게 당기는 느낌이 들 때까지 천천히 늘려요. 아프면 안 돼요."),
                 ("Байрлал бүрийг 20–30 секунд, тайван амьсгалан барина.", "Hold each position for 20–30 seconds, breathing calmly.", "자세마다 20–30초씩 편하게 호흡하며 유지해요.")],
                ("Огцом хөдөлж, түлхэж сунгаж болохгүй.", "Don't bounce or force the stretch.", "반동을 주거나 억지로 늘리지 마세요.")),
}

# Өгөгдлийн сан дахь (Монгол) нэр → зааврын түлхүүр
BY_NAME = {
    "Түлхэлт (push-up)": "pushup", "Сандал дээр трицепс": "dip", "Планк": "plank", "Пайк түлхэлт": "pike",
    "Суулт (squat)": "squat", "Лунж": "lunge", "Гантельтай лунж": "lunge", "Гүүр (glute bridge)": "bridge", "Гүүр": "bridge",
    "Тугалын өргөлт": "calf", "Үсрэлт (jumping jack)": "jack", "Үсрэлт": "jack",
    "Уулчин (mountain climber)": "climber", "Уулчин": "climber", "Бёрпи": "burpee",
    "Хурдан алхалт": "walk", "Хөнгөн алхалт": "walk",
    "Гантель цээжний түлхэлт": "chest_press", "Штанга цээжний түлхэлт": "chest_press",
    "Гантель мөрний түлхэлт": "shoulder_press", "Мөрний түлхэлт": "shoulder_press",
    "Нэг гартай татлага": "row", "Бицепс нугалалт": "curl", "Гоблет суулт": "goblet", "Штанга суулт": "bsquat",
    "Румын татлага": "rdl", "Гантель свинг": "swing", "Lat pulldown": "pulldown", "Кабель трицепс": "pushdown",
    "Leg press": "legpress", "Leg curl": "legcurl", "Гүйлтийн зам": "treadmill", "Дугуй": "bike",
    "Гиребны машин": "rower", "Шат": "stairs", "Сунгалт": "stretch",
}

_LANG = {"mn": 0, "en": 1, "ko": 2}


def _line(a, b, cls=""):
    return f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}"{cls}/>'


def _figure(p: dict) -> str:
    """Нэг байрлалыг 120×100 талбайд зурна."""
    out = [f'<line class="floor" x1="6" y1="{FLOOR + 3}" x2="114" y2="{FLOOR + 3}" stroke-width="2"/>']
    for kind, *a in p.get("props", []):
        if kind == "line":
            out.append(f'<line class="prop" x1="{a[0]}" y1="{a[1]}" x2="{a[2]}" y2="{a[3]}" stroke-width="2.5"/>')
        elif kind == "rect":
            out.append(f'<rect class="prop" x="{a[0]}" y="{a[1]}" width="{a[2]}" height="{a[3]}" rx="2" fill="none" stroke-width="2"/>')
        elif kind == "ring":
            out.append(f'<circle class="prop" cx="{a[0]}" cy="{a[1]}" r="{a[2]}" fill="none" stroke-width="2"/>')
    back = "" if p.get("front") else ' opacity=".4"'   # хажуугаас харахад цаад талын гар, хөл бүдэг
    if "knee2" in p:
        out.append(f'<g{back}>{_line(p["hip"], p["knee2"])}{_line(p["knee2"], p["foot2"])}</g>')
    if "elbow2" in p:
        out.append(f'<g{back}>{_line(p["sh"], p["elbow2"])}{_line(p["elbow2"], p["hand2"])}</g>')
    out += [_line(p["sh"], p["hip"]), _line(p["hip"], p["knee"]), _line(p["knee"], p["foot"]),
            _line(p["sh"], p["elbow"]), _line(p["elbow"], p["hand"]),
            f'<circle cx="{p["head"][0]}" cy="{p["head"][1]}" r="7.5" fill="currentColor" stroke="none"/>']
    for kind, *a in p.get("props", []):
        if kind == "weight":
            out.append(f'<circle class="weight" cx="{a[0]}" cy="{a[1]}" r="{a[2]}" stroke-width="1"/>')
    return "".join(out)


def svg(key: str) -> str:
    """Зааврын зураг: 1 эсвэл 2 байрлал зэрэгцээ, дунд нь сум."""
    poses = POSES[key]
    first_x = 0 if len(poses) == 2 else 70  # ганц байрлалыг голд нь — зургийн хэмжээ бүх дасгалд ижил
    parts = ['<svg class="pose" viewBox="0 0 260 100" role="img" aria-hidden="true" fill="none" stroke="currentColor" '
             'stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round">',
             f'<g transform="translate({first_x} 0)">{_figure(poses[0])}</g>']
    if len(poses) == 2:
        parts.append('<path class="prop" d="M124 50h12m-4-4 4 4-4 4" stroke-width="2"/>')
        parts.append(f'<g transform="translate(140 0)">{_figure(poses[1])}</g>')
    parts.append("</svg>")
    return "".join(parts)


def get(name: str, lang: str = "mn") -> dict | None:
    """Дасгалын (Монгол) нэрээр заавар авна. Агентын шинээр зохиосон, санд байхгүй дасгалд None."""
    key = BY_NAME.get(name)
    if not key:
        return None
    i = _LANG.get(lang, 0)
    steps, tip = TEXT[key]
    return {"key": key, "svg": Markup(svg(key)), "steps": [s[i] for s in steps], "tip": tip[i], "hold": len(POSES[key]) == 1}
