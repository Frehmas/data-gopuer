class SmartContainer:
    def __init__(self, initial_number=None, max_overflow_ratio=0.12):
        """
        تهيئة الحاوية الذكية.
        :param initial_number: الرقم الأولي لتبدأ به الحاوية (اختياري).
        :param max_overflow_ratio: نسبة التجاوز المسموح بها (الافتراضي 0.12 أي 12%).
        """
        self.numbers = []
        self.max_overflow_ratio = max_overflow_ratio
        
        if initial_number is not None:
            self.numbers.append(initial_number)

    @property

    def ceiling(self):
        """إرجاع السقف (أكبر رقم في المجموعة)، وإذا كانت فارغة يكون 0."""
        if not self.numbers:
            return 0
        return max(self.numbers)

    @property
    def current_sum(self):
        """المجموع الحقيقي لأرقام المجموعة."""
        return sum(self.numbers)

    @property
    def limit_sum(self):
        """المجموع السقفي: السقف الحالي × عدد البيانات المضافة."""
        return self.ceiling * len(self.numbers)

    def can_add(self, number) -> bool:
        """
        التحقق من إمكانية إضافة الرقم بناءً على 

الشروط:
        1. الرقم >= السقف الحالي.
        2. المجموع السقفي لا يتجاوز المجموع الحقيقي بنسبة أعلى من 12%.
        """
        # إذا كانت الحاوية فارغة، نُجيز الإضافة مباشرة
        if not self.numbers:
            return True

        # الشرط الأول: ألا يكون الرقم أقل من السقف الحالي
        if number < self.ceiling:
            return False

        # محاكاة تجريبية للإضافة قبل واعتمادها
        temp_numbers = self.numbers + [number]
        temp_ceiling = max(temp_numbers)
        temp_limit_sum = temp_ceiling * len(temp_numbers)
        temp_real_sum = sum(temp_numbers)


        # الحد الأقصى المسموح للمجموع السقفي مع نسبة السماح (12%)
        max_allowed_limit = temp_real_sum * (1 + self.max_overflow_ratio)

        # شرط القبول: المجموع السقفي يجب ألا يتجاوز الحد المسموح
        return temp_limit_sum <= max_allowed_limit

    def add(self, number):
        """
        إضافة رقم للحاوية:
        - إذا تحققت الشروط يُضاف للحاوية الحالية وتُرجع نفس الحاوية.
        - عند التجاوز، تُنشأ وتُرجع نسخة (حاوية) جديدة يوضع بها الرقم.
        """
        if self.can_add(number):
            self.numbers.append(number)

            return self
        else:
            # إنشاء حاوية جديدة مع الاحتفاظ بنسبة التجاوز نفسها
            new_container = SmartContainer(
                initial_number=number, 
                max_overflow_ratio=self.max_overflow_ratio
            )
            return new_container

    def __repr__(self):
        return (f"SmartContainer(numbers={self.numbers}, "
                f"ceiling={self.ceiling}, "
                f"real_sum={self.current_sum}, "
                f"limit_sum={self.limit_sum})")
