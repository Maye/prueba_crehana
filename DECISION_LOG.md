# Decision Log

## 1. Gestor de paquetes: uv

Elegí `uv` porque reemplaza tres herramientas que normalmente usaría por separado (`pip`, `venv`, `pip-tools`) con una sola. La velocidad de instalación es notablemente mayor y el manejo del entorno virtual es automático. Para un proyecto nuevo en 2025 no tenía razón para no usarlo.

## 2. Base de datos: PostgreSQL con SQLAlchemy async

Quería una base de datos relacional desde el inicio porque las relaciones entre usuarios, listas y tareas son claras y bien definidas. PostgreSQL me da transacciones reales, lo cual importa cuando incremento el contador `task_count` junto con la creación de una tarea — necesito que ambas operaciones fallen o pasen juntas.

Usé SQLAlchemy 2 con async porque FastAPI corre sobre asyncio y mezclar código sincrónico de base de datos en un servidor async bloquea el event loop para todas las demás peticiones.

## 3. Arquitectura: routers → controllers → services → repositories

Opté por una estructura plana por componente en lugar de separar por capas (domain / application / infrastructure). La razón es práctica: es más fácil de navegar cuando el proyecto es pequeño. Busco `task_list.py` y encuentro el router, el servicio y el repositorio en sus carpetas respectivas, sin tener que saltar entre cuatro carpetas de capas para seguir un flujo.

La separación de responsabilidades está igual de presente — el router no toca la base de datos, el repositorio no conoce la lógica de negocio — solo que la organización prioriza el componente sobre la capa.

## 4. Pydantic v2

No consideré v1. Pydantic v2 es más rápido y `model_validate` con `from_attributes=True` me permite convertir objetos ORM a schemas de respuesta sin código extra. La única diferencia que tuve que tener en cuenta fue que `pydantic-settings` ahora es un paquete separado.

## 5. Python 3.12

Usé 3.12 porque es la versión estable más reciente y todo el stack que elegí la soporta sin problemas. No hay una razón especial más allá de no querer empezar con una versión que ya tiene sucesor disponible.

## 6. Async de punta a punta

Toda la pila es async: routers, controllers, servicios, repositorios e interfaces. No hay ninguna función que toque I/O escrita de forma sincrónica.

La razón es que FastAPI corre sobre asyncio. Si en algún punto del flujo hay una llamada sincrónica que espera I/O — una query a la base de datos, por ejemplo — ese hilo queda bloqueado y el servidor no puede atender ninguna otra petición mientras tanto. Con async, la espera libera el event loop y otras peticiones se procesan en ese tiempo.

El otro beneficio es que las interfaces de repositorio también definen sus métodos como `async`, así que cualquier implementación futura está obligada a seguir el mismo contrato. No hay forma de introducir una implementación sincrónica sin romper la interfaz.

En el servicio de listas usé `asyncio.gather` para ejecutar en paralelo la query de datos y la query de conteo total, que son independientes entre sí. Sin async eso no sería posible sin hilos.

## 7. Repositorios e interfaces

Cada entidad tiene una interfaz (`TaskListRepositoryInterface`, `TaskRepositoryInterface`, `UserRepositoryInterface`) definida con `ABC` y métodos abstractos, y una implementación concreta en SQLAlchemy que la hereda.

La razón de separarlo así es que los servicios dependen de la interfaz, no de la implementación. `TaskListService.__init__` recibe un `TaskListRepositoryInterface` — no sabe nada de SQLAlchemy, ni de sesiones, ni de cómo se ejecutan las queries. Eso me permite pasar una implementación diferente en los tests sin tocar el servicio.

La alternativa habría sido que el servicio instancie el repositorio directamente o que reciba la sesión y haga las queries él mismo. Cualquiera de las dos mezcla responsabilidades: el servicio termina sabiendo demasiado de cómo se almacenan los datos, y testear la lógica de negocio sin base de datos se vuelve complicado.

## 8. Dockerfile multistage

Separé el build en dos etapas para que la imagen final no incluya `uv` ni herramientas de compilación. El resultado es una imagen más pequeña y con menos cosas que no necesita para ejecutarse. Es un patrón estándar con Docker y no cuesta nada aplicarlo desde el principio.
