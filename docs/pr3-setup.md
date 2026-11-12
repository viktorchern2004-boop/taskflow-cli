# Практична робота №3 – MCP-конектори Obsidian та GitHub

## Що реалізовано
Власний MCP-сервер Python на stdio з інструментами `get_note`, `search_notes`, `ingest_note`. Пошук базовий лексичний (семантичний RAG буде в ПР7). `ingest_note` створює/оновлює нотатки, працює з гілкою `pr3-mcp-ingestion`, робить commit/push та не дублює однакові записи. Не перезаписує вручну створені нотатки й не пушить напряму в main.

## Підготовка Windows
1. Встанови Git, Python 3.11+ та VS Code із GitHub Copilot Chat.
2. Склонуй обидва репозиторії **поряд**, а не один всередину іншого:
   ```powershell
   mkdir "$HOME\Documents\TaskFlow" -Force
   cd "$HOME\Documents\TaskFlow"
   git clone https://github.com/viktorchern2004-boop/taskflow-cli.git
   git clone https://github.com/viktorchern2004-boop/taskflow-knowledge-base.git
   cd taskflow-cli
   git switch pr3-mcp-connectors
   py -3 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -e ".[test]"
   .\.venv\Scripts\python.exe -m pytest -q
   ```
3. Додай у змінні середовища **користувача Windows**:
   - `TASKFLOW_PYTHON` – повний шлях до `taskflow-cli\.venv\Scripts\python.exe`;
   - `TASKFLOW_VAULT_PATH` – повний шлях до **окремої** папки `taskflow-knowledge-base`;
   - `GITHUB_MCP_TOKEN` – fine-grained токен GitHub, лише для читання репозиторію `taskflow-cli` (Contents/Issues/Pull requests – Read).
4. Перезапусти VS Code, відкрий **тільки** папку `taskflow-cli` (не спільну батьківську папку й не vault).
5. `Ctrl+Shift+P` → **Chat: Open Customizations** → **MCP Servers**. Переконайся, що VS Code завантажив кореневий файл `.mcp.json`, і підключи `taskflowVault` та `githubReadOnly`. Обирай Copilot Agent, а не звичайний Ask.
6. Якщо під час першого запуску Git попросить авторизуватися, виконай вхід через офіційний Git Credential Manager. Ніколи не додавай токен у Git чи скріншоти.

## Реальні сценарії перевірки в Copilot Agent
**Retrieval 1:** «Використай інструмент taskflowVault.search_notes для пошуку нотаток про статуси задач; покажи шлях і назву знайденої нотатки».

**Retrieval 2:** «Використай taskflowVault.get_note, відкрий TaskModel та назви правила валідації».

**Ingestion:** «Виклич taskflowVault.ingest_note з title=ADR-PR3-MCP, type=decision, content="Доступ агента до Obsidian vault здійснюється лише через MCP-конектор.", links=["Task","TaskModel"]. Покажи результат інструмента».

Повтори виклик без зміни аргументів: спершу очікується `created`, потім `unchanged`. При зміні content очікується `updated`. Перевір на GitHub гілку `pr3-mcp-ingestion`, файл `Decisions/ADR-PR3-MCP.md`, коміти.

**GitHub MCP:** «Через githubReadOnly знайди 2–3 реальні коміти в viktorchern2004-boop/taskflow-cli, покажи SHA, повідомлення та змінені файли. Потім передай підтверджені дані через taskflowVault.ingest_note як 2–3 різні нотатки decision». Перевір створені файли й повтори один виклик для перевірки ідемпотентності.

## Скріншоти до звіту
1. Два окремі локальні репозиторії.
2. Доступні MCP-сервери й інструменти в Copilot.
3. Успішний виклик `search_notes` агентом.
4. Успішний виклик `get_note` агентом.
5. `ingest_note` – створено/без змін/оновлено.
6. Нова гілка та файли на GitHub vault.
7. GitHub MCP – коміти та передавання даних у vault.
8. Вивід `python -m pytest -q`.

**Важливо:** локальні unit-тести підтверджують логіку Python, але не є доказом підключення MCP-сервера в Copilot. Скріншоти мають бути реальними, із запуску на твоєму комп’ютері.

## Офіційні джерела
- https://py.sdk.modelcontextprotocol.io/
- https://code.visualstudio.com/docs/agents/reference/mcp-configuration
- https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md
