import pytest

from app.utils import setup_logger, typo_checker


logger = setup_logger(__name__)


class TestTypoVariations:

    @pytest.mark.parametrize(
        "original,typo,expected_found",
        [
            ("bank of the james financial", "ank of the james financial", True),
            ("west holdings corp", "wst holdings corp", True),
            ("robert half inc", "robert alf inc", True),
            ("xcel energy inc", "xce energy inc", True),
            ("berry corp", "bery corp", True),
            (
                "bank of the james financial",
                "bankk of the james financial",
                True,
            ),
            ("west holdings corp", "wesst holdings corp", True),
            ("robert half inc", "robert halff inc", True),
            ("xcel energy inc", "xcel energyy inc", True),
            ("berry corp", "berryy corp", True),
            (
                "bank of the james financial",
                "bonk of the james financial",
                True,
            ),
            ("west holdings corp", "wost holdings corp", True),
            ("robert half inc", "robert holf inc", True),
            ("xcel energy inc", "xcel energe inc", True),
            ("berry corp", "barry corp", True),
            (
                "bank of the james financial",
                "abnk of the james financial",
                True,
            ),
            ("west holdings corp", "ewst holdings corp", True),
            ("robert half inc", "robert hlaf inc", True),
            (
                "xcel energy inc",
                "xccel energy inc",
                True,
            ),
            ("berry corp", "beryr corp", True),
            ("bank of the james financial", "bak of te james financial", True),
            ("west holdings corp", "wst holdin corp", True),
            ("robert half inc", "robet haf inc", True),
            ("xcel energy inc", "xl enrgy inc", True),
            ("berry corp", "bery cop", True),
            (
                "bank of the james financial",
                "bank f the james financial",
                True,
            ),
            (
                "west holdings corp",
                "west holding corp",
                True,
            ),
            ("robert half inc", "robt haf inc", True),
            (
                "xcel energy inc",
                "xcl engy inc",
                True,
            ),
            ("berry corp", "bery co", True),
            (
                "bank of the james financial",
                "bk of t james financial",
                False,
            ),
            ("west holdings corp", "ws holdi corp", False),
            ("robert half inc", "robt ha inc", False),
            ("xcel energy inc", "xl engy inc", False),
            ("berry corp", "ber co", False),
        ],
    )
    def test_character_modifications(self, original, typo, expected_found):
        suggestions = typo_checker.requires_check(typo)

        if expected_found:
            assert (
                len(suggestions) > 0
            ), f"Expected suggestions for '{typo}' -> '{original}'"
            suggestion_names = [s[0] for s in suggestions]
            assert (
                original in suggestion_names
            ), f"Expected '{original}' in suggestions for '{typo}'"
        else:
            suggestion_names = (
                [s[0] for s in suggestions] if suggestions else []
            )
            assert (
                original not in suggestion_names
            ), f"Did not expect '{original}' in suggestions for '{typo}'"

    @pytest.mark.parametrize(
        "original,typo_variations",
        [
            (
                "avecho biotechnology ltd",
                [
                    "avech biotechnology ltd",
                    "avechoo biotechnology ltd",
                    "avecho biotechnolgy ltd",
                    "aevcho biotechnology ltd",
                    "avch biotechnology ltd",
                ],
            ),
            (
                "masterworks 127 llc ltd cl a",
                [
                    "masterwork 127 llc ltd cl a",
                    "masterworkss 127 llc ltd cl a",
                    "masterworks 127 llc ltd cl o",
                    "amsterworks 127 llc ltd cl a",
                    "masterwrks 127 llc ltd cl a",
                ],
            ),
            (
                "allegro microsystems inc",
                [
                    "allegr microsystems inc",
                    "allegro microsystemss inc",
                    "allegro microsystems onc",
                    "alelgro microsystems inc",
                    "allegro microsystes inc",
                ],
            ),
        ],
    )
    def test_typo_variations(self, original, typo_variations):
        for typo in typo_variations:
            suggestions = typo_checker.requires_check(typo)
            assert len(suggestions) > 0, f"No suggestions found for '{typo}'"

            suggestion_names = [s[0] for s in suggestions]
            assert (
                original in suggestion_names
            ), f"Expected '{original}' in suggestions for '{typo}'"


class TestTypoAccuracy:

    def load_typo_test_data(self):
        test_pairs = []
        with open("tests/examples/typo_test.txt") as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split("\t")
                    if len(parts) == 2:
                        correct, typo = parts
                        test_pairs.append((correct, typo))
        return test_pairs

    def test_typo_correction_accuracy(self):
        test_pairs = self.load_typo_test_data()

        total_tests = len(test_pairs)
        correct_predictions = 0
        no_suggestions = 0

        for correct_name, typo in test_pairs:
            suggestions = typo_checker.requires_check(typo)

            if not suggestions:
                no_suggestions += 1
                continue

            suggestion_names = [s[0] for s in suggestions]

            if correct_name in suggestion_names:
                correct_predictions += 1

        accuracy = correct_predictions / total_tests if total_tests > 0 else 0

        logger.info(f"Total test cases: {total_tests}", "BLUE")
        logger.info(f"Correct predictions: {correct_predictions}", "BLUE")
        logger.info(f"No suggestions provided: {no_suggestions}", "BLUE")
        logger.info(f"Accuracy: {accuracy:.2%}", "BLUE")
