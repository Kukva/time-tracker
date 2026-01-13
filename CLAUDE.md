# Claude AI Development Guide

## Project Overview
Time Tracker CLI - простой инструмент для отслеживания времени работы над задачами.

## Technology Stack
- Python 3.11+
- Click (CLI framework)
- pytest + pytest-cov (testing)
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
2. Написать pytest тесты в tests/test_*.py
3. Запустить тесты (они должны упасть)
4. Реализовать функционал
5. Запустить тесты (они должны пройти)
6. Сделать коммит с описательным сообщением
7. Push делает пользователь вручную
```

## Running Tests
```bash
# Активировать venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Запустить тесты с покрытием
pytest tests/ -v --cov=src --cov-report=term-missing

# Целевое покрытие: >80%
```

## Git Workflow

### Commit Messages Format
```
<type>: <short description>

<detailed description if needed>
```

**Types:**
- `feat`: новая функциональность
- `test`: добавление/изменение тестов
- `fix`: исправление бага
- `refactor`: рефакторинг без изменения функциональности
- `docs`: обновление документации
- `chore`: технические изменения (зависимости, конфигурация)

### Примеры коммитов:
```
test: add tests for CSV export functionality

feat: implement CSV export with date filtering

docs: update README with export command usage
```

## Project Structure
```
time-tracker/
├── src/
│   ├── __init__.py
│   ├── tracker.py      # Основная логика и CLI команды
│   └── storage.py      # Работа с JSON хранилищем
├── tests/
│   ├── test_tracker.py # Тесты основной логики
│   └── test_storage.py # Тесты хранилища
├── requirements.txt    # Зависимости
├── setup.py           # Установка пакета
└── README.md          # Пользовательская документация
```

## Current Status

### Implemented Features
- ✅ Basic commands: start, stop, status, report
- ✅ Task name validation
- ✅ Corrupted JSON handling
- ✅ Test coverage: 84%

### In Progress (High Priority)
- 🔄 CSV export functionality
- 🔄 Weekly reports
- 🔄 Monthly reports

### Backlog
- Telegram bot integration (#10)
- SQLite migration
- CI/CD setup
- Logging framework

## Code Standards

### Python Style
- Follow PEP 8
- Use type hints where appropriate
- Docstrings for all public methods
- Clear, descriptive variable names

### Error Handling
- Graceful error handling with user-friendly messages
- Validate input at entry points
- Use emoji indicators: ✓ (success), ❌ (error), ⚠️ (warning)

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
- PowerShell doesn't support `&&`, use `;` or full paths

### Virtual Environment
- venv located in project root
- Always use: `venv\Scripts\python.exe` for commands
- Dependencies installed in venv

### Data Storage
- Location: `~/.timetracker/`
- Files:
  - `active.json` - текущая активная сессия
  - `sessions.json` - история завершенных сессий
  - `.backup` / `.corrupted` - бэкапы при ошибках

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
venv\Scripts\python.exe -m pytest tests/ -v --cov=src

# Run application
track start "task name"
track stop
track status
track report
track export -o output.csv --start-date 2026-01-01
```

## AI Assistant Guidelines

1. **Always follow TDD**: Tests first, implementation second
2. **Make atomic commits**: One feature/fix per commit
3. **Auto-push**: Push after each successful commit
4. **Update todos**: Keep TodoWrite list current
5. **Check coverage**: Maintain >80% test coverage
6. **Handle errors**: Graceful error handling for all edge cases
7. **Documentation**: Update README when adding new commands

## Related Issues

See GitHub Issues for detailed feature requests and bugs.
Priority levels marked in issue labels.
