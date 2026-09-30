import unittest
from update_stats import collect


class PublicStatsTest(unittest.TestCase):
    def test_private_and_forked_repositories_never_enter_cards(self):
        calls = []

        def fetch(path):
            calls.append(path)
            if "/languages" in path:
                self.assertEqual(path, "/repos/ZephyrAki/project/languages")
                return {"Python": 300, "JavaScript": 100}
            return [
                {"name": "project", "private": False, "fork": False, "stargazers_count": 11, "forks_count": 3},
                {"name": "private-project", "private": True, "fork": False, "stargazers_count": 99, "forks_count": 99},
                {"name": "upstream-fork", "private": False, "fork": True, "stargazers_count": 99, "forks_count": 99},
            ]

        counts, languages = collect(fetch)
        self.assertEqual(counts, [1, 11, 3])
        self.assertEqual(languages, {"Python": 300, "JavaScript": 100})
        self.assertEqual(len(calls), 2)

    def test_pagination_continues_past_a_full_page(self):
        pages = []

        def fetch(path):
            pages.append(path)
            return [{"private": True, "fork": False}] * 100 if path.endswith("&page=1") else []

        self.assertEqual(collect(fetch), ([0, 0, 0], {}))
        self.assertEqual(len(pages), 2)
        self.assertIn("page=2", pages[1])


if __name__ == "__main__":
    unittest.main()
