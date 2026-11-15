import unittest
from core.models import CharacterProfile, GameSession


class TestBusinessLogic(unittest.TestCase):

    def test_damage_formulas(self):
        attacker = CharacterProfile("Warrior", "Warrior", 100, 30, 5, 0.0, 100)
        defender = CharacterProfile("Target", "Monster", 100, 20, 10, 0.2, 90)

        # Physical damage: max(0, 30 - 10) * (1 - 0.2) = 20 * 0.8 = 16
        phys_dmg = attacker.calculate_physical_damage(defender)
        self.assertEqual(phys_dmg, 16)

        # Magic damage ignoring armor with res_pen 0.1: effective resist = 0.2 - 0.1 = 0.1; 30 * 0.9 = 27
        magic_dmg = attacker.calculate_magic_damage(defender, res_pen=0.1)
        self.assertEqual(magic_dmg, 27)

    def test_game_turn_and_history(self):
        session = GameSession()
        session.select_character(0)
        session.start_game()
        self.assertTrue(session.is_active)
        self.assertGreater(len(session.history), 0)

        res = session.execute_player_attack()
        self.assertIn("завдає", res)
        self.assertGreaterEqual(len(session.history), 2)


if __name__ == "__main__":
    unittest.main()
