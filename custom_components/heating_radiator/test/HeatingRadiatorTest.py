import unittest

from custom_components.heating_radiator.test.SetupTest import SetupTest


class HeatingRadiatorTest(SetupTest):

    def setUp(self) -> None:
        super().setUp()
        self.hassFacade.states["input_number.temp0"] = "19.0"

    def test_should(self):
        device = self.devices["heating_radiator_test_room0"]
        self.loop.run_until_complete(device.async_update())
        self.assertEqual(device.state_attributes["deviation"], -0.5)
        self.assertEqual(device.state_attributes["tick"], 1)


# def test_upper(self):
#     self.assertEqual('foo'.upper(), 'FOO')
#
# def test_isupper(self):
#     self.assertTrue('FOO'.isupper())
#     self.assertFalse('Foo'.isupper())
#
# def test_split(self):
#     s = 'hello world'
#     self.assertEqual(s.split(), ['hello', 'world'])
#     # check that s.split fails when the separator is not a string
#     with self.assertRaises(TypeError):
#         s.split(2)


if __name__ == '__main__':
    unittest.main()
