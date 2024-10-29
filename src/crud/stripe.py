from sqlalchemy.orm import Session

from src.models import StripeCourseOrm


class StripeCourseRepository:

    def __init__(self, db: Session):
        self.db = db
        self.model = StripeCourseOrm

    def create_stripe_product(self, stripe_data):
        new_row = self.model(**stripe_data)
        self.db.add(new_row)
        self.db.commit()

    def select_stripe_product_id(self, course_id):
        data = (self.db.query(self.model.stripe_product_id)
                .filter(self.model.course_id == course_id)
                .scalar())

        return data

    def select_stripe_price_id(self, course_id):
        data = (self.db.query(self.model.stripe_price_id)
                .filter(self.model.course_id == course_id)
                .scalar())

        return data

    def select_price_ids(self, course_ids: list[int]):
        result = (self.db.query(self.model.stripe_price_id.label("price_id"))
                  .filter(self.model.course_id.in_(course_ids))
                  .all())

        price_ids = [item.price_id for item in result]
        return price_ids

    def update_stripe_price_id(self, course_id, stripe_price_id):
        (self.db.query(self.model)
         .filter(self.model.course_id == course_id)
         .update({
            self.model.stripe_price_id: stripe_price_id
         }, synchronize_session=False))

        self.db.commit()
