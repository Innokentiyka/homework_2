# equipment.py
from abc import ABC, abstractmethod
from typing import List, Optional


class Equipment(ABC):
    """Абстрактный базовый класс для всего оборудования"""

    def __init__(self, name: str, voltage_level: str):
        self.name = name
        self.voltage_level = voltage_level
        self.status = "normal"  # normal, fault, tripped
        self.protections: List['Protection'] = []  # Агрегация: оборудование содержит защиты

    def add_protection(self, protection: 'Protection'):
        """Добавить защиту к оборудованию (агрегация)"""
        self.protections.append(protection)

    @abstractmethod
    def get_breakers(self):
        """Получить выключатели, связанные с оборудованием"""
        pass

    def trip(self):
        """Отключить оборудование"""
        self.status = "tripped"
        for breaker in self.get_breakers():
            breaker.open()


class Breaker:
    """Выключатель - композиция с подстанцией"""

    def __init__(self, name: str, voltage_level: str):
        self.name = name
        self.voltage_level = voltage_level
        self.status = "closed"  # closed, opened
        self.equipment: Optional[Equipment] = None  # Ассоциация: ссылка на оборудование

    def open(self):
        self.status = "opened"

    def close(self):
        self.status = "closed"

    def __repr__(self):
        return f"Breaker({self.name}, {self.voltage_level}, {self.status})"


class Line(Equipment):
    """Линия электропередачи - наследуется от Equipment"""

    def __init__(self, name: str, voltage_level: str):
        super().__init__(name, voltage_level)
        self._breakers: List[Breaker] = []  # Композиция: линия владеет выключателями

    def add_breaker(self, breaker: Breaker):
        """Добавить выключатель к линии"""
        self._breakers.append(breaker)
        breaker.equipment = self

    def get_breakers(self) -> List[Breaker]:
        return self._breakers.copy()

    def __repr__(self):
        return f"Line({self.name}, {self.voltage_level}, breakers: {len(self._breakers)})"


class Transformer(Equipment):
    """Трансформатор 750/330 - наследуется от Equipment"""

    def __init__(self, name: str):
        super().__init__(name, "VN")  # ВН как основной уровень
        self.hv_breakers: List[Breaker] = []  # Выключатели на стороне 750 кВ (ВН)
        self.lv_breakers: List[Breaker] = []  # Выключатели на стороне 330 кВ (НН)

    def add_breaker(self, breaker: Breaker, side: str):
        """Добавить выключатель на указанную сторону"""
        breaker.equipment = self
        if side == "HV":
            self.hv_breakers.append(breaker)
        elif side == "LV":
            self.lv_breakers.append(breaker)

    def get_breakers(self) -> List[Breaker]:
        """Получить все выключатели трансформатора"""
        return self.hv_breakers + self.lv_breakers

    def __repr__(self):
        return f"Transformer({self.name}, 750кВ:{len(self.hv_breakers)}, 330кВ:{len(self.lv_breakers)})"


class Busbar(Equipment):
    """Секция шин - наследуется от Equipment"""

    def __init__(self, name: str, voltage_level: str, section_number: int):
        super().__init__(name, voltage_level)
        self.section_number = section_number
        self.connected_breakers: List[Breaker] = []  # Выключатели, подключенные к шине

    def connect_breaker(self, breaker: Breaker):
        """Подключить выключатель к шине"""
        self.connected_breakers.append(breaker)
        breaker.equipment = self

    def get_breakers(self) -> List[Breaker]:
        return self.connected_breakers.copy()

    def __repr__(self):
        return f"Busbar({self.name}, секция {self.section_number}, выкл:{len(self.connected_breakers)})"