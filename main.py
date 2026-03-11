# main.py
import json
import time
from logger_setup import logger
from substation import Substation
from protection import ProtectionFactory, ProtectionSystem
from fault_simulator import FaultSimulator


def build_substation() -> Substation:
    """Построить подстанцию 750/330 по схеме четырехугольника"""
    ss = Substation("ПС 220/110/10")

    # 1. Шины
    vn_bus1 = ss.add_busbar("ВН_Секция_1", "VN", 1)
    vn_bus2 = ss.add_busbar("ВН_Секция_2", "VN", 2)
    sn_bus1 = ss.add_busbar("СН_Секция_1", "SN", 1)
    sn_bus2 = ss.add_busbar("СН_Секция_2", "SN", 2)


    # 2. Выключатели
    vn_q = [ss.add_breaker(f"ВН_Q{i}", "VN") for i in range(1, 6)]

    sn_q = [ss.add_breaker(f"СН_Q{i}", "SN") for i in range(1, 7)]


    # 3. Линии
    vn_l1 = ss.add_line("ВН_Линия_1", "VN")
    vn_l1.add_breaker(vn_q[0])
    vn_l2 = ss.add_line("ВН_Линия_2", "VN")
    vn_l2.add_breaker(vn_q[1])

    sn_l1 = ss.add_line("СН_Линия_1", "SN")
    sn_l1.add_breaker(sn_q[0])
    sn_l2 = ss.add_line("СН_Линия_2", "SN")
    sn_l2.add_breaker(sn_q[1])
    sn_l3 = ss.add_line("СН_Линия_3", "SN")
    sn_l3.add_breaker(sn_q[2])


    # 4. Трансформаторы
    t1 = ss.add_transformer("Т1")
    t1.add_breaker(vn_q[2], "HV")
    t1.add_breaker(sn_q[3], "MV")


    t2 = ss.add_transformer("Т2")
    t2.add_breaker(vn_q[3], "HV")
    t2.add_breaker(sn_q[4], "MV")

    # 5. Подключение к шинам
    vn_bus1.connect_breaker(vn_q[0])
    vn_bus2.connect_breaker(vn_q[1])
    vn_bus1.connect_breaker(vn_q[2])
    vn_bus2.connect_breaker(vn_q[3])
    vn_bus1.connect_breaker(vn_q[4])
    vn_bus2.connect_breaker(vn_q[4])

    sn_bus1.connect_breaker(sn_q[0])
    sn_bus2.connect_breaker(sn_q[1])
    sn_bus1.connect_breaker(sn_q[2])
    sn_bus1.connect_breaker(sn_q[3])
    sn_bus2.connect_breaker(sn_q[4])
    sn_bus1.connect_breaker(sn_q[5])
    sn_bus2.connect_breaker(sn_q[5])


    logger.info("Подстанция инициализирована")
    return ss


def load_protections(filename: str = 'config.json'):
    """Загрузить защиты из JSON"""
    with open(filename, 'r', encoding='utf-8') as f:
        config = json.load(f)

    protections = []
    for p_data in config['protections']:
        protections.append(ProtectionFactory.create_from_json(p_data))

    logger.info(f"Загружено {len(protections)} защит из JSON")
    return protections, config['global']


def link_protections(substation: Substation, protections):
    """Привязать защиты к оборудованию"""
    count = 0
    for prot in protections:
        eq = substation.get_equipment(prot.object_name)
        if eq:
            eq.add_protection(prot)
            count += 1
            logger.debug(f"Защита {prot.type} привязана к {prot.object_name}")
        else:
            logger.warning(f"Объект {prot.object_name} не найден!")

    logger.info(f"Привязано {count} защит к оборудованию")
    return count


def run_simulation():
    """Основная функция симуляции"""
    logger.info("=" * 60)
    logger.info("ЗАПУСК СИМУЛЯЦИИ РЗА (ВАРИАНТ 3: 750/330, СХЕМА ЧЕТЫРЕХУГОЛЬНИК)")
    logger.info("=" * 60)

    # Построение подстанции
    substation = build_substation()

    # Загрузка защит
    protections, global_config = load_protections()
    link_protections(substation, protections)

    # Инициализация симулятора
    simulator = FaultSimulator(substation)
    max_iter = global_config.get('max_iterations', 15)

    logger.info(f"Запуск {max_iter} итераций симуляции")

    iteration = 0
    while iteration < max_iter:
        iteration += 1
        logger.info(f"--- Итерация {iteration} ---")

        # Сброс состояния
        substation.reset()
        rza = ProtectionSystem(substation)

        # Генерация КЗ
        obj, ftype, current = simulator.generate_fault()
        if not obj:
            continue

        logger.info(
            f"КЗ на {obj.name} ({type(obj).__name__}), тип: {ProtectionSystem.FAULT_TYPES[ftype]}, ток: {current:.1f} А")

        # Проверка самоустранения
        if simulator.is_self_clearing(obj):
            logger.info(f"КЗ на {obj.name} самоустранилось")
            simulator.update_stats(obj, ftype, False, self_cleared=True)
            continue

        # Анализ КЗ
        tripped, breakers = rza.analyze_fault(obj, ftype, current)

        # Логирование результатов
        if tripped:
            logger.info(f"КЗ отключено защитой {tripped.type}, отключено выключателей: {len(breakers)}")
        else:
            logger.error(f"КЗ НЕ ОТКЛЮЧЕНО! Отказало защит: {len(rza.failed_protections)}")

        # Обновление статистики
        simulator.update_stats(obj, ftype, tripped is not None)

        time.sleep(0.1)

    # Итоговая статистика
    logger.info("=" * 60)
    logger.info("СТАТИСТИКА СИМУЛЯЦИИ")
    logger.info("=" * 60)
    logger.info(f"Всего КЗ: {simulator.stats['total']}")
    logger.info(f"Успешно отключено: {simulator.stats['success']}")
    logger.info(f"Не отключено: {simulator.stats['fail']}")
    logger.info(f"Самоустранилось: {simulator.stats['self_cleared']}")

    logger.info("=" * 60)
    logger.info("СИМУЛЯЦИЯ ЗАВЕРШЕНА")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        run_simulation()
    except Exception as e:
        logger.exception("Критическая ошибка в работе программы")