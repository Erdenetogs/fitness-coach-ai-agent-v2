package com.fitcoach;

import com.fasterxml.jackson.databind.JsonNode;

import java.io.IOException;
import java.io.UncheckedIOException;

/** Fixed answers used when no API key is configured (demo mode). */
final class DemoData {

    private DemoData() {
    }

    static JsonNode food() {
        return parse("""
            {
              "ingredients": ["chicken breast", "spinach", "eggs", "rice", "tomatoes", "greek yogurt"],
              "note": "Demo mode: this is sample data. Add an API key to analyse your real photo.",
              "meals": [
                {"name": "Chicken and spinach rice bowl", "calories": 520, "protein_g": 42, "minutes": 20,
                 "uses": ["chicken breast", "spinach", "rice", "tomatoes"],
                 "steps": ["Cook the rice.", "Pan-fry sliced chicken for 6-7 minutes.", "Wilt the spinach in the same pan.", "Serve over rice with chopped tomatoes."]},
                {"name": "Spinach tomato omelette", "calories": 340, "protein_g": 24, "minutes": 10,
                 "uses": ["eggs", "spinach", "tomatoes"],
                 "steps": ["Beat 3 eggs with a pinch of salt.", "Soften spinach and tomato in a pan.", "Pour in the eggs and cook until set.", "Serve with Greek yogurt on the side."]},
                {"name": "Egg fried rice with spinach", "calories": 460, "protein_g": 22, "minutes": 15,
                 "uses": ["rice", "eggs", "spinach"],
                 "steps": ["Scramble 2 eggs and set aside.", "Fry cold rice in a hot pan.", "Add spinach, then the eggs.", "Season and serve."]}
              ]
            }
            """);
    }

    static JsonNode plan(String goal, int days) {
        String[][] sessions = {
            {"Upper body", "Push-ups|3|12", "Dumbbell row|3|10", "Shoulder press|3|10", "Plank|3|40 sec"},
            {"Legs", "Squats|4|12", "Lunges|3|10 each leg", "Glute bridge|3|15", "Calf raises|3|20"},
            {"Core and cardio", "Mountain climbers|3|30 sec", "Crunches|3|15", "Jumping jacks|3|45 sec", "Side plank|2|30 sec each side"},
            {"Full body", "Burpees|3|10", "Goblet squat|3|12", "Push-ups|3|10", "Russian twists|3|20"},
            {"Mobility and light cardio", "Brisk walk|1|20 min", "Hip openers|2|10", "Cat-cow stretch|2|10", "Hamstring stretch|2|30 sec"},
            {"Upper body 2", "Incline push-ups|3|12", "Band pull-apart|3|15", "Tricep dips|3|10", "Superman hold|3|30 sec"}
        };
        StringBuilder json = new StringBuilder();
        json.append("{\"summary\":\"Demo mode: a sample ").append(days)
            .append("-day plan for the goal: ").append(goal.replace("\"", ""))
            .append(". Add an API key for a plan written by the AI coach.\",\"sessions\":[");
        for (int i = 0; i < days; i++) {
            String[] s = sessions[i % sessions.length];
            if (i > 0) json.append(',');
            json.append("{\"name\":\"").append(s[0]).append("\",\"minutes\":35,\"exercises\":[");
            for (int j = 1; j < s.length; j++) {
                String[] p = s[j].split("\\|");
                if (j > 1) json.append(',');
                json.append("{\"name\":\"").append(p[0]).append("\",\"sets\":").append(p[1])
                    .append(",\"reps\":\"").append(p[2]).append("\"}");
            }
            json.append("]}");
        }
        json.append("]}");
        return parse(json.toString());
    }

    static String chat(String message) {
        return "I'm in demo mode right now, so I can't read your message properly. "
            + "Keep going with today's plan and log your workout to earn XP! "
            + "(Add an ANTHROPIC_API_KEY on the server to talk with the real AI coach.)";
    }

    private static JsonNode parse(String json) {
        try {
            return AiService.MAPPER.readTree(json);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
