import unittest

from custom_components.heating_radiator.test.SetupTest import SetupTest


class HeatingRadiatorTest(SetupTest):

    def setUp(self) -> None:
        super().setUp()
        self.device0 = self.devices["heating_radiator_test_room0"]

    def test_return_attributes(self):
        self.hassFacade.states["input_number.temp0"] = "19.0"

        self.assertEqual(self.device0.state, 'idle')
        self.assertEqual(self.device0.state_attributes["deviation"], None)
        self.assertEqual(self.device0.state_attributes["current_temperature"], None)
        self.assertEqual(self.device0.state_attributes["target_temperature"], None)
        self.assertEqual(self.device0.state_attributes["target_temperature_patch"], None)
        self.assertEqual(self.device0.state_attributes["tick"], 0)
        self.assertEqual(self.device0.state_attributes["sleep_tick"], 0)
        self.assertEqual(self.device0.state_attributes["should_warmup"], False)

        for i in range(5):
            self.loop.run_until_complete(self.device0.async_update())
        self.assertEqual(self.device0.state, 'heating')
        self.assertEqual(self.device0.state_attributes["deviation"], -0.5)
        self.assertEqual(self.device0.state_attributes["current_temperature"], 19)
        self.assertEqual(self.device0.state_attributes["target_temperature"], 20)
        self.assertEqual(self.device0.state_attributes["target_temperature_patch"], 0)
        self.assertEqual(self.device0.state_attributes["tick"], 5)
        self.assertEqual(self.device0.state_attributes["sleep_tick"], 5)
        self.assertEqual(self.device0.state_attributes["should_warmup"], False)

    def test_enable_warmup_after_30min(self):
        self.hassFacade.states["input_number.temp0"] = "20.0"
        self.assertEqual(self.device0.state_attributes["should_warmup"], False, "Start state")
        for i in range(180):
            self.loop.run_until_complete(self.device0.async_update())
            self.assertEqual(self.device0.state_attributes["should_warmup"], False, f"Before switch state ({i})")

        self.loop.run_until_complete(self.device0.async_update())
        self.assertEqual(self.device0.state_attributes["should_warmup"], True, "Expected state")

    def test_reset_warmup_after_full_cycle(self):
        self.hassFacade.states["input_number.temp0"] = "20.0"
        for i in range(181):
            self.loop.run_until_complete(self.device0.async_update())
        self.assertEqual(self.device0.state_attributes["should_warmup"], True, "Active")

        self.hassFacade.states["input_number.temp0"] = "19.0"
        for i in range(29):
            self.loop.run_until_complete(self.device0.async_update())
            self.assertEqual(self.device0.state_attributes["should_warmup"], True, f"Active during cycle ({i})")

        self.loop.run_until_complete(self.device0.async_update())
        self.assertEqual(self.device0.state_attributes["should_warmup"], False, "Disable after cycle")

    def test_work_time_depend_on_deviation(self):
        self.hassFacade.states["input_number.temp0"] = "19.0"
        self.assertEqual(self.device0.state, "idle")
        for i in range(6):
            self.loop.run_until_complete(self.device0.async_update())
            self.assertEqual(self.device0.state, "heating", f"19.0 {i}")
        for i in range(24):
            self.loop.run_until_complete(self.device0.async_update())
            self.assertEqual(self.device0.state, "pause", f"19.0 {i}")

        self.hassFacade.states["input_number.temp0"] = "18.5"
        for i in range(9):
            self.loop.run_until_complete(self.device0.async_update())
            self.assertEqual(self.device0.state, "heating", f"18.5 {i}")
        for i in range(21):
            self.loop.run_until_complete(self.device0.async_update())
            self.assertEqual(self.device0.state, "pause", f"18.5 {i}")

        self.hassFacade.states["input_number.temp0"] = "20.0"
        self.loop.run_until_complete(self.device0.async_update())
        self.assertEqual(self.device0.state, "idle", f"20")

    def test_minimal_work_time(self):
        self.hassFacade.states["input_number.temp0"] = "19.99"
        self.assertEqual(self.device0.state, "idle")
        for i in range(3):
            self.loop.run_until_complete(self.device0.async_update())
            self.assertEqual(self.device0.state, "heating", f"19.99 {i}")
        for i in range(27):
            self.loop.run_until_complete(self.device0.async_update())
            self.assertEqual(self.device0.state, "pause", f"19.99 {i}")

        self.hassFacade.states["input_number.temp0"] = "20.0"
        self.loop.run_until_complete(self.device0.async_update())
        self.assertEqual(self.device0.state, "idle", "20.0")

    def test_maximum_work_time(self):
        self.hassFacade.states["input_number.temp0"] = "17"
        self.assertEqual(self.device0.state, "idle")
        for i in range(12):
            self.loop.run_until_complete(self.device0.async_update())
            self.assertEqual(self.device0.state, "heating", f"17 {i}")
        for i in range(18):
            self.loop.run_until_complete(self.device0.async_update())
            self.assertEqual(self.device0.state, "pause", f"17 {i}")

        self.hassFacade.states["input_number.temp0"] = "20.0"
        self.loop.run_until_complete(self.device0.async_update())
        self.assertEqual(self.device0.state, "idle", "20.0")

    def test_minimal_work_time_with_warmup(self):
        self.hassFacade.states["input_number.temp0"] = "20.0"
        for i in range(181):
            self.loop.run_until_complete(self.device0.async_update())
        self.assertEqual(self.device0.state_attributes["should_warmup"], True, "Active")

        self.hassFacade.states["input_number.temp0"] = "19.99"
        for i in range(5):
            self.loop.run_until_complete(self.device0.async_update())
            self.assertEqual(self.device0.state, "heating", f"19.99 {i}")
        for i in range(25):
            self.loop.run_until_complete(self.device0.async_update())
            self.assertEqual(self.device0.state, "pause", f"19.99 {i}")

        self.hassFacade.states["input_number.temp0"] = "20.0"
        self.loop.run_until_complete(self.device0.async_update())
        self.assertEqual(self.device0.state, "idle", "20")

    def test_maximum_work_time_with_warmup(self):
        self.hassFacade.states["input_number.temp0"] = "20.0"
        for i in range(181):
            self.loop.run_until_complete(self.device0.async_update())
        self.assertEqual(self.device0.state_attributes["should_warmup"], True, "Active")

        self.hassFacade.states["input_number.temp0"] = "17"
        for i in range(14):
            self.loop.run_until_complete(self.device0.async_update())
            self.assertEqual(self.device0.state, "heating", f"17 {i}")
        for i in range(16):
            self.loop.run_until_complete(self.device0.async_update())
            self.assertEqual(self.device0.state, "pause", f"17 {i}")

        self.hassFacade.states["input_number.temp0"] = "20.0"
        self.loop.run_until_complete(self.device0.async_update())
        self.assertEqual(self.device0.state, "idle", "20.0")

    def test_patch_from_device(self):
        self.hassFacade.states["input_number.temp0"] = "20.0"
        self.hassFacade.condition["cond_0"].return_value = True
        self.loop.run_until_complete(self.device0.async_update())
        self.assertEqual(self.device0.state_attributes["target_temperature"], 22)

        self.hassFacade.condition["cond_1"].return_value = True
        self.loop.run_until_complete(self.device0.async_update())
        self.assertEqual(self.device0.state_attributes["target_temperature"], 12)

    def test_patch_from_global(self):
        self.hassFacade.states["input_number.temp0"] = "20.0"
        self.hassFacade.condition["global_0"].return_value = True
        self.loop.run_until_complete(self.device0.async_update())
        self.assertEqual(self.device0.state_attributes["target_temperature"], 15)


if __name__ == '__main__':
    unittest.main()
