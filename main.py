from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from database import SessionLocal, engine, Base
from models import Roll
from schemas import Roll as RollSchema, RollCreate, RollUpdate
from typing import Optional
from datetime import date, timedelta
import random
import statistics

Base.metadata.create_all(bind=engine)
app = FastAPI()


# Функция для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Ошибка базы данных: " + str(e))
    finally:
        db.close()


# Генерация случайной даты за 2024 год
def random_date_2024():
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)
    random_days = random.randint(0, (end_date - start_date).days)
    return start_date + timedelta(days=random_days)


@app.get("/", response_class=FileResponse)
async def root():
    return FileResponse("index.html")


# Создание рулона с датой добавления
@app.post("/rolls/", response_model=RollSchema)
def create_roll(roll: RollCreate, db: Session = Depends(get_db)):
    try:
        roll_date = roll.date_added if roll.date_added else random_date_2024()
        db_roll = Roll(
            length=roll.length,
            weight=roll.weight,
            date_added=roll_date
        )
        db.add(db_roll)
        db.commit()
        db.refresh(db_roll)
        return db_roll
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Ошибка при создании рулона")


# Получение списка рулонов с фильтрацией по нескольким диапазонам
@app.get("/rolls/", response_model=list[RollSchema])
def read_rolls(
        id_min: Optional[int] = Query(None, description="Минимальный ID"),
        id_max: Optional[int] = Query(None, description="Максимальный ID"),
        weight_min: Optional[float] = Query(None, description="Минимальный вес"),
        weight_max: Optional[float] = Query(None, description="Максимальный вес"),
        length_min: Optional[float] = Query(None, description="Минимальная длина"),
        length_max: Optional[float] = Query(None, description="Максимальная длина"),
        date_added_min: Optional[date] = Query(None, description="Минимальная дата добавления (YYYY-MM-DD)"),
        date_added_max: Optional[date] = Query(None, description="Максимальная дата добавления (YYYY-MM-DD)"),
        date_removed_min: Optional[date] = Query(None, description="Минимальная дата удаления (YYYY-MM-DD)"),
        date_removed_max: Optional[date] = Query(None, description="Максимальная дата удаления (YYYY-MM-DD)"),
        db: Session = Depends(get_db),
):
    try:
        query = db.query(Roll)
        if id_min is not None:
            query = query.filter(Roll.id >= id_min)
        if id_max is not None:
            query = query.filter(Roll.id <= id_max)
        if weight_min is not None:
            query = query.filter(Roll.weight >= weight_min)
        if weight_max is not None:
            query = query.filter(Roll.weight <= weight_max)
        if length_min is not None:
            query = query.filter(Roll.length >= length_min)
        if length_max is not None:
            query = query.filter(Roll.length <= length_max)
        if date_added_min is not None:
            query = query.filter(Roll.date_added >= date_added_min)
        if date_added_max is not None:
            query = query.filter(Roll.date_added <= date_added_max)
        if date_removed_min is not None:
            query = query.filter(Roll.date_removed >= date_removed_min)
        if date_removed_max is not None:
            query = query.filter(Roll.date_removed <= date_removed_max)
        query = query.order_by(Roll.id)
        rolls = query.all()
        return rolls
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Ошибка при получении данных рулонов")

# Получение статистики за указанный период
@app.get("/stats/")
def get_stats(
        start_date: date = Query(..., description="Начальная дата периода (YYYY-MM-DD)"),
        end_date: date = Query(..., description="Конечная дата периода (YYYY-MM-DD)"),
        db: Session = Depends(get_db),
):
    try:
        interval_weight = []
        interval_lenght = []
        intervals = []
        timeline = []

        # Все рулоны на складе в данный период
        rolls = db.query(Roll).filter(
            Roll.date_added <= end_date,
            or_(
                Roll.date_removed >= start_date,
                Roll.date_removed.is_(None)
            )
        ).all()
        # Добавленные рулоны
        added_rolls = db.query(Roll.date_added).filter(
            Roll.date_added >= start_date,
            Roll.date_added <= end_date
        ).all()
        # Удаленные рулоны
        removed_rolls = db.query(Roll.date_removed).filter(
            Roll.date_removed >= start_date,
            Roll.date_removed <= end_date
        ).all()

        # Расчет статистики
        for roll in rolls:
            interval_weight.append(roll.weight)
            interval_lenght.append(roll.length)
            if roll.date_added <= end_date:
                timeline.append([roll.date_added, 1, roll.weight])
            if roll.date_removed is not None and roll.date_removed <= end_date:
                timeline.append([roll.date_removed, 0, roll.weight])
            if roll.date_removed:
                if any(roll.date_removed == date_tuple[0] for date_tuple in removed_rolls) and any(
                        roll.date_added == date_tuple[0] for date_tuple in added_rolls):
                    intervals.append((roll.date_removed - roll.date_added).days)

        def sort_by_date(item):
            if item[0] is None:
                return date.max
            return item[0]

        timeline = sorted(timeline, key=sort_by_date)

        min_time = [start_date, end_date, float('inf')]
        max_time = [start_date, end_date, 1]
        min_time_weight = [start_date, end_date, float('inf')]
        max_time_weight = [start_date, end_date, 0]
        actual_counter = 0
        actual_weight = 0
        if len(timeline) > 1:
            for i in range(len(timeline)):
                if timeline[i][1] == 1:
                    actual_counter += 1
                else:
                    actual_counter -= 1
                if i != len(timeline)-1:
                    if actual_counter <= min_time[2] and timeline[i + 1][0] >= start_date:
                        min_time = [timeline[i][0], timeline[i + 1][0], actual_counter]
                    if actual_counter >= max_time[2]:
                        max_time = [timeline[i][0], timeline[i + 1][0], actual_counter]
                    if i == 0 and timeline[i][0] > start_date:
                        min_time = [start_date, timeline[i][0], 0]
                        max_time = [start_date, timeline[i][0], 0]
                else:
                    if actual_counter <= min_time[2]:
                        min_time = [timeline[i][0], end_date, actual_counter]
                    if actual_counter >= max_time[2]:
                        max_time = [timeline[i][0], end_date, actual_counter]

                if timeline[i][1] == 1:
                    actual_weight += timeline[i][2]
                else:
                    actual_weight -= timeline[i][2]
                if i != len(timeline) - 1:
                    if actual_weight <= min_time_weight[2] and timeline[i + 1][0] >= start_date:
                        min_time_weight = [timeline[i][0], timeline[i + 1][0], actual_weight]
                    if actual_weight >= max_time_weight[2]:
                        max_time_weight = [timeline[i][0], timeline[i + 1][0], actual_weight]
                    if i == 0 and timeline[i][0] > start_date:
                        min_time_weight = [start_date, timeline[i][0], 0]
                        max_time_weight = [start_date, timeline[i][0], 0]
                else:
                    if actual_weight <= min_time_weight[2]:
                        min_time_weight = [timeline[i][0], end_date, actual_weight]
                    if actual_weight >= max_time[2]:
                        max_time_weight = [timeline[i][0], end_date, actual_weight]
            if min_time[0] < start_date:
                min_time[0] = start_date
            if max_time[0] < start_date:
                max_time[0] = start_date

            if min_time_weight[0] < start_date:
                min_time_weight[0] = start_date
            if max_time_weight[0] < start_date:
                max_time_weight[0] = start_date
        else:
            raise HTTPException(status_code=400, detail="Недостаточно данных для статистики")

        min_time_description = f"дни, когда на складе находилось минимальное количество рулонов за указанный период: с {str(min_time[0])} до {str(min_time[1])}, в те дни на складе было {str(min_time[2])} рулонов"
        max_time_description = f"дни, когда на складе находилось максимальное количество рулонов за указанный период: с {str(max_time[0])} до {str(max_time[1])}, в те дни на складе было {str(max_time[2])} рулонов"
        min_time_weight_description = f"дни, когда суммарный вес рулонов на складе был минимальным в указанный период.: с {str(min_time_weight[0])} до {str(min_time_weight[1])}, в те дни на складе общий вес был {str(min_time_weight[2])}кг"
        max_time_weight_description = f"дни, когда суммарный вес рулонов на складе был максимальным в указанный период: с {str(max_time_weight[0])} до {str(max_time_weight[1])}, в те дни на складе общий вес был {str(max_time_weight[2])}кг"

        if rolls:
            avg_length = statistics.mean(interval_lenght)
            avg_weight = statistics.mean(interval_weight)
            min_weight = min(interval_weight)
            max_weight = max(interval_weight)
            min_length = min(interval_lenght)
            max_length = max(interval_lenght)
            sum_weight = sum(interval_weight)
            added = len(added_rolls)
            removed = len(removed_rolls)
            max_interval = max(intervals) if intervals else None
            min_interval = min(intervals) if intervals else None
            return JSONResponse(
                content={
                    "1)количество добавленных рулонов": added,
                    "2)количество удалённых рулонов": removed,
                    "3)средняя длина рулонов, находившихся на складе в этот период": avg_length,
                    "4)средний вес рулонов, находившихся на складе в этот период": avg_weight,
                    "5)максимальная длина рулонов, находившихся на складе в этот период": max_length,
                    "6)минимальная длина рулонов, находившихся на складе в этот период": min_length,
                    "7)максимальный вес рулонов, находившихся на складе в этот период": max_weight,
                    "8)минимальный вес рулонов, находившихся на складе в этот период": min_weight,
                    "9)суммарный вес рулонов на складе за период": sum_weight,
                    "10)максимальный промежуток между добавлением и удалением рулона": max_interval,
                    "11)минимальный промежуток между добавлением и удалением рулона": min_interval,
                    "12)": min_time_description,
                    "13)": max_time_description,
                    "14)": min_time_weight_description,
                    "15)": max_time_weight_description
                },
                media_type="application/json",
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        else:
            raise HTTPException(status_code=404, detail="Нет статистики за данный период")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Ошибка при получении статистики")


# Обновление рулона (установка даты удаления)
@app.patch("/rolls/{roll_id}", response_model=RollSchema)
def update_roll(roll_id: int, roll_update: RollUpdate, db: Session = Depends(get_db)):
    roll = db.query(Roll).filter(Roll.id == roll_id).first()
    if roll is None:
        raise HTTPException(status_code=404, detail="Рулон не найден")

    # Если дата удаления не указана, используем текущую дату
    if roll_update.date_removed and roll.date_added <= roll_update.date_removed:
        roll.date_removed = roll_update.date_removed
        db.commit()
        db.refresh(roll)
        return roll
    else:
        if not roll_update.date_removed and roll.date_added <= date.today():
            roll.date_removed = date.today()
            db.commit()
            db.refresh(roll)
            return roll
        else:
            raise HTTPException(status_code=422, detail="не корректная дата, удаление должно быть позже добавления")


# Удаление всех записей в таблице
@app.delete("/rolls/clear/", response_model=dict)
def clear_rolls(db: Session = Depends(get_db)):
    try:
        db.query(Roll).delete()
        db.commit()
        return {"message": "Все записи в таблице Roll были успешно удалены."}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при удалении записей из таблицы Roll")
