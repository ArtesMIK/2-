# БЛОК 1: Установка и подключение библиотек
# Устанавливаем нужные библиотеки, если их нет
!pip install pandas numpy folium

# Подключаем библиотеки
import pandas as pd  # Для работы с таблицами данных
import numpy as np  # Для вычислений
from math import radians, sin, cos, sqrt  # Для формулы расстояния
import folium  # Для создания карты
from IPython.display import display, clear_output  # Для показа и обновления карты
import time  # Для задержки
import os  # Для проверки файлов

# БЛОК 2: Функция вычисления расстояния
# Считаем расстояние между двумя точками (формула Хаверсина)
def haversine(lon1, lat1, lon2, lat2):
    R = 6371000  # Радиус Земли в метрах
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])  # Переводим в радианы
    dlon = lon2 - lon1  # Разница долготы
    dlat = lat2 - lat1  # Разница широты
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2  # Часть формулы
    c = 2 * np.arcsin(sqrt(a))  # Финальный угол
    return R * c  # Расстояние в метрах

# БЛОК 3: Функция триангуляции
# Находим координаты БВС по данным от двух точек
def triangulate(lon1, lat1, lon2, lat2, r1, r2, flight_area_north=True):
    d = haversine(lon1, lat1, lon2, lat2)  # Считаем расстояние между П1 и П2
    print(f"Расстояние между П1 и П2 (d): {d:.2f} м")
    print(f"r1: {r1}, r2: {r2}, r1 + r2: {r1 + r2}, |r1 - r2|: {abs(r1 - r2)}")

    # Проверяем, можно ли найти точку
    if r1 + r2 < d:
        print("Триангуляция невозможна: r1 + r2 < d (окружности не пересекаются).")
        return None, None
    if abs(r1 - r2) > d:
        print("Триангуляция невозможна: |r1 - r2| > d (окружности не пересекаются).")
        return None, None

    # Считаем координаты
    x = (r1**2 - r2**2 + d**2) / (2 * d)
    y = sqrt(abs(r1**2 - x**2))
    y_south = -y  # Вариант южнее

    delta_lon = x / (111320 * cos(radians(lat1)))  # Смещение по долготе
    delta_lat = y / 111320  # Смещение по широте (север)
    delta_lat_south = y_south / 111320  # Смещение по широте (юг)

    bvs_lon_north = lon1 + delta_lon  # Долгота для севера
    bvs_lat_north = lat1 + delta_lat  # Широта для севера
    bvs_lon_south = lon1 + delta_lon  # Долгота для юга
    bvs_lat_south = lat1 + delta_lat_south  # Широта для юга

    # Возвращаем север или юг в зависимости от выбора
    return (bvs_lon_north, bvs_lat_north) if flight_area_north else (bvs_lon_south, bvs_lat_south)

# БЛОК 4: Ввод данных и подготовка
# Запрашиваем путь к файлу
csv_file_path = input("Введите путь к CSV-файлу (например, 'data.csv'): ").strip()

# Устанавливаем, где искать БВС (севернее или южнее линии П1-П2)
flight_area_north = True  # Поменяйте на False, если БВС южнее

# БЛОК 5: Обработка файла и создание карты
if not os.path.exists(csv_file_path):  # Проверяем, есть ли файл
    print(f"Ошибка: Файл '{csv_file_path}' не найден.")
else:
    try:
        # Читаем CSV-файл
        csv_data = pd.read_csv(csv_file_path, delimiter=";")
        expected_columns = ['time', 'lon1', 'lat1', 'r1', 'lon2', 'lat2', 'r2']  # Нужные колонки
        if not all(col in csv_data.columns for col in expected_columns):
            print(f"Ошибка: В файле нужны колонки {expected_columns}.")
            print(f"Найденные колонки: {list(csv_data.columns)}")
        else:
            print("Прочитанные данные из CSV:")
            print(csv_data)

            # Берём координаты П1 и П2 из первой строки
            lon1_fixed, lat1_fixed = csv_data.iloc[0]['lon1'], csv_data.iloc[0]['lat1']
            lon2_fixed, lat2_fixed = csv_data.iloc[0]['lon2'], csv_data.iloc[0]['lat2']
            print(f"Координаты П1: ({lat1_fixed}, {lon1_fixed})")
            print(f"Координаты П2: ({lat2_fixed}, {lon2_fixed})")

            # Создаём карту с центром в П1
            m = folium.Map(location=[lat1_fixed, lon1_fixed], zoom_start=13)
            folium.Marker([lat1_fixed, lon1_fixed],  # Точка П1
                          popup=f"П1: Широта={lat1_fixed:.6f}, Долгота={lon1_fixed:.6f}",
                          icon=folium.Icon(color="red")).add_to(m)
            folium.Marker([lat2_fixed, lon2_fixed],  # Точка П2
                          popup=f"П2: Широта={lat2_fixed:.6f}, Долгота={lon2_fixed:.6f}",
                          icon=folium.Icon(color="red")).add_to(m)

            # Список для точек маршрута БВС
            bvs_positions = []

            # БЛОК 6: Обработка строк и показ маршрута
            for index, row in csv_data.iterrows():
                current_time = row['time']  # Время измерения
                r1, r2 = row['r1'], row['r2']  # Расстояния от П1 и П2
                bvs_lon, bvs_lat = triangulate(lon1_fixed, lat1_fixed, lon2_fixed, lat2_fixed, r1, r2, flight_area_north)
                if bvs_lon is None:  # Если точку не нашли
                    print(f"Время {current_time}: Невозможно вычислить позицию.")
                    continue
                bvs_positions.append([bvs_lat, bvs_lon])  # Добавляем точку в маршрут
                # Добавляем маркер БВС
                folium.Marker([bvs_lat, bvs_lon],
                              popup=f"БВС t={current_time}: Широта={bvs_lat:.6f}, Долгота={bvs_lon:.6f}",
                              icon=folium.Icon(color="blue")).add_to(m)
                # Обновляем маршрут, если есть больше одной точки
                if len(bvs_positions) > 1:
                    # Перерисовываем карту с новым маршрутом
                    m = folium.Map(location=[lat1_fixed, lon1_fixed], zoom_start=13)
                    folium.Marker([lat1_fixed, lon1_fixed],
                                  popup=f"П1: Широта={lat1_fixed:.6f}, Долгота={lon1_fixed:.6f}",
                                  icon=folium.Icon(color="red")).add_to(m)
                    folium.Marker([lat2_fixed, lon2_fixed],
                                  popup=f"П2: Широта={lat2_fixed:.6f}, Долгота={lon2_fixed:.6f}",
                                  icon=folium.Icon(color="red")).add_to(m)
                    for i, pos in enumerate(bvs_positions):  # Добавляем все точки
                        time_at_pos = csv_data.iloc[i]['time']
                        folium.Marker(pos,
                                      popup=f"БВС t={time_at_pos}: Широта={pos[0]:.6f}, Долгота={pos[1]:.6f}",
                                      icon=folium.Icon(color="blue")).add_to(m)
                    folium.PolyLine(bvs_positions, color="blue", weight=2.5, opacity=1).add_to(m)  # Рисуем линию
                print(f"Время {current_time}: БВС на ({bvs_lat:.6f}, {bvs_lon:.6f})")
                # Показываем карту с задержкой
                clear_output(wait=True)
                display(m)
                time.sleep(1)  # Ждём 1 секунду

            # БЛОК 7: Итог и сохранение
            if len(bvs_positions) > 1:
                print("Маршрут добавлен на карту.")
            else:
                print("Недостаточно точек для построения маршрута.")
            m.save("bvs_map.html")  # Сохраняем карту
            print("Карта сохранена в 'bvs_map.html'.")

    except Exception as e:
        print(f"Ошибка при обработке файла '{csv_file_path}': {str(e)}")