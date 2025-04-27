from collections import defaultdict
import os
from typing import Callable, Sequence, TypeVar
from dotenv import load_dotenv
from todoist_api_python.models import Task, Project

from repository import TodoistRepository, TodoistSyncRepository

load_dotenv()

TOKEN = os.getenv('TOKEN')
SYNC_URL = 'https://api.todoist.com/sync/v9/sync'

T = TypeVar('T')


def find_by_predicate(
    items: Sequence[T],
    predicate: Callable[..., bool]
) -> T | None:
    return next((item for item in items if predicate(item)), None)


def find_by_id(items: Sequence[T], id: int) -> T | None:
    return find_by_predicate(items, lambda x: x.id == id)


def find_by_name(items: Sequence[T], name: str) -> T | None:
    return find_by_predicate(items, lambda x: x.name == name)


def create_projects_by_labels(query: str) -> None:
    repo = TodoistRepository(TOKEN)
    tasks: list[Task] = repo.filter_tasks(query=query)
    projects: list[Project] = repo.get_projects()

    task_id_to_subtask_ids = get_task_id_to_subtask_ids(tasks)

    sync_repo = TodoistSyncRepository(TOKEN, SYNC_URL)
    for t_id, subt_ids in task_id_to_subtask_ids.items():
        project_name = find_by_id(tasks, t_id).content

        project = find_by_name(projects, project_name)
        if not project:
            project = repo.add_project(project_name)

        for subt_id in subt_ids:
            sync_repo.add_move_item_command(subt_id, project_id=project.id)
        sync_repo.send_commands()


def get_task_id_to_subtask_ids(tasks: list[Task]) -> defaultdict[str, set[str]]:
    tasks_subtasks: dict[str, set[str]] = defaultdict(set)
    for t in tasks:
        if t.parent_id is not None:
            tasks_subtasks[t.parent_id].add(t.id)
    return tasks_subtasks


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
    create_projects_by_labels(query="#Inbox")
