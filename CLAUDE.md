# Claude AI Development Guide

## Project Overview
Time Tracker CLI - инструмент для отслеживания времени работы над задачами с множеством интерфейсов.

## Technology Stack
- Python 3.11+
- Click (CLI framework)
- Rich (TUI dashboard)
- python-telegram-bot (Telegram интеграция)
- pytest + pytest-cov + pytest-bdd + pytest-asyncio (testing)
- JSON storage (планируется миграция на SQLite)

## Development Workflow

### TDD/BDD Approach
**ВАЖНО:** Проект следует Test-Driven Development подходу!

1. **RED**: Сначала пишем тесты (они должны падать)
2. **GREEN**: Реализуем минимальный код для прохождения тестов
3. **REFACTOR**: Улучшаем код, тесты должны проходить

### Порядок работы над фичей:
```
1. Написать BDD сценарии в features/*.feature
2. Написать step definitions в tests/test_bdd.py
3. Написать pytest тесты в tests/test_*.py
4. Запустить тесты (они должны упасть)
5. Реализовать функционал
6. Запустить тесты (они должны пройти)
7. Сделать коммит с описательным сообщением
8. Push делает пользователь вручную
```

## Running Tests
```bash
# Активировать venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Запустить тесты с покрытием
venv\Scripts\python.exe -m pytest tests/ -v --cov=src --cov-report=term-missing

# Целевое покрытие: >80%
# Текущее: 120+ тестов
```

## Git Workflow

### Commit Messages Format
```
<type>: <short description>
```

**Types:**
- `feat`: новая функциональность
- `test`: добавление/изменение тестов
- `fix`: исправление бага
- `refactor`: рефакторинг без изменения функциональности
- `docs`: обновление документации
- `chore`: технические изменения (зависимости, конфигурация)

### Важно:
- НЕ делать push автоматически - пользователь делает сам
- Спрашивать перед коммитом
- Раздельные коммиты для кода и тестов если нужно

## Project Structure
```
time-tracker/
├── src/
│   ├── __init__.py
│   ├── tracker.py      # Основная логика, CLI команды, Pomodoro
│   ├── storage.py      # Работа с JSON хранилищем
│   ├── tui.py          # Rich TUI dashboard
│   └── telegram_bot.py # Telegram бот с напоминаниями
├── tests/
│   ├── test_tracker.py # Тесты основной логики
│   ├── test_storage.py # Тесты хранилища
│   ├── test_tui.py     # Тесты TUI компонентов
│   ├── test_telegram_bot.py # Тесты Telegram бота
│   └── test_bdd.py     # BDD step definitions
├── features/
│   └── time_tracking.feature # BDD сценарии
├── requirements.txt    # Зависимости
├── setup.py           # Установка пакета
├── README.md          # Пользовательская документация
├── TODO.md            # Roadmap проекта
└── CLAUDE.md          # Этот файл
```

## Current Status

### Implemented Features
- ✅ Basic commands: start, stop, status, report
- ✅ Task name validation & error handling
- ✅ CSV export with date filtering
- ✅ Weekly & Monthly reports
- ✅ Tags/Categories for sessions
- ✅ Rich TUI Dashboard with live timer
- ✅ Telegram Bot with reminders
- ✅ Pomodoro Timer mode
- ✅ Interactive CLI mode
- ✅ Test coverage: 120+ tests

### Backlog
- CI/CD with GitHub Actions
- SQLite migration
- Desktop notifications
- Data visualization

## Code Standards

### Python Style
- Follow PEP 8
- Use type hints where appropriate
- Docstrings for all public methods
- Clear, descriptive variable names

### Error Handling
- Graceful error handling with user-friendly messages
- Validate input at entry points
- Use emoji indicators: ✓ (success), ❌ (error), ⚠️ (warning), 🍅 (pomodoro)

### Testing Standards
- Test happy path
- Test edge cases
- Test error conditions
- Test data validation
- Use descriptive test names: `test_<action>_<condition>`

## Important Notes

### Windows Environment
- Project path contains Cyrillic characters: "ДЗ"
- Use full paths in bash commands
- CMD не поддерживает `&&` через Claude - использовать отдельные команды

### Virtual Environment
- venv located in project root
- Always use: `venv\Scripts\python.exe` for commands
- Dependencies installed in venv

### Data Storage
- Location: `~/.timetracker/`
- Files:
  - `active.json` - текущая активная сессия (+ tags, pomodoro data)
  - `sessions.json` - история завершенных сессий
  - `telegram.json` - конфиг Telegram бота
  - `.backup` / `.corrupted` - бэкапы при ошибках

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
venv\Scripts\python.exe -m pytest tests/ -v --cov=src

# Basic tracking
track start "task name" --tag work
track stop
track status
track report --tag work

# Pomodoro
track pomodoro start "deep work"
track pomodoro status
track pomodoro complete
track pomodoro break

# TUI & Bot
track tui
track bot --setup
track bot

# Export
track export -o output.csv --start-date 2026-01-01 --tag client
```

## AI Assistant Guidelines

1. **Always follow TDD**: Tests first, implementation second
2. **Make atomic commits**: One feature/fix per commit
3. **NO auto-push**: Пользователь делает push сам
4. **Ask before commit**: Спрашивать перед коммитом
5. **Update todos**: Keep TodoWrite list current
6. **Check coverage**: Maintain >80% test coverage
7. **Handle errors**: Graceful error handling for all edge cases
8. **Documentation**: Update README/TODO when adding new features
9. **Separate commits**: Можно разделять код и тесты в разные коммиты

## Related Issues

See GitHub Issues for detailed feature requests and bugs.
Closed issues: #2-10, #13-15, #17-19
