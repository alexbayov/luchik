# Лучик

Лёгкий специализированный форк [Hermes Agent](https://github.com/NousResearch/hermes-agent) для редакторской работы.

## Что это

Лучик — обрезанная сборка Hermes Agent:
- Вырезаны лишние скилы и toolsets (gaming, smart-home, discord, vision, video, image_gen, и т.д.)
- Оставлены только инструменты для редакторской работы: terminal, file, web, skills, todo, memory, session_search
- Кастомный SOUL.md — личность «Лучик»
- 10 кастомных скилов для редакторских workflow
- Запускается одной командой `luchik chat`
- Не конфликтует с основным Hermes (отдельный HERMES_HOME)

## Установка

```bash
git clone https://github.com/alexbayov/luchik.git
cd luchik
bash setup-luchik.sh
```

Скрипт:
1. Создаёт venv и устанавливает зависимости
2. Копирует профиль в `~/.hermes/` (или `$HERMES_HOME`)
3. Создаёт wrapper `~/.local/bin/luchik`
4. Создаёт `.env` из шаблона (нужно заполнить ключи)

После установки отредактируйте `~/.hermes/.env` — впишите API-ключи провайдеров.

## Запуск

```bash
luchik chat
```

## Обновление из upstream

Лучик — форк. Движок обновляется из оригинального репо, кастом не трогается:

```bash
git fetch upstream
git merge upstream/main
# luchik-profile/ не затрагивается — merge никогда не тронет
git push origin main
```

После обновления движка переустановите зависимости:

```bash
source .venv/bin/activate
pip install -e .
```

## Структура

```
luchik/
├── luchik-profile/       ← кастом Лучика (не в upstream)
│   ├── config.yaml       ← конфиг: model, providers, toolsets, personality
│   ├── SOUL.md           ← личность Лучика
│   ├── .env.example      ← шаблон ключей (без секретов)
│   ├── MEMORY.md         ← память агента
│   ├── USER.md           ← профиль пользователя
│   └── skills/           ← 10 кастомных скилов
├── setup-luchik.sh       ← установка на любой комп
├── skills/               ← upstream скилы (прореженные)
├── hermes_cli/           ← код движка (из upstream)
├── agent/                ← код движка (из upstream)
└── ...                   ← остальной код Hermes Agent
```

## Конфигурация

- **Модель:** kimi-k2.6 (провайдер kimchi)
- **Fallback:** deepseek-v4-flash (провайдер openmodel)
- **Персоналия:** luchik
- **Язык интерфейса:** ru

Ключи провайдеров хранятся в `.env` (не в git). Шаблон — `.env.example`.

## Отключённые toolsets

vision, video, image_gen, video_gen, computer_use, browser, tts, x_search, moa

## Кастомные скилы

- communication-conventions
- content-pipeline
- debugging-protocol
- fireworks-signup
- hermes-hup-workflow
- linux-dev-workflow
- prose-engine
- temp-email-coda
- webbridge-browser
- workflow-engine
