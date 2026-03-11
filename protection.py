# protection.py
import random
from typing import List, Optional, Tuple
from logger_setup import logger


class Protection:
    """Класс защиты - может существовать независимо (агрегация)"""

    def __init__(self, object_name: str, prot_type: str, setting_a: float,
                 fail_prob: float, time_delay_ms: int):
        self.object_name = object_name
        self.type = prot_type
        self.setting_A = setting_a
        self.fail_prob_threshold = fail_prob
        self.time_delay_ms = time_delay_ms
        self.tripped = False
        self.failed = False

    def should_trip(self, current: float) -> bool:
        """Проверить, должно ли сработать защиту"""
        return current > self.setting_A

    def check_failure(self) -> bool:
        """Проверить отказ защиты"""
        if random.uniform(0, 100) < self.fail_prob_threshold:
            self.failed = True
            return True
        return False

    def __repr__(self):
        status = "✅" if self.tripped else "⏳"
        if self.failed:
            status = "❌"
        return f"{status} {self.type}(уставка={self.setting_A}А, время={self.time_delay_ms}мс)"


class ProtectionFactory:
    """Фабрика для создания защит из JSON"""

    @staticmethod
    def create_from_json(data: dict) -> Protection:
        """Создать защиту из JSON-данных"""
        return Protection(
            object_name=data["object"],
            prot_type=data["type"],
            setting_a=data["setting_A"],
            fail_prob=data["fail_prob_threshold"],
            time_delay_ms=data["time_delay_ms"]
        )


class ProtectionSystem:
    """Система РЗА - управляет защитами и выключателями"""

    # Типы повреждений
    FAULT_TYPES = {
        "3ph": "трехфазное КЗ",
        "2ph": "двухфазное КЗ",
        "1ph": "однофазное КЗ",
        "winding": "витковое замыкание"
    }

    def __init__(self, substation):
        self.substation = substation
        self.tripped_protections: List[Protection] = []
        self.failed_protections: List[Protection] = []

    def analyze_fault(self, equipment, fault_type: str, current: float) -> Tuple[Optional[Protection], List]:
        """
        Анализ КЗ и выбор срабатывающей защиты
        """
        if not equipment.protections:
            logger.warning(f"На объекте {equipment.name} нет защит!")
            return None, []

        # Логируем детали КЗ в debug режиме
        logger.debug(
            f"Анализ КЗ на {equipment.name} ({type(equipment).__name__}), тип: {self.FAULT_TYPES[fault_type]}, ток: {current:.1f} А")

        # Фильтруем отказавшие защиты
        working = []
        for prot in equipment.protections:
            if prot.check_failure():
                logger.error(f"Защита {prot.type} на {equipment.name} отказала! (порог {prot.fail_prob_threshold}%)")
                self.failed_protections.append(prot)
            else:
                working.append(prot)

        if not working:
            logger.error(f"ВСЕ ЗАЩИТЫ на {equipment.name} ОТКАЗАЛИ!")
            return None, []

        # Сортируем по времени срабатывания
        working.sort(key=lambda p: p.time_delay_ms)

        # Проверяем условия срабатывания
        tripped = None
        for prot in working:
            if prot.should_trip(current):
                logger.debug(f"Защита {prot.type}: ток {current:.1f}А > уставка {prot.setting_A}А")
                if tripped is None or prot.time_delay_ms < tripped.time_delay_ms:
                    tripped = prot
            else:
                logger.debug(f"Защита {prot.type}: ток {current:.1f}А < уставка {prot.setting_A}А")

        if tripped:
            logger.info(f"Срабатывает защита {tripped.type} на {equipment.name} (время {tripped.time_delay_ms} мс)")
            tripped.tripped = True
            self.tripped_protections.append(tripped)

            # Отключаем выключатели
            breakers = equipment.get_breakers()
            for br in breakers:
                if br.status == "closed":
                    br.open()
                    logger.debug(f"Отключен выключатель {br.name}")

            return tripped, breakers

        logger.info(f"Ни одна защита на {equipment.name} не сработала (ток {current:.1f}А ниже уставок)")
        return None, []

    def reset(self):
        """Сброс состояния системы"""
        self.tripped_protections.clear()
        self.failed_protections.clear()