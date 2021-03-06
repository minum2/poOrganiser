import unittest
from Poorganiser import Response, Choice


class TestResponse(unittest.TestCase):
    def test_constructor_assertions(self):
        # Incorrect responder_id type
        with self.assertRaises(AssertionError):
            Response("text", "asdf", 3)

        with self.assertRaises(AssertionError):
            Response(3.14, 1032, response_text="LOL")

        with self.assertRaises(AssertionError):
            Response([1], 1032, choice_ids=[3, 4], response_text="ok then")

        # Incorrect question_id type
        with self.assertRaises(AssertionError):
            Response(24, "qwerty")

        with self.assertRaises(AssertionError):
            Response(952, ["in", "va", "li", "d"], response_text="asdf")

        with self.assertRaises(AssertionError):
            Response(952, 9.876, choice_ids=[42, 24, 56], response_text="qwertyuiop")

        # Invalid response_text type
        with self.assertRaises(AssertionError):
            Response(952, ["in", "va", "li", "d"], response_text=12345)

        with self.assertRaises(AssertionError):
            Response(952, 9.876, choice_ids=[42, 24, 56], response_text=False)

        # Invalid choice_ids type
        with self.assertRaises(AssertionError):
            Response(14, 4, choice_ids="lel")

        with self.assertRaises(AssertionError):
            Response(14, 4, choice_ids=1234, response_text="lalalala")

        with self.assertRaises(AssertionError):
            Response(14, 4, choice_ids=[1, 3, 4, "INVALID"])

        with self.assertRaises(AssertionError):
            Response(14, 4, choice_ids=[1.3, 2, 3, 4])

    def test_get_responder_id(self):
        r = Response(1, 2)
        self.assertEqual(r.get_responder_id(), 1)

        r = Response(32, 9999, response_text="lol")
        self.assertEqual(r.get_responder_id(), 32)

        r = Response(56, 64, choice_ids=[64, 34], response_text="hahahaha")
        self.assertEqual(r.get_responder_id(), 56)

    def test_get_question_id(self):
        r = Response(1, 2)
        self.assertEqual(r.get_question_id(), 2)

        r = Response(32, 9999, response_text="wat")
        self.assertEqual(r.get_question_id(), 9999)

        r = Response(56, 64, choice_ids=[64, 34, 103], response_text="why")
        self.assertEqual(r.get_question_id(), 64)

    def test_get_response_text(self):
        r = Response(1, 2)
        self.assertEqual(r.get_response_text(), None)

        r = Response(56, 64, choice_ids=[14], response_text="... really")
        self.assertEqual(r.get_response_text(), "... really")

        r = Response(72, 34, choice_ids=[245, 10, 201], response_text="why would you do that")
        self.assertEqual(r.get_response_text(), "why would you do that")

    def test_get_choice_ids(self):
        r = Response(1, 2)
        self.assertEqual(r.get_choice_ids(), [])

        r = Response(56, 64, choice_ids=[14], response_text="... really")
        self.assertEqual(r.get_choice_ids(), [14])

        r = Response(72, 34, choice_ids=[245, 10, 201], response_text="why would you do that")
        self.assertEqual(r.get_choice_ids(), [245, 10, 201])

    def test_set_response_text(self):
        r = Response(1, 2)
        self.assertEqual(r.get_response_text(), None)
        r.set_response_text("WHATEVER")
        self.assertEqual(r.get_response_text(), "WHATEVER")
        r.set_response_text("WHATEVER2")
        self.assertEqual(r.get_response_text(), "WHATEVER2")

        r = Response(56, 64, choice_ids=[14], response_text="... really")
        self.assertEqual(r.get_response_text(), "... really")
        r.set_response_text("something along those lines")
        self.assertEqual(r.get_response_text(), "something along those lines")

        r = Response(72, 34, choice_ids=[245, 10, 201], response_text="why would you do that")
        self.assertEqual(r.get_response_text(), "why would you do that")
        r.set_response_text("blablabla")
        self.assertEqual(r.get_response_text(), "blablabla")

    def test_add_choice_id(self):
        r = Response(1, 64)
        self.assertEqual(r.get_choice_ids(), [])

        r.add_choice_id(14)
        self.assertEqual(r.get_choice_ids(), [14])

        r = Response(290, 34, choice_ids=[10], response_text="???")
        self.assertEqual(r.get_choice_ids(), [10])

        # Test adding with mock Choice objects
        c_mock = Choice(1, "lol")
        c_mock.id = 201
        r.add_choice_id(c_mock)
        self.assertEqual(r.get_choice_ids(), [10, 201])
        c_mock.id = 245
        r.add_choice_id(c_mock)
        self.assertEqual(r.get_choice_ids(), [10, 201, 245])

        # Test adding duplicates
        r.add_choice_id(245)
        r.add_choice_id(245)
        r.add_choice_id(10)
        self.assertEqual(r.get_choice_ids(), [10, 201, 245])

        # Test adding ids with invalid types
        with self.assertRaises(TypeError):
            r.add_choice_id("lol")

        with self.assertRaises(TypeError):
            r.add_choice_id(31.45)

        with self.assertRaises(TypeError):
            r.add_choice_id(r)

    def test_remove_choice_id(self):
        r = Response(1, 64)
        self.assertEqual(r.get_choice_ids(), [])

        # Add and remove single role
        r.add_choice_id(14)
        self.assertEqual(r.get_choice_ids(), [14])
        r.remove_choice_id(14)
        self.assertEqual(r.get_choice_ids(), [])

        # Add and remove multiple roles
        r = Response(42, 34, choice_ids=[10], response_text="um ok")
        self.assertEqual(r.get_choice_ids(), [10])
        r.add_choice_id(245)
        self.assertEqual(r.get_choice_ids(), [10, 245])
        r.remove_choice_id(10)
        self.assertEqual(r.get_choice_ids(), [245])
        r.remove_choice_id(245)
        self.assertEqual(r.get_choice_ids(), [])
        r.add_choice_id(10)
        self.assertEqual(r.get_choice_ids(), [10])
        r.add_choice_id(201)
        self.assertEqual(r.get_choice_ids(), [10, 201])
        r.add_choice_id(245)
        self.assertEqual(r.get_choice_ids(), [10, 201, 245])

        # Test removing with mock Choice objects
        c_mock = Choice(45, "something")
        c_mock.id = 10
        r.remove_choice_id(c_mock)
        self.assertEqual(r.get_choice_ids(), [201, 245])
        c_mock.id = 245
        r.remove_choice_id(c_mock)
        self.assertEqual(r.get_choice_ids(), [201])
        c_mock.id = 999  # Doesn't exist
        self.assertEqual(r.get_choice_ids(), [201])
        r.remove_choice_id(201)
        self.assertEqual(r.get_choice_ids(), [])

        # Test removing ids with invalid types
        with self.assertRaises(TypeError):
            r.remove_choice_id("lol")

        with self.assertRaises(TypeError):
            r.remove_choice_id(31.45)

        with self.assertRaises(TypeError):
            r.remove_choice_id(r)

if __name__ == '__main__':
    unittest.main()
