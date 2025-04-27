from functools import wraps
import json
import uuid
import requests
from typing import Any, Callable, Iterator, ParamSpec, TypeVar

from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task

T = TypeVar('T')
P = ParamSpec('P')


class TodoistRepository:
    def __init__(self, token: str) -> None:
        self.api = TodoistAPI(token)

    @staticmethod
    def list_from_api(
        func: Callable[P, Iterator[list[T]]]
    ) -> Callable[P, list[T]]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> list[T]:
            res: list[T] = []
            for objects_list in func(*args, **kwargs):
                res.extend(objects_list)
            return res
        return wrapper

    @list_from_api
    def filter_tasks(
        self, *, query = None, lang = None, limit = None
    ) -> Iterator[list[Task]]:
        return self.api.filter_tasks(query=query, lang=lang, limit=limit)


class TodoistSyncRepository:
    def __init__(self, token: str, url: str) -> None:
        self.token = token
        self.url = url
        self.commands: list[dict[str, Any]] = []

    def add_move_item_command(
        self,
        task_id: str,
        parent_id: str | None = None,
        section_id: str | None = None,
        project_id: str | None = None
    ) -> dict[str, Any]:
        only_one_target: bool = (((parent_id is not None)
                                ^ (section_id is not None)
                                ^ (project_id is not None))
                                and not((project_id is not None)
                                        and (section_id is not None)
                                        and (project_id is not None)))
        if not only_one_target:
            raise ValueError(
                'Должно быть указано только одно место назначения: '
                'parent_id, section_id, project_id'
            )

        command = {
            'type': 'item_move',
            'uuid': str(uuid.uuid4()),
            'args': {'id': task_id}
        }
        if parent_id is not None:
            command['args']['parent_id'] = parent_id
        elif section_id is not None:
            command['args']['section_id'] = section_id
        elif project_id is not None:
            command['args']['project_id'] = project_id

        self.commands.append(command)

    def send_commands(self) -> requests.Response:
        headers = {'Authorization': f'Bearer {self.token}'}
        payload = {'commands': json.dumps(self.commands)}
        return requests.post(self.url, headers=headers, data=payload)
