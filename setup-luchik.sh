#!/usr/bin/env bash
set -euo pipefail

# Лучик — setup script
# Запускать на любой машине после клонирования репо:
#   git clone https://github.com/alexbayov/luchik.git
#   cd luchik && bash setup-luchik.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROFILE_DIR="${HERMES_HOME:-$HOME/.luchik}"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "═══════════════════════════════════════════════"
echo "  Лучик — установка"
echo "═══════════════════════════════════════════════"

# 1. Проверка Python
if ! command -v "$PYTHON_BIN" &>/dev/null; then
  echo "✗ Python не найден. Установите Python 3.12+."
  exit 1
fi

PY_VERSION="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PY_MAJOR="$("$PYTHON_BIN" -c 'import sys; print(sys.version_info.major)')"
PY_MINOR="$("$PYTHON_BIN" -c 'import sys; print(sys.version_info.minor)')"
if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 12 ]); then
  echo "✗ Нужен Python 3.12+, найден $PY_VERSION"
  echo "  Установите через uv:  uv python install 3.12"
  echo "  Или pyenv:            pyenv install 3.12"
  exit 1
fi
echo "✓ Python $PY_VERSION"

# 2. venv + install
echo "→ Создание venv в $VENV_DIR ..."
"$PYTHON_BIN" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -e "$SCRIPT_DIR" -q
echo "✓ Зависимости установлены"

# 3. Профиль
echo "→ Настройка профиля в $PROFILE_DIR ..."
mkdir -p "$PROFILE_DIR/skills"

# Копируем профильные файлы (config, SOUL, USER, MEMORY, .env.example)
for f in config.yaml SOUL.md USER.md MEMORY.md .env.example; do
  if [ -f "$SCRIPT_DIR/luchik-profile/$f" ]; then
    cp "$SCRIPT_DIR/luchik-profile/$f" "$PROFILE_DIR/$f"
  fi
done

# Копируем скилы
if [ -d "$SCRIPT_DIR/luchik-profile/skills" ]; then
  cp -r "$SCRIPT_DIR/luchik-profile/skills/"* "$PROFILE_DIR/skills/" 2>/dev/null || true
fi

# .env — создаём из примера, если нет
if [ ! -f "$PROFILE_DIR/.env" ]; then
  if [ -f "$SCRIPT_DIR/luchik-profile/.env.example" ]; then
    cp "$SCRIPT_DIR/luchik-profile/.env.example" "$PROFILE_DIR/.env"
    echo "⚠ .env создан из шаблона — заполните ключи в $PROFILE_DIR/.env"
  fi
fi

echo "✓ Профиль установлен"

# 4. Wrapper
WRAPPER_PATH="$HOME/.local/bin/luchik"
mkdir -p "$HOME/.local/bin"

cat > "$WRAPPER_PATH" << WRAPPER
#!/usr/bin/env bash
export HERMES_HOME="$PROFILE_DIR"
exec "$VENV_DIR/bin/python" "$SCRIPT_DIR/cli.py" "\$@"
WRAPPER
chmod +x "$WRAPPER_PATH"

echo "✓ Wrapper установлен: $WRAPPER_PATH"

# 5. Проверка PATH
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
  echo "⚠ $HOME/.local/bin не в PATH. Добавьте в ~/.zshrc или ~/.bashrc:"
  echo '  export PATH="$HOME/.local/bin:$PATH"'
fi

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✓ Лучик установлен!"
echo "  Запуск: luchik chat      — чат"
echo "  Запуск: luchik -g        — gateway (Telegram)"
echo "═══════════════════════════════════════════════"
