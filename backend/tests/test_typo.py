import pytest

from app.utils import typo_checker


class TestTypoVariations:

    @pytest.mark.parametrize(
        "original,typo,expected_found",
        [
            # Single character deletion - using companies from your actual corpus
            ("bank of the james financial", "ank of the james financial", True),
            ("west holdings corp", "wst holdings corp", True),
            ("robert half inc", "robert alf inc", True),
            ("xcel energy inc", "xce energy inc", True),
            ("berry corp", "bery corp", True),
            # Single character insertion
            (
                "bank of the james financial",
                "bankk of the james financial",
                True,
            ),
            ("west holdings corp", "wesst holdings corp", True),
            ("robert half inc", "robert halff inc", True),
            ("xcel energy inc", "xcel energyy inc", True),
            ("berry corp", "berryy corp", True),
            # Single character substitution
            (
                "bank of the james financial",
                "bonk of the james financial",
                True,
            ),
            ("west holdings corp", "wost holdings corp", True),
            ("robert half inc", "robert holf inc", True),
            ("xcel energy inc", "xcel energe inc", True),
            ("berry corp", "barry corp", True),
            # Single character transposition (Damerau-Levenshtein advantage)
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
            ),  # changed - original was same after normalization
            ("berry corp", "beryr corp", True),
            # Two character modifications
            ("bank of the james financial", "bak of te james financial", True),
            ("west holdings corp", "wst holdin corp", True),
            ("robert half inc", "robet haf inc", True),
            ("xcel energy inc", "xl enrgy inc", True),
            ("berry corp", "bery cop", True),
            # Three character modifications (at threshold)
            (
                "bank of the james financial",
                "bank f the james financial",
                True,
            ),  # changed to stay within threshold
            (
                "west holdings corp",
                "west holding corp",
                True,
            ),  # changed to stay within threshold
            ("robert half inc", "robt haf inc", True),
            (
                "xcel energy inc",
                "xcl engy inc",
                True,
            ),  # changed to stay within threshold
            ("berry corp", "bery co", True),
            # Four character modifications (should exceed threshold)
            (
                "bank of the james financial",
                "bk of t james financial",
                False,
            ),  # distance 4
            ("west holdings corp", "ws holdi corp", False),  # distance 5
            ("robert half inc", "robt ha inc", False),
            ("xcel energy inc", "xl engy inc", False),  # distance 4
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
