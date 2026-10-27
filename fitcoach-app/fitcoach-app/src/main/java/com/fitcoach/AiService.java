package com.fitcoach;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * Talks to the Claude API.
 * If ANTHROPIC_API_KEY is not set, it returns built-in demo answers so the app
 * still works for UI development without spending money.
 */
@Service
public class AiService {

    private static final String API_URL = "https://api.anthropic.com/v1/messages";
    static final ObjectMapper MAPPER = new ObjectMapper();

    private final HttpClient http = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(15))
            .build();

    @Value("${anthropic.api-key:}")
    private String apiKey;

    @Value("${anthropic.model:claude-haiku-5-5}")
    private String model;

    public boolean isLive() {
        return apiKey != null && !apiKey.isBlank();
    }

    public String model() {
        return model;
    }

    /** Sends one user message (text and/or image blocks) and returns Claude's text reply. */
    public String ask(String system, ArrayNode content, int maxTokens) throws IOException, InterruptedException {
        ObjectNode body = MAPPER.createObjectNode();
        body.put("model", model);
        body.put("max_tokens", maxTokens);
        body.put("system", system);
        ObjectNode message = body.putArray("messages").addObject();
        message.put("role", "user");
        message.set("content", content);

        HttpRequest request = HttpRequest.newBuilder(URI.create(API_URL))
                .header("x-api-key", apiKey)
                .header("anthropic-version", "2023-06-01")
                .header("content-type", "application/json")
                .timeout(Duration.ofSeconds(90))
                .POST(HttpRequest.BodyPublishers.ofString(MAPPER.writeValueAsString(body)))
                .build();

        HttpResponse<String> response = http.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() / 100 != 2) {
            throw new AiException("Claude API returned " + response.statusCode() + ": " + response.body());
        }

        StringBuilder text = new StringBuilder();
        for (JsonNode block : MAPPER.readTree(response.body()).path("content")) {
            if ("text".equals(block.path("type").asText())) {
                text.append(block.path("text").asText());
            }
        }
        return text.toString();
    }

    /** Same as ask(), but expects a JSON object back and parses it. */
    public JsonNode askJson(String system, ArrayNode content, int maxTokens) throws IOException, InterruptedException {
        String text = ask(system, content, maxTokens);
        int start = text.indexOf('{');
        int end = text.lastIndexOf('}');
        if (start < 0 || end <= start) {
            throw new AiException("AI reply was not JSON: " + text);
        }
        return MAPPER.readTree(text.substring(start, end + 1));
    }

    public static ArrayNode textContent(String text) {
        ArrayNode content = MAPPER.createArrayNode();
        content.addObject().put("type", "text").put("text", text);
        return content;
    }

    /** Thrown when the AI call fails; turned into a 502 response by ApiExceptionHandler. */
    public static class AiException extends IOException {
        public AiException(String message) {
            super(message);
        }
    }
}
