from __future__ import annotations

from typing import Iterable, Iterator, List, Tuple

import pandas as pd
import streamlit as st

# =============================================================================
#  1)  مساعدة الفئة الأساسية (نفس المنطق السابق مع دالة  للسبب
# linked with GitHub
# =============================================================================
class CeilingContainer:
    """حاوية أرقام ذات سقف تصاعدي، مع حدٍّ أعلى لنسبة التجاوز."""

    __slots__ = ("_items", "_max_slack")
    DEFAULT_MAX_SLACK: float = 0.12
    _EPS: float = 1e-12

    def __init__(self,
                 items: Iterable[float] = (),
                 max_slack_ratio: float = DEFAULT_MAX_SLACK) -> None:
        if not (0.0 <= max_slack_ratio < 1.0):
            raise ValueError("max_slack_ratio يجب أن يكون في [0, 1)")
        self._items: List[float] = sorted(self._validate(v) for v in items)
        self._max_slack: float = max_slack_ratio

    @staticmethod
    def _validate(value: float) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"يُسمح بالأرقام فقط: {value!r}")
        return float(value)

    # -------- خصائص --------
    @property
    def ceiling(self) -> float:
        return self._items[-1] if self._items else 0.0

    @property
    def real_sum(self) -> float:
        return sum(self._items)


    @property
    def ceiling_sum(self) -> float:
        return self.ceiling * len(self._items)

    @property
    def slack_ratio(self) -> float:
        cs = self.ceiling_sum
        if cs <= 0:
            return 0.0
        return max(0.0, (cs - self.real_sum) / cs)

    @property
    def max_slack_ratio(self) -> float:
        return self._max_slack

    @property
    def items(self) -> Tuple[float, ...]:
        return tuple(self._items)

    # -------- الشروط --------
    def _slack_ratio_if_added(self, value: float) -> float:
        new_count = len(self._items) + 1
        new_real  = self.real_sum + value
        new_cs    = value * new_count
        if new_cs <= 0:
            return 0.0
        slack = new_cs - new_real
        return 0.0 if slack <= 0 else slack / new_real

    def can_add(self, value: float) -> bool:
        value = self._validate(value)
        if not self._items:
            return True
        if value < self.ceiling:
            return False
        return self._slack_ratio_if_added(value) <= self._max_slack + self._EPS


    def rejection_reason(self, value: float) -> str:
        value = self._validate(value)
        if not self._items:
            return ""
        if value < self.ceiling:
            return f"الرقم {value:g} < السقف الحالي {self.ceiling:g}"
        r = self._slack_ratio_if_added(value)
        return f"لو أُضيف، نسبة التجاوز ≈ {r:.2%} > {self._max_slack:.0%}"

    # -------- الإضافة --------
    def add(self, value: float) -> "CeilingContainer":
        value = self._validate(value)
        if self.can_add(value):
            self._items.append(value)
            return self
        return type(self)([value], 

self._max_slack)

    def add_or_spill(self, value: float) -> Tuple["CeilingContainer", bool]:
        value = self._validate(value)
        if self.can_add(value):
            self._items.append(value)
            return self, False
        return type(self)([value], self._max_slack), True

    # -------- بروتوكولات --------
    def __len__(self) -> int: return len(self._items)
    def __iter__(self) -> Iterator[float]: return iter(self._items)
    def __contains__(self, v: object) -> bool: return v in self._items
    def __repr__(self) -> str:
        return (f"CeilingContainer(items={self._items}, ceiling={self.ceiling:g}, "
                f"sum={self.real_sum:g}, slack={self.slack_ratio:.2%})")
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CeilingContainer): return NotImplemented
        return self._items == other._items and self._max_slack == other._max_slack


# =============================================================================
#  2) دوال التوزيع
# =============================================================================
def distribute_sequential(numbers: List[float], max_slack: float

                         ) -> Tuple[List[CeilingContainer], List[dict]]:
    """تسلسلي: كل رقم يُجرَّب على الحاوية الحالية فقط، وإلا حاوية جديدة."""
    containers: List[CeilingContainer] = []
    log: List[dict] = []
    current: CeilingContainer | None = None

    for n in numbers:
        if current is None:
            current = CeilingContainer([n], max_slack_ratio=max_slack)
            containers.append(current)
            log.append({"الرقم": n, "الحاوية": len(containers),
                        "القرار": "بداية جديدة",
                        "نسبة التجاوز بعد": current.slack_ratio,
                        "السبب": "أول رقم"})
            continue

        if current.can_add(n):
            current.add(n)
            log.append({"الرقم": n, "الحاوية": len(containers),
                        "القرار": "قبول",
                        "نسبة التجاوز بعد": current.slack_ratio,
                        "السبب": ""})
        else:
            reason = current.rejection_reason(n)
            current = CeilingContainer([n], max_slack_ratio=max_slack)
            containers.append(current)
            log.append({"الرقم": n, "الحاوية": len(containers),
                        "القرار": "تجاوز → حاوية جديدة",
                        "نسبة التجاوز بعد": current.slack_ratio,
                        "السبب": reason})
    return containers, log


def distribute_first_fit(numbers: List[float], max_slack: float
                         ) -> Tuple[List[CeilingContainer], List[dict]]:
    """أول-ملائم: يُجرَّب كل رقم على الحاويات بالترتيب، أول حاوية تقبله."""
    containers: List[CeilingContainer] = []
    log: List[dict] = []

    for n in numbers:
        placed = False
        for i, c in enumerate(containers, 1):
            if c.can_add(n):
                c.add(n)
                log.append({"الرقم": n, "الحاوية": i, "القرار": "قبول",
                            "نسبة التجاوز بعد": c.slack_ratio, "السبب": ""})
                placed = True
                break

        if not placed:
            new = CeilingContainer([n], max_slack_ratio=max_slack)
            containers.append(new)
            log.append({"الرقم": n, "الحاوية": len(containers),
                        "القرار": "حاوية جديدة",
                        "نسبة التجاوز بعد": new.slack_ratio,
                        "السبب": "لا حاوية حالية تقبله"})
    return containers, log



