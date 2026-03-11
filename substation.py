# substation.py
from typing import List, Dict, Optional
from equipment import Busbar, Breaker, Line, Transformer, Equipment
from logger_setup import logger


class Substation:
    """Подстанция 750/330 - композиция: владеет всем оборудованием"""

    def __init__(self, name: str = "ПС 750/330"):
        self.name = name
        self.busbars: List[Busbar] = []  # Композиция
        self.lines: List[Line] = []  # Композиция
        self.transformers: List[Transformer] = []  # Композиция
        self.breakers: List[Breaker] = []  # Композиция
        self._equipment_dict: Dict[str, Equipment] = {}  # Для быстрого доступа

    def add_busbar(self, name: str, voltage: str, section: int) -> Busbar:
        """Добавить шину"""
        bus = Busbar(name, voltage, section)
        self.busbars.append(bus)
        self._equipment_dict[name] = bus
        logger.debug(f"Добавлена шина {name}")
        return bus

    def add_line(self, name: str, voltage: str) -> Line:
        """Добавить линию"""
        line = Line(name, voltage)
        self.lines.append(line)
        self._equipment_dict[name] = line
        logger.debug(f"Добавлена линия {name}")
        return line

    def add_transformer(self, name: str) -> Transformer:
        """Добавить трансформатор"""
        tr = Transformer(name)
        self.transformers.append(tr)
        self._equipment_dict[name] = tr
        logger.debug(f"Добавлен трансформатор {name}")
        return tr

    def add_breaker(self, name: str, voltage: str) -> Breaker:
        """Добавить выключатель"""
        br = Breaker(name, voltage)
        self.breakers.append(br)
        logger.debug(f"Добавлен выключатель {name}")
        return br

    def get_equipment(self, name: str) -> Optional[Equipment]:
        """Получить оборудование по имени"""
        return self._equipment_dict.get(name)

    def get_all_equipment(self) -> List[Equipment]:
        """Получить все оборудование для КЗ"""
        return self.lines + self.transformers + self.busbars

    def reset(self):
        """Сброс состояния подстанции"""
        for br in self.breakers:
            br.close()
        for eq in self.get_all_equipment():
            eq.status = "normal"
            for prot in eq.protections:
                prot.tripped = False
                prot.failed = False
        logger.debug("Состояние подстанции сброшено")