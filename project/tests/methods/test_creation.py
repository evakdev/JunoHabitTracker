from base import Session
from models.models import Method
from unittest import TestCase
import unittest


class TestSpecified(TestCase):
    def setUp(self):

        with Session(expire_on_commit=False) as s:

            duration = "week"
            self.method = Method(
                type="specified", duration=duration, specified=[1, 3, 5]
            )  # Mon, Wed, Fri
            s.add(self.method)
            s.commit()
            self.method_id = self.method.id

    def test_convert_specified(self):
        sample_ls = [2, 3, 4]
        result = self.method.convert_specified(sample_ls)
        self.assertEqual(type(result), str)

    def test_specified_days_property(self):
        result = self.method.specified_days
        self.assertEqual(result, [1, 3, 5])
        self.assertEqual(type(result), list)
        self.assertEqual(type(result[0]), int)

    def tearDown(self) -> None:

        with Session() as s:
            method = s.query(Method).filter_by(id=self.method_id)
            method.delete()
            s.commit()


if __name__ == "__main__":
    unittest.main()
