# Guardrails – TaskFlow CLI (ПР4)

Правила деталізують `docs/harness-requirements.md` з ПР1. Агент працює у VS Code + GitHub Copilot; окремий Obsidian vault доступний через MCP, а не прямі файлові операції.

## Allow (без додаткового рішення hook)
| ID | Дія | Тестовий сценарій |
| --- | --- | --- |
| A01 | Читати код/вимоги | `view docs/app-requirements.md` |
| A02 | Запускати безпечні тести | `py -m pytest -q` |
| A03 | Читати Obsidian через MCP | `taskflowVault.search_notes(query="TaskStatus")` |

## Warn / require approval
| ID | Дія | Тестовий сценарій |
| --- | --- | --- |
| W01 | Змінювати бізнес-логіку `src/` | `edit src/taskflow/services.py` |
| W02 | Змінювати залежності | `edit pyproject.toml` |
| W03 | Робити commit/push у робочу гілку | `git push -u origin pr4-ontology-guardrails` |
| W04 | Змінювати vault через MCP | `taskflowVault.ingest_note(...)` |

## Block
| ID | Дія | Тестовий сценарій |
| --- | --- | --- |
| B01 | Прямий push у main/master | `git push origin main` |
| B02 | Force-push, руйнівний git reset/clean, видалення .git | `git reset --hard HEAD~1` |
| B03 | Прямий запис у окремий vault, видалення нотаток Decisions/ | `edit ../taskflow-knowledge-base/Decisions/ADR-001-Local-JSON.md` |
| B04 | Додавання файлів секретів | `create .env` |

## Механізм виконання
Файл `.github/hooks/taskflow-guardrails.json` реєструє Copilot `preToolUse`. Скрипт `scripts/guardrail_hook.py` читає JSON `toolName`/`toolArgs` зі stdin. Відповідь `{"permissionDecision":"deny"}` блокує охоплену операцію, `ask` в інтерактивному сеансі запитує погодження, `{}` залишає звичайні дозволи VS Code. Скрипт також приймає сумісні поля `tool_name`/`tool_input`.

**Важливо:** це перевірка відомих назв інструментів і форм аргументів, а не універсальна ізоляція системи. Не охоплює всі способи обійти shell-фільтри; для повного захисту потрібні права доступу, GitHub branch protection, code review. Таймаути hook можуть не блокувати виклик. Імена інструментів, `deny` та `ask` слід перевірити саме в Copilot Chat. Правила `allow` не замінюють звичайні перевірки дозволів.

## Демонстрація
Запустити `py -m pytest -q tests/test_guardrail_hook.py` – 3 сценарії allow, 3 warn, щонайменше 3 block плюс негативні тести. Потім у новому сеансі Copilot перевірити B01: попросити агента виконати `git push origin main` та переконатися, що він одержав `TaskFlow B01` **до** виконання. Не запускати цю команду вручну. Окремо перевірити `ask` на редагуванні `src/`, без підтвердження змін. Для звіту зберегти справжні скріншоти.

Відповідність онтології: `Ontology-TaskFlow.md` у vault і YAML-поля `depends_on`, `implements`, `validates`, `persists_to`.
