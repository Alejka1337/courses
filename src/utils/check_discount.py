from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.crud.course import CourseRepository
from src.crud.category import CategoryRepository
from src.utils.stripe_logic import create_coupon, create_promotion_code
from src.crud.student_course import check_bought_course


class Discount(ABC):
    def __init__(self, db: Session, cart: list[int], student_id: int):
        self._db = db
        self._course_repo = CourseRepository(db)
        self._category_repo = CategoryRepository(db)
        self._cart = cart
        self._student_id = student_id

    @abstractmethod
    def check_discount(self):
        pass


class WebDiscount(Discount):

    def check_discount(self):
        result = self.check_full_category_discount()
        if result["status"] == "set_discount":
            return {"coupon": result["coupon"], "type": "coupon"}

        result = self.check_part_category_discount()
        if result["status"] == "set_discount":
            return {"coupon": result["coupon"], "type": "coupon"}

    def check_full_category_discount(self):
        for item in self._cart:
            course_base = self._course_repo.select_base_course_by_id(item)
            category_courses = self._course_repo.select_course_by_category(course_base.category_id)

            if set(self._cart).intersection(set(category_courses)) == set(category_courses):
                discount = self._category_repo.select_category_discount(course_base.category_id)
                coupon_id = create_coupon(discount)
                return {"status": "set_discount", "coupon": coupon_id}

        return {"status": "without_discount"}

    def check_part_category_discount(self):
        for item in self._cart:
            course_base = self._course_repo.select_base_course_by_id(item)
            category_courses = self._course_repo.select_course_by_category(course_base.category_id)

            difference = set(category_courses).difference(set(self._cart))
            result = check_bought_course(self._db, self._student_id, list(difference))

            if result is not None:
                discount = self._category_repo.select_category_discount(course_base.category_id)
                coupon_id = create_coupon(discount)
                return {"status": "set_discount", "coupon": coupon_id}

        return {"status": "without_discount"}


class MobileDiscount(Discount):

    def check_discount(self):
        result = self.check_full_category_discount()
        if result is not None:
            return result

        result = self.check_part_category_discount()
        if result is not None:
            return result

    def check_full_category_discount(self):
        for item in self._cart:
            course_base = self._course_repo.select_base_course_by_id(item)
            category_courses = self._course_repo.select_course_by_category(course_base.category_id)

            if set(self._cart).intersection(set(category_courses)) == set(category_courses):
                discount = self._category_repo.select_category_discount(course_base.category_id)
                return discount / 100

    def check_part_category_discount(self):
        for item in self._cart:
            course_base = self._course_repo.select_base_course_by_id(item)
            category_courses = self._course_repo.select_course_by_category(course_base.category_id)

            difference = set(category_courses).difference(set(self._cart))
            print(difference)
            result = check_bought_course(self._db, self._student_id, list(difference))

            if result:
                print(f"Part - {result}")
                discount = self._category_repo.select_category_discount(course_base.category_id)
                return discount / 100
