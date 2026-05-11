import asyncio
import os
import tempfile
import unittest
from pathlib import Path

from playwright.async_api import async_playwright

from core.interaction_manager import InteractionManager
from core.post_manager import PostManager


FIXTURES = Path(__file__).parent / "fixtures"


def fixture_url(name: str) -> str:
    return (FIXTURES / name).resolve().as_uri()


class ManagerFlowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def asyncTearDown(self):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    async def test_create_post_dry_run_fills_fields_without_publish(self):
        manager = PostManager(
            self.page,
            dry_run=True,
            create_post_url=fixture_url("create_post.html"),
        )
        manager.delay = self._no_delay

        result = await manager.create_post("Hello dry run body", title="Hello dry run")

        self.assertTrue(result["ok"])
        self.assertTrue(result["dry_run"])
        self.assertFalse(result["submitted"])
        self.assertTrue(result["category_selected"])
        self.assertEqual(await self.page.locator("#subject").input_value(), "Hello dry run")
        self.assertIn("Hello dry run body", await self.page.locator(".w-e-text").inner_text())
        self.assertEqual(await self.page.locator("#communityId-columnId").input_value(), "异环 / 「呗果」揭示板")
        self.assertEqual(
            await self.page.evaluate("window.categoryClicks"),
            ["异环", "「呗果」揭示板"],
        )
        self.assertFalse(await self.page.evaluate("window.publishClicked"))

    async def test_create_post_dry_run_skips_existing_image_path(self):
        manager = PostManager(
            self.page,
            dry_run=True,
            create_post_url=fixture_url("create_post.html"),
        )
        manager.delay = self._no_delay

        with tempfile.NamedTemporaryFile(suffix=".png") as image_file:
            result = await manager.create_post(
                "Hello dry run body",
                image_path=image_file.name,
                title="Hello dry run",
            )

        self.assertTrue(result["ok"])
        self.assertFalse(result["image_uploaded"])
        self.assertEqual(await self.page.locator('input[type="file"]').input_value(), "")

    async def test_reply_dry_run_fills_replies_without_sending(self):
        manager = InteractionManager(
            self.page,
            dry_run=True,
            reply_url=fixture_url("notifications.html"),
        )
        manager.delay = self._no_delay

        result = await manager.reply_to_comments()

        self.assertTrue(result["ok"])
        self.assertEqual(result["would_reply_count"], 2)
        self.assertEqual(result["replied_count"], 0)
        self.assertEqual(await self.page.locator(".reply-editor").input_value(), "")
        self.assertEqual(await self.page.evaluate("window.sendClicked"), 0)

    async def test_browse_and_like_zero_limit_exits_cleanly(self):
        manager = InteractionManager(self.page, dry_run=True)
        result = await manager.browse_and_like(fixture_url("feed.html"), max_likes=0)

        self.assertTrue(result["ok"])
        self.assertEqual(result["would_like_count"], 0)
        self.assertEqual(result["processed_post_ids"], [])

    async def test_browse_and_like_dry_run_counts_without_clicking(self):
        manager = InteractionManager(
            self.page,
            dry_run=True,
            post_url_template=fixture_url("post_detail_unliked.html") + "?post_id={post_id}",
        )
        manager.delay = self._no_delay

        result = await manager.browse_and_like(fixture_url("feed.html"), max_likes=1, max_time_minutes=0.1)

        self.assertTrue(result["ok"])
        self.assertEqual(result["liked_count"], 0)
        self.assertEqual(result["would_like_count"], 1)
        self.assertEqual(len(result["processed_post_ids"]), 1)

    async def test_extract_post_ids_from_response_body(self):
        body = '{"postId": 12345, "uid": 99999, "postStat": {"postId": "67890"}}'
        self.assertEqual(InteractionManager.extract_post_ids(body), {"12345", "67890"})

    async def test_extract_post_id_from_href(self):
        self.assertEqual(InteractionManager.extract_post_id_from_href("#/post?postId=12345"), "12345")
        self.assertEqual(InteractionManager.extract_post_id_from_href("/post/67890"), "67890")
        self.assertIsNone(InteractionManager.extract_post_id_from_href("#/user?id=12345"))

    async def test_like_state_detection(self):
        manager = InteractionManager(self.page, dry_run=True)

        await self.page.goto(fixture_url("post_detail_unliked.html"))
        unliked = await manager.find_like_button(self.page)
        self.assertFalse(await manager.is_already_liked(unliked))

        await self.page.goto(fixture_url("post_detail_liked.html"))
        liked = await manager.find_like_button(self.page)
        self.assertTrue(await manager.is_already_liked(liked))

    async def _no_delay(self, *_args, **_kwargs):
        await asyncio.sleep(0)


class MainExampleTests(unittest.TestCase):
    def test_main_example_uses_target_url_not_removed_tag_argument(self):
        main_source = Path("main.py").read_text(encoding="utf-8")
        self.assertNotIn("browse_and_like(tag=", main_source)
        self.assertIn("target_url=TARGET_URL", main_source)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    unittest.main()
