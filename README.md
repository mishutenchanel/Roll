# Управление рулонами

Этот проект представляет собой REST API для работы со складом рулонов металла. API построен на основе **FastAPI** и использует **PostgreSQL** для хранения данных.

## Основные функции

- Создание, чтение, обновление и удаление записей о рулонах.
- Фильтрация рулонов по различным параметрам (ID, вес, длина, дата добавления и удаления).
- Получение статистики по рулонам за указанный период.
- Очистка всей таблицы с данными.

## Технологии

- **FastAPI** — фреймворк для создания API.
- **SQLAlchemy** — ORM для работы с базой данных.
- **PostgreSQL** — реляционная база данных.
- **Docker** — контейнеризация приложения и базы данных.
- **Pydantic** — библиотека для валидации данных и работы с моделями.
- **HTML/JavaScript** — фронтенд-часть.

---
## Описание функций и работа с приложением
После запуска приложения с ним можно работать либо через веб-интерфейс по адресу *http://localhost:8000* в браузере, либо вы можете отправлять HTTP-запросы напрямую к API, используя инструменты вроде curl, Postman или любой другой HTTP-клиент.

**1) Создание записи о рулоне**

Для создания записи о рулоне необъходимо указать его длину и вес. Также можно указать дату его добавления на склад. Если дату не указывать, автоматически ставится случайный день 2024 года.
Пример:

**curl -X POST "http://localhost:8000/rolls/" \
-H "Content-Type: application/json" \
-d '{"length": 15.0, "weight": 25.5, "date_added": "2024-01-01"}'**

При создании рулона его id устанавливается автоматически. У каждого рулона свой id, даже после удаления его id не может перейти другому рулону.

**2) Получение списка рулонов с фильтрацией по нескольким диапазонам**

Для просмотра всех записей нужно отправить запрос без фильтров "**curl -X GET "http://localhost:8000/rolls/"**". Для фильрации нужно указать диапазоны. Если по одному критерию( например вес ) указать только минимальную границу, то в полученном списке будут все рулоны, у которых данный параметр больше, и наоборот.
Одновременно можно указывать любые ограничения параметров (ID, вес, длина, дата добавления и удаления).

Пример запроса с фильтрацией:

**curl -X GET "http://localhost:8000/rolls/?weight_min=10&weight_max=30&date_added_min=2024-01-01"**

**3) Просмотр статистики за выбранный диапазон**

Для получения статистики нужно ввести начальную и конечную даты диапазона.
Для анализа нужно, чтобы в выбранный период существовали рулоны.

Пример:

**curl -X GET "http://localhost:8000/stats/?start_date=2024-01-01&end_date=2024-12-31"**

**4) Удаление рулона**

Для удаления рулона со склада нужно указать его id. Также можно указать дату удаления( позже его даты добавления ). Если не указывать дату удаления, то автоматически ставится текущая дата.

Пример: 

**curl -X PATCH "http://localhost:8000/rolls/1" \
-H "Content-Type: application/json" \
-d '{"date_removed": "2024-12-31"}'**

**5) Отчистка таблицы с данными**

Можно полностью удалить все данные из таблицы. При этом, счетчик id у новых рулонов продолжится.

Пример: 

**curl -X DELETE "http://localhost:8000/rolls/clear/"**



### Требования

Установленный Docker и Docker Compose.

### Инструкция

Клонируйте репозиторий и запустите проект с помощью Docker Compose (docker-compose up --build). При запуске также автоматически проводятся тесты с помощью pytest. **Рекомендуется использовать и тестировать приложение с помощью веб-интерфейса**
