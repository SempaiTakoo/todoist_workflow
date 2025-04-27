import os
from dotenv import load_dotenv
from todoist_api_python.models import Task

from repository import TodoistRepository, TodoistSyncRepository

load_dotenv()

TOKEN = os.getenv('TOKEN')
SYNC_URL = 'https://api.todoist.com/sync/v9/sync'


def move_tasks_by_rule(query: str, rule: dict[str, str]) -> None:
    repo = TodoistRepository(TOKEN)
    tasks: list[Task] = repo.filter_tasks(query=query)

    sync_repo = TodoistSyncRepository(TOKEN, SYNC_URL)
    for t in tasks:
        if not t.labels:
            continue
        label = filter(lambda label: label in t.labels, rule)
        sync_repo.add_move_item_command(
            task_id=t.id,
            project_id=rule[label]
        )
    sync_repo.send_commands()


if __name__ == "__main__":
    labels_to_project_ids = {
        "#разовая": "6XmVVx4ChwxWffFx",
        "#календарь": "6XmVVx4ChwxWffFx",
        "#календарь/рутина/неделя": "6XmVVx4ChwxWffFx",
        "#календарь/рутина/месяц": "6XmVVx4ChwxWffFx",
        "#календарь/праздник": "6XmVVx4ChwxWffFx",
        "#календарь/платёж": "6XmVVx4ChwxWffFx",
        "#потом/неделя": "6XmVVx4ChwxWffFx",
        "#потом/месяц": "6XmVVx4ChwxWffFx",
        "#потом/неясно": "6XmVVx4ChwxWffFx",
    }
    move_tasks_by_rule(query="#Inbox", rule=labels_to_project_ids)
