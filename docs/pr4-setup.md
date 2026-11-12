# ПР4 – перевірка у VS Code

1. Відкрийте `taskflow-cli` та у PowerShell виконайте `git fetch origin`, `git switch pr4-ontology-guardrails`, `git pull --ff-only origin pr4-ontology-guardrails`. Важливо: спочатку перевірте `git status`; якщо є незбережені зміни, не перемикайте гілку до їх збереження.
2. Запустіть `.\.venv\Scripts\python.exe -m pytest -q tests/test_guardrail_hook.py`.
3. Виберіть Copilot Chat → Open Customizations → Hooks. У Workspace має бути конфігурація `.github/hooks/taskflow-guardrails.json`.
4. Відкрийте **новий** чат. Запропонуйте Copilot виконати тестову команду `git push origin main`, не запускати її вручну. Збережіть скріншот явного `deny` із `TaskFlow B01`. Hook може не бачити деякі назви інструментів або форми даних: за відсутності блокування не вважайте перевірку успішною; перегляньте журнал Hooks та інструменту.
5. Спробуйте через Copilot змінити `src/taskflow/services.py` (без погодження фактичного запису); очікуване `ask`.
6. Перевірте дозволену дію: запуск `pytest`. Зберігайте скріншоти із реального VS Code та GitHub.
7. На GitHub: `taskflow-cli` – `pr4-ontology-guardrails`, vault – `pr4-ontology`. Не робіть прямого push у `main`.

## Скриншоти
1 – Ontology-TaskFlow та категорії; 2 – типізовані зв'язки YAML у Obsidian; 3 – guardrails allow/warn/block; 4 – зареєстрований hook; 5 – реальна відмова `deny`; 6 – реальний запит `ask`; 7 – виконані тести.

**Обмеження:** локальний Python launcher `py -3` обов'язковий для hook; перевірка у VS Code необхідна, навіть якщо локальні unit-тести проходять. Документація: https://code.visualstudio.com/docs/agent-customization/hooks.

## Якщо dry-run push не заблоковано
Це НЕ успіх B01. Спочатку перевірте `hook-debug.log` після нового сеансу Copilot (після `git pull`). Скрипт зберігає **лише назву інструмента, назви ключів аргументів і власне рішення**, без значень команд чи секретів. У PowerShell: `Get-Content .github/hooks/hook-debug.log -Tail 15`. Якщо файла немає, Copilot не викликає скрипт або не може його запустити: перевірте вибраний Session Target, виконання в локальному workspace та журнал Hooks. Якщо є рядок із рішенням `none`, надішліть назву інструмента й ключі – потрібно узгодити перевірку з реальною схемою. Перевіряйте тільки командою `git push --dry-run origin main` через Copilot, ніколи прямим push.
