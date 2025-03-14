import pytest
from fastapi.testclient import TestClient
from main import app  # Импортируйте ваше FastAPI приложение
from database import SessionLocal, engine, Base, get_db  # Импортируйте SessionLocal, engine, Base и get_db
from sqlalchemy.orm import Session
from datetime import date
from models import Roll  # Импортируйте вашу модель Roll

# Фикстура для создания тестовой сессии базы данных
@pytest.fixture(scope="function")
def db_session():
    # Убедимся, что таблицы созданы перед тестом
    Base.metadata.drop_all(bind=engine)  # Очистка базы данных
    Base.metadata.create_all(bind=engine)  # Создание таблиц
    session = SessionLocal()

    yield session  # Возвращаем сессию для использования в тестах

    # После завершения теста откатываем транзакцию и очищаем данные
    session.rollback()
    session.close()

# Фикстура для клиента FastAPI
@pytest.fixture(scope="function")
def client(db_session: Session):
    # Переопределяем зависимость get_db в приложении
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db  # Переопределяем зависимость
    yield TestClient(app)  # Возвращаем клиент для использования в тестах

    # После завершения теста сбрасываем переопределение
    app.dependency_overrides.clear()

# Фикстура для добавления тестовых данных
@pytest.fixture(scope="function")
def add_test_data(db_session: Session):
    # Добавляем тестовые данные в базу данных
    test_rolls = [
        Roll(length=10.5, weight=20.3, date_added=date(2024, 1, 1), date_removed=date(2024, 6, 1)),
        Roll(length=15.0, weight=25.0, date_added=date(2024, 2, 1), date_removed=date(2024, 7, 1)),
        Roll(length=12.0, weight=22.0, date_added=date(2024, 3, 1), date_removed=None),
    ]

    db_session.add_all(test_rolls)
    db_session.commit()

    yield  # Тесты выполняются здесь

    # После завершения теста очищаем данные
    db_session.query(Roll).delete()
    db_session.commit()

# Тесты
def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"

def test_create_roll(client: TestClient):
    roll_data = {
        "length": 10.5,
        "weight": 20.3,
        "date_added": "2024-01-01"
    }
    response = client.post("/rolls/", json=roll_data)
    assert response.status_code == 200
    assert response.json()["length"] == 10.5
    assert response.json()["weight"] == 20.3
    assert response.json()["date_added"] == "2024-01-01"

def test_read_rolls(client: TestClient):
    response = client.get("/rolls/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_read_rolls_with_filters(client: TestClient):
    response = client.get("/rolls/?id_min=1&id_max=10&weight_min=10&weight_max=20&length_min=5&length_max=15")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_stats(client: TestClient, add_test_data):
    start_date = "2024-01-01"
    end_date = "2024-12-31"
    response = client.get(f"/stats/?start_date={start_date}&end_date={end_date}")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_update_roll(client: TestClient):
    # Сначала создаем рулон, чтобы потом его обновить
    roll_data = {
        "length": 10.5,
        "weight": 20.3,
        "date_added": "2024-01-01"
    }
    create_response = client.post("/rolls/", json=roll_data)
    roll_id = create_response.json()["id"]

    update_data = {
        "date_removed": "2024-06-01"
    }
    update_response = client.patch(f"/rolls/{roll_id}", json=update_data)
    assert update_response.status_code == 200
    assert update_response.json()["date_removed"] == "2024-06-01"

def test_update_roll_invalid_date(client: TestClient):
    # Сначала создаем рулон, чтобы потом его обновить
    roll_data = {
        "length": 10.5,
        "weight": 20.3,
        "date_added": "2024-01-01"
    }
    create_response = client.post("/rolls/", json=roll_data)
    roll_id = create_response.json()["id"]

    update_data = {
        "date_removed": "2023-12-31"  # Некорректная дата, раньше даты добавления
    }
    update_response = client.patch(f"/rolls/{roll_id}", json=update_data)
    assert update_response.status_code == 422