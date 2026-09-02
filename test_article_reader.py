import unittest

from article_reader import build_story_urls


class BuildStoryUrlsTests(unittest.TestCase):
    def test_full_story_url_generates_part_sequence(self):
        urls = build_story_urls("https://humanhearttales.feji.io/full-story-she-stole-my-wedding-dress-then-the-security-footage-started-playing/")
        self.assertEqual(
            urls[:4],
            [
                "https://humanhearttales.feji.io/full-story-she-stole-my-wedding-dress-then-the-security-footage-started-playing/",
                "https://humanhearttales.feji.io/part-2-she-stole-my-wedding-dress-then-the-security-footage-started-playing/",
                "https://humanhearttales.feji.io/part-3-she-stole-my-wedding-dress-then-the-security-footage-started-playing/",
                "https://humanhearttales.feji.io/part-4-she-stole-my-wedding-dress-then-the-security-footage-started-playing/",
            ],
        )

    def test_part_url_continues_sequence(self):
        urls = build_story_urls("https://humanhearttales.feji.io/part-7-my-husband-asked-for-divorce-then-his-sisters-voice-filled-the-lawyers-office/")
        self.assertEqual(
            urls[:4],
            [
                "https://humanhearttales.feji.io/part-7-my-husband-asked-for-divorce-then-his-sisters-voice-filled-the-lawyers-office/",
                "https://humanhearttales.feji.io/part-8-my-husband-asked-for-divorce-then-his-sisters-voice-filled-the-lawyers-office/",
                "https://humanhearttales.feji.io/part-9-my-husband-asked-for-divorce-then-his-sisters-voice-filled-the-lawyers-office/",
                "https://humanhearttales.feji.io/part-10-my-husband-asked-for-divorce-then-his-sisters-voice-filled-the-lawyers-office/",
            ],
        )


if __name__ == "__main__":
    unittest.main()
