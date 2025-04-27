import os
from dotenv import load_dotenv
from todoist_api_python.models import Task

from repository import TodoistRepository, TodoistSyncRepository

load_dotenv()

TOKEN = os.getenv('TOKEN')
SYNC_URL = 'https://api.todoist.com/sync/v9/sync'


# def create_projects_by_labels(query: str, labels: list[str]) -> None:
#     repo = TodoistRepository(TOKEN)
#     tasks: list[Task] = repo.filter_tasks(query=query)

#     tasks_with_subtasks: set[str] = set(
#         t.parent_id for t in tasks if t.parent_id is not None
#     )

#     move_tasks_by_rule()



def move_tasks_by_rule(query: str, rule: dict[str, str]) -> None:
    repo = TodoistRepository(TOKEN)
    tasks: list[Task] = repo.filter_tasks(query=query)

    sync_repo = TodoistSyncRepository(TOKEN, SYNC_URL)
    for t in tasks:
        if not t.labels:
            continue

        destination = ''
        for label in rule:
            if label in t.labels:
                destination = rule[label]

        if destination:
            sync_repo.add_move_item_command(
                task_id=t.id,
                project_id=destination
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
    # create_projects_by_labels(query="#Inbox", labels=[])
