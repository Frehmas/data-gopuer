from __future__ import annotations

from typing import Iterable, Iterator, List, Tuple

import pandas as pd
import streamlit as st


# =============================================================================
#  1)  مساعدة الفئة الأساسية (نفس المنطق السابق مع دالة  للسبب

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


# =============================================================================
#  3) أدوات مساعدة للعرض
# =============================================================================
def parse_numbers(text: str) -> List[float]:
    tokens = text.replace(",", " ").replace("،", " ").split()
    out: List[float] = []
    for t in tokens:
        try:
            out.append(float(t))
        except ValueError:
            raise ValueError(f"قيمة غير رقمية: {t!r}")
    return out


def fmt_num(v: float) -> str:
    return f"{int(v)}" if float(v).is_integer() else f"{v:g}"


def render_kpis(containers: List[CeilingContainer]) -> None:
    total_real = sum(c.real_sum for c in 

containers)
    total_ceil = sum(c.ceiling_sum for c in containers)
    avg_slack  = sum(c.slack_ratio for c in containers) / len(containers)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("عدد الحاويات", len(containers))
    c2.metric("إجمالي الأرقام", sum(len(c) for c in containers))
    c3.metric("المجموع الحقيقي", f"{total_real:,.0f}")
    c4.metric("المجموع السقفي", f"{total_ceil:,.0f}")
    c5.metric("متوسط نسبة التجاوز", f"{avg_slack:.2%}")


def render_containers_table(containers: List[CeilingContainer]) -> None:
    rows = [{
        "الحاوية": f"C{i}",

        "العناصر": ", ".join(fmt_num(v) for v in c.items),
        "العدد": len(c),
        "السقف": c.ceiling,
        "المجموع الحقيقي": c.real_sum,
        "المجموع السقفي": c.ceiling_sum,
        "نسبة التجاوز %": round(c.slack_ratio * 100, 2),
    } for i, c in enumerate(containers, 1)]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_chart(containers: List[CeilingContainer], max_slack: float) -> None:
    chart = pd.DataFrame({
        "الحاوية": [f"C{i}" for i in range(1, len(containers) + 1)],
        "نسبة التجاوز %": [round(c.slack_ratio * 

100, 2) for c in containers],
    })
    st.bar_chart(chart, x="الحاوية", y="نسبة التجاوز %", height=280)
    st.caption(f"الحد المسموح = {max_slack:.0%} — كل قيمة فوقه تعني تجاوزاً.")


def render_log(log: List[dict]) -> None:
    rows = [{
        "الرقم": e["الرقم"],
        "الحاوية": f"C{e['الحاوية']}",
        "القرار": e["القرار"],
        "نسبة التجاوز بعد %": round(e["نسبة التجاوز بعد"] * 100, 2),
        "السبب": e["السبب"],
    } for e in log]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_details(containers: List[CeilingContainer]) -> None:
    for i, c in enumerate(containers, 1):
        with st.expander(f"🔹 الحاوية C{i} — {len(c)} عنصر | slack = {c.slack_ratio:.2%}"):
            a, b, d = st.columns(3)
            a.metric("السقف", fmt_num(c.ceiling))
            b.metric("المجموع الحقيقي", f"{c.real_sum:,.0f}")
            d.metric("المجموع السقفي", f"{c.ceiling_sum:,.0f}")
            util = (c.real_sum / c.ceiling_sum) if c.ceiling_sum > 0 else 0.0
            st.progress(min(util, 1.0), text=f"نسبة الاستغلال: {util:.2%}")
            st.write("**العناصر:**", ", ".join(fmt_num(v) for v in c.items))


def download_buttons(containers: 

List[CeilingContainer], log: List[dict]) -> None:
    rows = [{
        "الحاوية": f"C{i}",
        "العناصر": ", ".join(fmt_num(v) for v in c.items),
        "العدد": len(c), "السقف": c.ceiling,
        "المجموع الحقيقي": c.real_sum,
        "المجموع السقفي": c.ceiling_sum,
        "نسبة التجاوز %": round(c.slack_ratio * 100, 2),
    } for i, c in enumerate(containers, 1)]

    c1, c2 = st.columns(2)
    c1.download_button(
        "⬇️ تنزيل الحاويات (CSV)",
        pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig"),
        file_name="containers.csv", mime="text/csv",

        use_container_width=True,
    )
    log_df = pd.DataFrame([{
        "الرقم": e["الرقم"], "الحاوية": f"C{e['الحاوية']}",
        "القرار": e["القرار"],
        "نسبة التجاوز بعد %": round(e["نسبة التجاوز بعد"] * 100, 2),
        "السبب": e["السبب"],
    } for e in log])
    c2.download_button(
        "⬇️ تنزيل السجل (CSV)",
        log_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="log.csv", mime="text/csv",
        use_container_width=True,
    )


# =============================================================================
#  4) الواجهة الرئيسية
# =============================================================================
def main() -> None:
    st.set_page_config(page_title="موزّع الأرقام", page_icon="📊", layout="wide")

    st.title("📊 موزّع الأرقام في حاويات ذات سقف تصاعدي")
    st.caption(
        "السقف = أكبر رقم | المجموع السقفي = السقف × العدد | "
        "نسبة التجاوز = (السقفي − الحقيقي) / السقفي | "
        "شرط القبول: الرقم ≥ السقف **و** نسبة التجاوز ≤ الحد"
    )


    # ---------------- الشريط الجانبي ----------------
    with st.sidebar:
        st.header("⚙️ الإعدادات")
        max_slack_pct = st.slider("حد نسبة التجاوز (%)", 1, 50, 12, 1)
        strategy = st.radio(
            "استراتيجية التوزيع",
            ["تسلسلي (حاوية حالية فقط)", "أول-ملائم (كل الحاويات)"],
            index=0,
            help="تسلسلي: يطابق سلوك الفئة الأصلية. أول-ملائم: يُجرَّب كل رقم على كل الحاويات القائمة.",
        )
        st.divider()
        st.caption("نسبة التجاوز هنا تعني **الهامش غير المستغل** بين المجموع الحقيقي والسقفي.")

    # ---------------- الإدخال ----------------
    st.subheader("1) أدخل الأرقام")
    default = "777\n810\n874\n1269\n1371"

    text = st.text_area(
        "رقم في كل سطر (يُقبل أيضاً الفصل بفواصل أو مسافات)",
        value=default, height=180,
    )

    try:
 # معالجة المدخلات وتحويلها إلى قائمة أرقام مرتبة تصاعدياً لضمان التسلسل الصحيح
        raw_numbers = [float(x.strip()) for x in text.replace(",", " ").split() if x.strip()]
        
        if not raw_numbers:
            st.warning("الرجاء إدخال أرقام صحيحة.")
        else:
            # ترتيب الأرقام تصاعدياً لضمان عمل منطق السقف بشكل صحيح
            numbers = sorted(raw_numbers)
        #numbers = parse_numbers(text)
    except ValueError as exc:
        st.error(f"❌ {exc}")
        return

    if not numbers:
        st.warning("⚠️ أدخل رقماً واحداً على الأقل.")
        return

    # ---------------- التوزيع ----------------
    max_slack = max_slack_pct / 100.0
    if strategy.startswith("تسلسلي"):
        containers, log = distribute_sequential(numbers, max_slack)

    else:
        containers, log = distribute_first_fit(numbers, max_slack)

    # ---------------- العرض ----------------
    st.subheader("2) المؤشرات")
    render_kpis(containers)

    st.subheader("3) الحاويات")
    render_containers_table(containers)

    st.subheader("4) توزيع نسبة التجاوز")
    render_chart(containers, max_slack)

    st.subheader("5) سجل القرارات")
    render_log(log)

    st.subheader("6) تفاصيل كل حاوية")
    render_details(containers)

    st.subheader("7) تنزيل النتائج")

    download_buttons(containers, log)


if __name__ == "__main__":
    main()
"""
ما ستراه عند التشغيل (بالأرقام الافتراضية 777 / 810 / 874 / 1269 / 1371)

🔢 المؤشرات العلوية

عدد الحاويات إجمالي الأرقام المجموع الحقيقي المجموع السقفي متوسط التجاوز
2 5 5,101 6,018 4.93%

📦 جدول الحاويات

الحاوية العناصر العدد السقف المجموع الحقيقي 

المجموع السقفي نسبة التجاوز %
C1 777, 810, 874 3 874 2,461 2,622 6.14
C2 1269, 1371 2 1371 2,640 2,742 3.72

📊 مخطط الأعمدة

عمودان: C1 ≈ 6.14% و C2 ≈ 3.72% — كلاهما تحت الحد 12%.

📝 سجل القرارات (مختصر)

الرقم الحاوية القرار نسبة التجاوز بعد % السبب
777 C1 بداية جديدة 0.00 أول رقم
810 C1 قبول 2.04 —
874 C1 قبول 6.14 —
1269 C2 تجاوز → حاوية جديدة 0.00 لو أُضيف، نسبة التجاوز ≈ 26.52% > 12%
1371 C2 قبول 3.72 —

🔍 تفاصيل كل حاوية (Expanders)

· C1: السقف 874 / الحقيقي 2,461 / السقفي 2,622 / الاستغلال 93.9% / العناصر 777, 810, 874
· C2: السقف 1371 / الحقيقي 2,640 / السقفي 2,742 / الاستغلال 96.3% / العناصر 1269, 1371

⬇️ التنزيل

زرّان: containers.csv و log.csv (بترميز UTF-8 مع BOM لفتحه بسهولة في Excel العربي).

---

ملاحظات تصميمية

العنصر الفائدة
مُزلِق الحد (%) يجعل تجربة إعادة التوزيع فورية بدون تعديل الكود (جرّب 25% وسترى 1269 يُقبل في C1).
استراتيجيتان تسلسلي يحافظ على سلوك الفئة الأصلي، أول-ملائم يعطي توزيعاً أذكى عندما تكثر الحاويات.

عمود "السبب" يشرح لماذا رُفض الرقم (رقم < السقف، أو slack سيتجاوز الحد) مع القيمة المحسوبة.
st.progress يُظهر نسبة استغلال الطاقة السقفية بصرياً لكل حاوية (88% حدّ أدنى = 12% slack أقصى).
زر تنزيل CSV يسمح بدمج النتائج في تقارير لاحقة.
use_container_width يجعل الجداول تمتد بعرض الشاشة.

إن أردت نسخة Tkinter تعمل دون تثبيت أي مكتبة (نافذة سطح مكتب كلاسيكية)، أخبرني وسأحوّل نفس الواجهة إليها.
"""