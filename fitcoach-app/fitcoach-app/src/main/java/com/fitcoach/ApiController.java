package com.fitcoach;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Base64;
import java.util.Map;
import java.util.Set;

/**
 * REST API used by index.html.
 *   GET  /api/status        -> is the real AI connected?
 *   POST /api/food/analyze  -> fridge photo -> ingredients + meal ideas
 *   POST /api/workout/plan  -> goal -> weekly workout plan
 *   POST /api/coach/chat    -> short chat with the AI coach
 */
@RestController
@RequestMapping("/api")
public class ApiController {

    private static final Set<String> IMAGE_TYPES = Set.of("image/jpeg", "image/png", "image/webp", "image/gif");

    private final AiService ai;

    public ApiController(AiService ai) {
        this.ai = ai;
    }

    @GetMapping("/status")
    public Map<String, Object> status() {
        return Map.of("live", ai.isLive(), "model", ai.isLive() ? ai.model() : "demo");
    }

    // ---------------------------------------------------------------- food

    @PostMapping(value = "/food/analyze", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public JsonNode analyzeFood(@RequestParam("image") MultipartFile image,
                                @RequestParam(value = "goal", defaultValue = "stay active") String goal)
            throws IOException, InterruptedException {

        String type = image.getContentType();
        if (image.isEmpty() || type == null || !IMAGE_TYPES.contains(type)) {
            throw new IllegalArgumentException("Please upload a JPG, PNG, WEBP or GIF image.");
        }
        if (!ai.isLive()) {
            return DemoData.food();
        }

        ArrayNode content = AiService.MAPPER.createArrayNode();
        ObjectNode imageBlock = content.addObject();
        imageBlock.put("type", "image");
        ObjectNode source = imageBlock.putObject("source");
        source.put("type", "base64");
        source.put("media_type", type);
        source.put("data", Base64.getEncoder().encodeToString(image.getBytes()));

        content.addObject().put("type", "text").put("text", """
            Look at this photo of someone's fridge or food ingredients.
            The user's fitness goal is: %s

            1. List the food ingredients you can clearly see.
            2. Suggest 3 meals they can cook mostly from those ingredients, best fit for the goal first.

            Reply with ONLY this JSON, no other text:
            {
              "ingredients": ["..."],
              "note": "one short sentence from the coach about why these meals fit the goal",
              "meals": [
                {"name": "...", "calories": 0, "protein_g": 0, "minutes": 0,
                 "uses": ["ingredient", "..."], "steps": ["short step", "..."]}
              ]
            }
            If there is no food in the photo, return "ingredients": [] and "meals": [] and explain in "note".
            """.formatted(clean(goal)));

        return ai.askJson(SYSTEM_COACH, content, 1500);
    }

    // ------------------------------------------------------------- workout

    public record PlanRequest(String goal, Integer daysPerWeek, String fitnessLevel) {
    }

    @PostMapping("/workout/plan")
    public JsonNode workoutPlan(@RequestBody PlanRequest req) throws IOException, InterruptedException {
        String goal = clean(req.goal() == null ? "stay active" : req.goal());
        int days = req.daysPerWeek() == null ? 3 : Math.max(2, Math.min(6, req.daysPerWeek()));
        String fitnessLevel = clean(req.fitnessLevel() == null ? "beginner" : req.fitnessLevel());

        if (!ai.isLive()) {
            return DemoData.plan(goal, days);
        }

        String prompt = """
            Make a weekly home workout plan with exactly %d sessions.
            Goal: %s. Fitness level: %s. Equipment: body weight and light dumbbells only.
            Each session 25-45 minutes, 4-5 exercises.

            Reply with ONLY this JSON, no other text:
            {
              "summary": "one or two sentences explaining the plan",
              "sessions": [
                {"name": "Upper body", "minutes": 35,
                 "exercises": [{"name": "Push-ups", "sets": 3, "reps": "12"}]}
              ]
            }
            """.formatted(days, goal, fitnessLevel);

        return ai.askJson(SYSTEM_COACH, AiService.textContent(prompt), 2000);
    }

    // ---------------------------------------------------------------- chat

    public record ChatRequest(String message, String goal, Integer level, Integer streak) {
    }

    @PostMapping("/coach/chat")
    public Map<String, String> chat(@RequestBody ChatRequest req) throws IOException, InterruptedException {
        String message = req.message() == null ? "" : req.message().trim();
        if (message.isEmpty()) {
            throw new IllegalArgumentException("Message is empty.");
        }
        if (message.length() > 600) {
            message = message.substring(0, 600);
        }
        if (!ai.isLive()) {
            return Map.of("reply", DemoData.chat(message));
        }

        String prompt = """
            User profile: goal = %s, coach level = %d, current streak = %d days.
            User says: %s

            Answer as their friendly fitness coach in 2-4 short sentences.
            Answer in the same language the user wrote in.
            """.formatted(
                clean(req.goal() == null ? "stay active" : req.goal()),
                req.level() == null ? 1 : req.level(),
                req.streak() == null ? 0 : req.streak(),
                message);

        return Map.of("reply", ai.ask(SYSTEM_COACH, AiService.textContent(prompt), 400).trim());
    }

    // --------------------------------------------------------------- utils

    private static final String SYSTEM_COACH = """
        You are FitCoach, a friendly and encouraging AI fitness and nutrition coach for university students.
        Give safe, practical advice. Do not give medical diagnoses; suggest seeing a doctor for pain or health problems.
        """;

    /** Keeps short user-provided labels (goal, level) to plain text. */
    private static String clean(String s) {
        String t = s.replaceAll("[^\\p{L}\\p{N} ,.\\-]", " ").trim();
        return t.length() > 60 ? t.substring(0, 60) : t;
    }
}
