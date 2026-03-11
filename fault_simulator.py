# fault_simulator.py
import random
from typing import Optional, Tuple
from equipment import Transformer, Line
from protection import ProtectionSystem
from logger_setup import logger


class FaultSimulator:
    """Симулятор КЗ - генерация случайных повреждений"""

    # Диапазоны токов для разных напряжений
    CURRENT_RANGES = {
        "VN": (1000, 8000),  # 750 кВ
        "NN": (2000, 15000)  # 330 кВ
    }

    # Коэффициенты для разных типов КЗ
    FAULT_COEFFICIENTS = {
        "3ph": (0.5, 1.0),  # трехфазное
        "2ph": (0.8, 0.87),  # двухфазное (от трехфазного)
        "1ph": (0.6, 0.8),  # однофазное
        "winding": (0.3, 0.5)  # витковое
    }

    def __init__(self, substation):
        self.substation = substation
        self.stats = {
            "total": 0, "success": 0, "fail": 0, "self_cleared": 0,
            "by_object": {}, "by_type": {}
        }

    def generate_fault(self) -> Tuple[Optional, str, float]:
        """
        Сгенерировать случайное КЗ
        Возвращает: (объект, тип_кз, ток)
        """
        # Выбираем объект
        objects = self.substation.get_all_equipment()
        if not objects:
            return None, "", 0

        obj = random.choice(objects)

        # Выбираем тип КЗ (витковое только для трансформаторов)
        if isinstance(obj, Transformer):
            fault_type = random.choice(list(ProtectionSystem.FAULT_TYPES.keys()))
        else:
            fault_type = random.choice(["3ph", "2ph", "1ph"])

        # Генерируем ток
        current = self._generate_current(fault_type, obj)

        logger.debug(f"Сгенерировано КЗ: {obj.name}, тип: {fault_type}, ток: {current:.1f} А")
        return obj, fault_type, current

    def _generate_current(self, fault_type: str, obj) -> float:
        """Сгенерировать ток КЗ"""
        # Определяем диапазон по напряжению
        voltage = getattr(obj, 'voltage_level', "VN")
        min_base, max_base = self.CURRENT_RANGES.get(voltage, (500, 5000))

        # Применяем коэффициент для типа КЗ
        if fault_type in self.FAULT_COEFFICIENTS:
            coef_min, coef_max = self.FAULT_COEFFICIENTS[fault_type]
            if fault_type == "2ph":
                # Для двухфазного относительно трехфазного
                max_current = max_base * coef_max
                return random.uniform(min_base * coef_min, max_current)
            else:
                return random.uniform(min_base * coef_min, max_base * coef_max)

        return random.uniform(min_base, max_base)

    def is_self_clearing(self, obj, probability: float = 0.15) -> bool:
        """Проверка самоустранения (только для линий)"""
        result = isinstance(obj, Line) and random.random() < probability
        if result:
            logger.debug(f"КЗ на {obj.name} самоустранилось")
        return result

    def update_stats(self, obj, fault_type: str, success: bool, self_cleared: bool = False):
        """Обновить статистику"""
        self.stats["total"] += 1

        if self_cleared:
            self.stats["self_cleared"] += 1
        elif success:
            self.stats["success"] += 1
        else:
            self.stats["fail"] += 1

        obj_key = f"{obj.name} ({type(obj).__name__})"
        self.stats["by_object"][obj_key] = self.stats["by_object"].get(obj_key, 0) + 1
        self.stats["by_type"][fault_type] = self.stats["by_type"].get(fault_type, 0) + 1