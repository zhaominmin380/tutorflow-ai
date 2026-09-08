from __future__ import annotations

import json

from app.models import Lesson, Student


class PromptService:
    summary_prompt_version = "sprint-7-summary-v1"
    feedback_prompt_version = "sprint-7-feedback-v2"

    def build_summary_prompt(self, lesson: Lesson, student: Student, raw_note: str) -> tuple[str, str]:
        prompt = f"""You are a teaching assistant. Create a factual lesson summary for a parent-facing tutoring system.
Use only the supplied information. Do not invent learning outcomes.
Student subject: {student.subject or "Not provided"}
Student grade: {student.grade or "Not provided"}
Lesson time: {lesson.start_time.isoformat()}
Lesson duration minutes: {lesson.duration_minutes}
Teacher raw note:
{raw_note}

Return JSON only with this exact shape:
{{
  "overview": "string",
  "learning_progress": ["string"],
  "strengths": ["string"],
  "difficulties": ["string"],
  "next_steps": ["string"]
}}"""
        return prompt, self.summary_prompt_version

    def build_feedback_prompt(
        self,
        lesson: Lesson,
        student: Student,
        ai_summary: dict[str, object],
        teacher_note: str | None,
    ) -> tuple[str, str]:
        summary_json = json.dumps(ai_summary, ensure_ascii=True)
        prompt = f"""Write supportive parent feedback for a tutoring lesson in Chinese.
Use only the provided lesson summary and teacher note. Do not invent facts.
Write 2–3 short paragraphs, totaling roughly 180–300 Chinese characters.
Student subject: {student.subject or "Not provided"}
Lesson time: {lesson.start_time.isoformat()}
Structured lesson summary: {summary_json}
Teacher note: {teacher_note or "None"}

Return plain text suitable for a parent."""
        return prompt, self.feedback_prompt_version
