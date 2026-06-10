class TaskListNotFoundError(Exception):
    def __init__(self, task_list_id: int):
        self.task_list_id = task_list_id
        super().__init__(f"Lista de tareas con id={task_list_id} no encontrada.")


class TaskNotFoundError(Exception):
    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"Tarea con id={task_id} no encontrada.")


class UserNotFoundError(Exception):
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"Usuario con id={user_id} no encontrado.")


class EmailAlreadyExistsError(Exception):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"El email '{email}' ya está registrado.")


class InvalidCredentialsError(Exception):
    def __init__(self):
        super().__init__("Credenciales inválidas.")
