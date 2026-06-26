#!/usr/bin/env python3
"""
Post-audit скрипт для проверки текстов по редполитике «Лучи».
Использование:
    python audit.py "текст для проверки"
    python audit.py --file путь/к/файлу.txt
    echo "текст" | python audit.py
"""

import sys
import re
import json
from pathlib import Path

# ── Словари замен ──────────────────────────────────────────────

NEGATIVE_PATTERNS = {
    "я не знаю": "Сейчас уточню и вернусь",
    "невозможно": "Рассмотрим другие варианты",
    "вы не правы": "Давайте уточним детали",
    "вы неправильно поняли": "Объясню иначе, чтобы было яснее",
    "это не наша вина": "Давайте разберёмся в ситуации",
    "читайте в договоре": "Скажу кратко, а при желании пришлю полный документ",
    "у нас проблемы с системой": "Система временно обновляется",
    "вам необходимо предоставить": "Сейчас подскажу, какие документы понадобятся",
    "подлежит урегулированию": "Разберёмся, что произошло. Расскажу по шагам",
    "изучите это в правилах": "Сейчас объясню главное простыми словами",
    "ознакомьтесь с правилами на сайте": "Расскажу коротко — вам не придётся искать самому",
    "ожидайте, с вами скоро свяжутся": "Я уже передал запрос — отвечу в ближайшее время",
    "это сложно": "Расскажу по шагам, это проще чем кажется",
    "не знаю, поймёте ли": "Сейчас объясню простыми словами",
    "успокойтесь": "Я рядом, сейчас разберёмся",
    "это ерунда": "Понимаю, что ситуация неприятная. Давайте решать",
}

CANCELLARY_PATTERNS = {
    "в соответствии с регламентом": "по правилам компании",
    "осуществить пролонгацию": "продлить договор",
    "произвести калькуляцию": "рассчитать стоимость",
    "имеет место быть": "бывает",
    "информируем вас": "сообщаем",
    "в рамках": "по",
    "надлежащим образом": "как положено",
    "вышеуказанный": "упомянутый выше",
    "настоящим уведомляем": "сообщаем",
    "осуществить": "сделать / выполнить",
    "пролонгация": "продление",
    "калькуляция": "расчёт",
}

EXCESS_BRAND_PATTERNS = [
    r"лучистого\s+\w+",
    r"сияем\b",
    r"лучи\s+добра",
    r"озарим\b",
    r"солнечные\b",
    r"на\s+крыльях\s+света",
    r"волшебный\s+момент",
    r"лучи\s+богатства",
    r"лучи\s+здоровья",
    r"полетели\b",
]

BAD_SKLONENIE = [
    r"от\s+[Лл]учей",
    r"с\s+[Лл]учами",
    r"у\s+[Лл]учи\b",
]

FORBIDDEN_TOPICS = [
    r"политик[аеиу]",
    r"военн[ыой]",
    r"конфликт",
    r"религи[яи]",
]

RED_FLAG_WORDS = [
    r"\bобязаны\b",
    r"\bдолжны\b",
    r"\bнарушили\b",
    r"понимаю\s+на\s+100%",
]


def check_text(text: str) -> dict:
    """Прогоняет текст через все проверки и возвращает отчёт."""
    text_lower = text.lower()
    findings = {"critical": [], "warning": [], "passed": []}

    # ── Негативные формулировки ──
    for pattern, replacement in NEGATIVE_PATTERNS.items():
        if pattern in text_lower:
            findings["critical"].append({
                "type": "negative",
                "found": pattern,
                "replacement": replacement,
                "reason": "Негативная формулировка"
            })

    # ── Канцелярит ──
    for pattern, replacement in CANCELLARY_PATTERNS.items():
        if pattern in text_lower:
            findings["critical"].append({
                "type": "cancellary",
                "found": pattern,
                "replacement": replacement,
                "reason": "Канцелярит / бюрократический язык"
            })

    # ── Избыточная бренд-лексика ──
    for pattern in EXCESS_BRAND_PATTERNS:
        matches = re.findall(pattern, text_lower)
        for m in matches:
            findings["critical"].append({
                "type": "excess_brand",
                "found": m if isinstance(m, str) else m[0],
                "replacement": "[удалить или заменить на сдержанную формулировку]",
                "reason": "Избыточная / неестественная бренд-лексика"
            })

    # ── Недопустимое склонение «Лучи» ──
    for pattern in BAD_SKLONENIE:
        matches = re.findall(pattern, text)
        for m in matches:
            findings["critical"].append({
                "type": "bad_sklonenie",
                "found": m if isinstance(m, str) else m[0],
                "replacement": "Использовать «Лучи» без склонения или родовое слово (компания «Лучи», онлайн-страховая «Лучи»)",
                "reason": "Склонение создаёт нежелательные ассоциации (отлучи, случи, улучи)"
            })

    # ── Запрещённые темы ──
    for pattern in FORBIDDEN_TOPICS:
        matches = re.findall(pattern, text_lower)
        for m in matches:
            findings["critical"].append({
                "type": "forbidden_topic",
                "found": m if isinstance(m, str) else m[0],
                "replacement": "[немедленно удалить]",
                "reason": "Запрещённая тема: политика, военные конфликты, религия"
            })

    # ── Красные флаги (долженствование) ──
    for pattern in RED_FLAG_WORDS:
        matches = re.findall(pattern, text_lower)
        for m in matches:
            findings["warning"].append({
                "type": "red_flag",
                "found": m if isinstance(m, str) else m[0],
                "replacement": "Переформулировать без долженствования",
                "reason": "Избыточное долженствование / давление"
            })

    # ── Подсчёт бренд-фраз (кроме избыточных) ──
    brand_phrases = re.findall(
        r"(?:проясн[ию]\w*|легк[оаи]\w*|светл[ыоа]\w*|ясн[ыоа]\w*)",
        text_lower
    )
    if len(brand_phrases) > 3:
        findings["warning"].append({
            "type": "brand_count",
            "found": f"{len(brand_phrases)} бренд-фраз: {', '.join(brand_phrases[:5])}...",
            "replacement": "Ограничить до 1 бренд-фразы на сообщение",
            "reason": "Слишком много бренд-лексики"
        })

    return findings


def format_report(text: str, findings: dict) -> str:
    """Форматирует отчёт аудита."""
    lines = []
    lines.append("=" * 60)
    lines.append("📊 ОТЧЁТ АУДИТА РЕДПОЛИТИКИ «ЛУЧИ»")
    lines.append("=" * 60)

    total_issues = len(findings["critical"]) + len(findings["warning"])

    if findings["critical"]:
        lines.append(f"\n🔴 КРИТИЧЕСКИЕ ({len(findings['critical'])}):")
        for i, item in enumerate(findings["critical"], 1):
            lines.append(f"  {i}. [{item['type']}] {item['reason']}")
            lines.append(f"     Найдено: «{item['found']}»")
            lines.append(f"     → {item['replacement']}")

    if findings["warning"]:
        lines.append(f"\n🟡 РЕКОМЕНДАЦИИ ({len(findings['warning'])}):")
        for i, item in enumerate(findings["warning"], 1):
            lines.append(f"  {i}. [{item['type']}] {item['reason']}")
            lines.append(f"     Найдено: «{item['found']}»")
            lines.append(f"     → {item['replacement']}")

    if not findings["critical"] and not findings["warning"]:
        lines.append("\n🟢 ВСЁ ЧИСТО — текст соответствует редполитике!")
        score = 10
    elif not findings["critical"]:
        lines.append(f"\n🟢 Критических проблем нет.")
        score = 7
    elif len(findings["critical"]) <= 2:
        lines.append(f"\n🟡 Есть замечания, но поправимо.")
        score = 5
    else:
        lines.append(f"\n🔴 Требуется серьёзная доработка.")
        score = 3

    lines.append(f"\n📝 ИТОГОВАЯ ОЦЕНКА: {score}/10")
    lines.append("=" * 60)

    return "\n".join(lines)


def main():
    text = ""

    if len(sys.argv) > 1:
        if sys.argv[1] == "--file" and len(sys.argv) > 2:
            path = Path(sys.argv[2])
            if path.exists():
                text = path.read_text(encoding="utf-8")
            else:
                print(f"Файл не найден: {sys.argv[2]}")
                sys.exit(1)
        else:
            text = " ".join(sys.argv[1:])
    else:
        # Читаем из stdin
        if not sys.stdin.isatty():
            text = sys.stdin.read()

    if not text.strip():
        print("Использование: python audit.py 'текст' | --file путь.txt | echo 'текст' | python audit.py")
        sys.exit(1)

    findings = check_text(text)
    report = format_report(text, findings)
    print(report)

    # Также выводим JSON для программного использования
    json_path = Path("/tmp/editorial_audit_result.json")
    json_path.write_text(json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n💾 JSON-отчёт сохранён: {json_path}")

    # Код возврата: 0 = чисто, 1 = есть критические, 2 = только предупреждения
    if findings["critical"]:
        sys.exit(1)
    elif findings["warning"]:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
