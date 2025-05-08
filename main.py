from collections.abc import Callable
import os
from collections import defaultdict
from typing import TypeVar

from dotenv import load_dotenv
from todoist_api_python.models import Section, Task

from repository import TodoistRepository, TodoistSyncRepository
from utils import find_by_id, find_by_name

TASK_LABELS_TO_MOVE = [
    "#разовая",
    "#календарь",
    "#календарь/рутина/неделя",
    "#календарь/рутина/месяц",
    "#календарь/праздник",
    "#календарь/платёж",
    "#потом/неделя",
    "#потом/месяц",
    "#потом/неясно",
]
TASKS_DESTINATION = "6XmVVx4ChwxWffFx"
PROJECTS_DESTINATION = "6XqvJwqJMgGm4QPv"


load_dotenv()

TOKEN = os.getenv("TOKEN")
SYNC_URL = "https://api.todoist.com/sync/v9/sync"

T = TypeVar("T")


class TodoistWorkflowService:
    def __init__(self, token: str, sync_url: str) -> None:
        self.token = token
        self.sync_url = sync_url
        self.repo = TodoistRepository(self.token)
        self.sync_repo = TodoistSyncRepository(self.token, self.sync_url)

    def add_label_to_tasks_by_predicate(
        self,
        query: str,
        label: str,
        predicate: Callable[[Task], bool]
    ) -> None:
        tasks: list[Task] = self.repo.filter_tasks(query=query)

        for task in tasks:
            if not predicate(task):
                continue

            if task.labels is None:
                new_labels = [label]
            elif label not in task.labels:
                new_labels = task.labels + [label]
            else:
                continue

            self.sync_repo.add_update_labels_command(task.id, new_labels)

        if self.sync_repo.commands:
            self.sync_repo.send_commands()


    @staticmethod
    def get_task_id_to_subtask_ids(tasks: list[Task]) -> dict[str, set[str]]:
        tasks_subtasks: dict[str, set[str]] = defaultdict(set)
        for t in tasks:
            if t.parent_id is not None:
                tasks_subtasks[t.parent_id].add(t.id)
        return tasks_subtasks

    def create_section_for_tasks_with_subtasks(
        self, query: str, project_id: str
    ) -> None:
        tasks: list[Task] = self.repo.filter_tasks(query=query)
        sections: list[Section] = self.repo.get_sections(project_id)

        task_id_to_subtask_ids = self.get_task_id_to_subtask_ids(tasks)

        for task_id, subtask_ids in task_id_to_subtask_ids.items():
            task = find_by_id(tasks, task_id)

            assert task is not None

            section = find_by_name(sections, task.content)
            if not section:
                section = self.repo.add_section(
                    name=task.content, project_id=project_id
                )
            print(section.name)

            for subtask_id in subtask_ids:
                self.sync_repo.add_move_item_command(
                    subtask_id, section_id=section.id
                )

        if self.sync_repo.commands:
            self.sync_repo.send_commands()

    def move_tasks_with_labels_to_project(
        self, query: str, labels: list[str], project_id: str
    ) -> None:
        tasks: list[Task] = self.repo.filter_tasks(query=query)

        for t in tasks:
            if not t.labels:
                continue

            if t.parent_id is not None:
                continue

            if not any(label in t.labels for label in labels):
                continue

            self.sync_repo.add_move_item_command(
                task_id=t.id, project_id=project_id
            )

        if self.sync_repo.commands:
            self.sync_repo.send_commands()


def main() -> None:
    if not TOKEN:
        print("TOKEN отсутствует!")
        return

    todoist = TodoistWorkflowService(TOKEN, SYNC_URL)

    todoist.add_label_to_tasks_by_predicate(
        query='#Inbox',
        label='#календарь',
        predicate=lambda task: task.due is not None
    )
    todoist.move_tasks_with_labels_to_project(
        query="#Inbox",
        labels=TASK_LABELS_TO_MOVE,
        project_id=TASKS_DESTINATION
    )
    todoist.create_section_for_tasks_with_subtasks(
        query="#Inbox",
        project_id=PROJECTS_DESTINATION
    )


if __name__ == "__main__":
    main()
