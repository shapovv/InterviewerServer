from models import Base, engine

# Создаем таблицы в базе данных
if __name__ == "__main__":
    print("Создаем таблицы...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы.")
