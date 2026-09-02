import unittest
from scraper_engine import StoryScraper, StoryArticle, StoryPart

class ScraperEngineTests(unittest.TestCase):
    def setUp(self):
        self.scraper = StoryScraper()

    def test_clean_title(self):
        t1 = self.scraper.clean_title("A battered suitcase on my kitchen floor ended my twenty-three year marriage - America Focus")
        self.assertEqual(t1, "A battered suitcase on my kitchen floor ended my twenty-three year marriage")

        t2 = self.scraper.clean_title("FULL STORY – She Stole My Wedding Dress–Then the Security Footage Started Playing - DAILY STORIES")
        self.assertEqual(t2, "She Stole My Wedding Dress–Then the Security Footage Started Playing")

        t3 = self.scraper.clean_title("Part 2: Hours After My Divorce Became Final - LEVANEWS")
        self.assertEqual(t3, "Hours After My Divorce Became Final")

    def test_fanstopis_scrape(self):
        url = "https://fanstopis.com/my-wife-was-about-to-be-burie"
        article = self.scraper.scrape(url)
        self.assertEqual(article.total_parts, 3)
        self.assertTrue(article.total_words > 1000)
        self.assertTrue("coffin" in article.title.lower() or "wife" in article.title.lower())
        self.assertTrue("coffin" in article.parts[0].text.lower())
        self.assertTrue("choices define" in article.parts[2].text.lower() or "relatives" in article.parts[2].text.lower())

    def test_levanews_scrape(self):
        url = "https://levanews.com/hours-after-my-divorce-became-final-my-former-mother-in-law-tried-to-charge-a-48000-auction-purchase-to-my-credit-card-but-i-had-already-canceled-it-by-the-next-morning-my-ex-husband-was-having/"
        article = self.scraper.scrape(url)
        self.assertEqual(article.total_parts, 3)
        self.assertTrue(article.total_words > 2000)
        self.assertTrue("divorce" in article.title.lower())
        self.assertTrue("divorce became official" in article.parts[0].text.lower())

    def test_feji_scrape(self):
        url = "https://humanhearttales.feji.io/full-story-she-stole-my-wedding-dress-then-the-security-footage-started-playing/"
        article = self.scraper.scrape(url)
        self.assertEqual(article.total_parts, 9)
        self.assertTrue(article.total_words > 3000)
        self.assertTrue("dress" in article.title.lower() or "security" in article.title.lower())
        self.assertTrue("television screen flickered" in article.parts[0].text.lower())
        self.assertTrue("look like myself" in article.parts[-1].text.lower())

    def test_export_formats(self):
        article = StoryArticle(
            title="Test Story Title",
            original_url="https://example.com/story",
            domain="example.com",
            parts=[
                StoryPart(part_num=1, url="https://example.com/story/1", paragraphs=["Paragraph one of part one.", "Paragraph two of part one."]),
                StoryPart(part_num=2, url="https://example.com/story/2", paragraphs=["Paragraph one of part two.", "Final conclusion paragraph."])
            ]
        )
        txt = article.to_text(include_metadata=True, include_part_headers=True)
        self.assertIn("TEST STORY TITLE", txt)
        self.assertIn("Part 1", txt)
        self.assertIn("Part 2", txt)
        self.assertIn("Final conclusion paragraph.", txt)

        pure_body = article.to_pure_body()
        self.assertNotIn("TEST STORY TITLE", pure_body)
        self.assertNotIn("━━━━━━━━", pure_body)
        self.assertIn("Final conclusion paragraph.", pure_body)

        md = article.to_markdown()
        self.assertIn("# Test Story Title", md)
        self.assertIn("## Part 1", md)

        html_out = article.to_html()
        self.assertIn("<!DOCTYPE html>", html_out)
        self.assertIn("Test Story Title", html_out)
        self.assertIn("www.deainnovations.com", html_out)

if __name__ == "__main__":
    unittest.main()
