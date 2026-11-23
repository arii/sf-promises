import unittest

import httpx
from keenable import KeenableAPIError, KeenableRateLimitError

from src.keenable import RetryingKeenable


class KeenableRetryTests(unittest.IsolatedAsyncioTestCase):
    async def test_respects_retry_after_then_retries(self):
        requests = []
        sleeps = []

        def handler(request):
            requests.append(request)
            if len(requests) == 1:
                return httpx.Response(429, headers={"Retry-After": "3"}, json={"error": "limited"})
            return httpx.Response(200, json={"results": []})

        async def sleep(seconds):
            sleeps.append(seconds)

        async with RetryingKeenable(
            api_key="test-key", transport=httpx.MockTransport(handler), sleep=sleep
        ) as client:
            result = await client.search("library", max_results=3)
        self.assertEqual(len(result.results), 0)
        self.assertEqual(len(requests), 2)
        self.assertEqual(sleeps, [3])

    async def test_missing_or_excessive_retry_after_is_blocked(self):
        for headers in ({}, {"Retry-After": "999"}):
            requests = []

            def handler(request):
                requests.append(request)
                return httpx.Response(429, headers=headers, json={"error": "limited"})

            async with RetryingKeenable(
                api_key="test-key", transport=httpx.MockTransport(handler)
            ) as client:
                with self.assertRaises(KeenableRateLimitError):
                    await client.search("library")
            self.assertEqual(len(requests), 1)

    async def test_transient_gateway_error_is_retried_then_succeeds(self):
        requests, sleeps = [], []

        def handler(request):
            requests.append(request)
            if len(requests) == 1:
                return httpx.Response(502, text="<html>502 Server Error</html>")
            return httpx.Response(200, json={"results": []})

        async def sleep(seconds):
            sleeps.append(seconds)

        async with RetryingKeenable(
            api_key="test-key", transport=httpx.MockTransport(handler), sleep=sleep
        ) as client:
            result = await client.search("library")
        self.assertEqual(len(result.results), 0)
        self.assertEqual(len(requests), 2)
        self.assertEqual(sleeps, [30])

    async def test_persistent_gateway_error_is_bounded(self):
        requests, sleeps = [], []

        def handler(request):
            requests.append(request)
            return httpx.Response(503, text="unavailable")

        async def sleep(seconds):
            sleeps.append(seconds)

        async with RetryingKeenable(
            api_key="test-key", transport=httpx.MockTransport(handler), sleep=sleep
        ) as client:
            with self.assertRaises(KeenableAPIError):
                await client.search("library")
        self.assertEqual(len(requests), 3)
        self.assertEqual(sleeps, [30, 30])

    async def test_connection_timeout_is_retried_then_succeeds(self):
        requests, sleeps = [], []

        def handler(request):
            requests.append(request)
            if len(requests) == 1:
                raise httpx.ReadTimeout("timed out", request=request)
            return httpx.Response(200, json={"results": []})

        async def sleep(seconds):
            sleeps.append(seconds)

        async with RetryingKeenable(
            api_key="test-key", transport=httpx.MockTransport(handler), sleep=sleep
        ) as client:
            result = await client.search("library")
        self.assertEqual(len(result.results), 0)
        self.assertEqual(len(requests), 2)
        self.assertEqual(sleeps, [30])

    async def test_persistent_connection_timeout_is_bounded(self):
        requests, sleeps = [], []

        def handler(request):
            requests.append(request)
            raise httpx.ReadTimeout("timed out", request=request)

        async def sleep(seconds):
            sleeps.append(seconds)

        async with RetryingKeenable(
            api_key="test-key", transport=httpx.MockTransport(handler), sleep=sleep
        ) as client:
            from keenable import KeenableConnectionError
            with self.assertRaises(KeenableConnectionError):
                await client.search("library")
        self.assertEqual(len(requests), 3)
        self.assertEqual(sleeps, [30, 30])

    async def test_client_errors_are_not_retried(self):
        for status in (400, 401, 403, 422):
            requests = []

            def handler(request):
                requests.append(request)
                return httpx.Response(status, json={"error": "rejected"})

            with self.subTest(status=status):
                async with RetryingKeenable(
                    api_key="test-key", transport=httpx.MockTransport(handler)
                ) as client:
                    with self.assertRaises(KeenableAPIError):
                        await client.search("library")
                self.assertEqual(len(requests), 1)

    async def test_payment_error_is_not_retried(self):
        requests = []

        def handler(request):
            requests.append(request)
            return httpx.Response(402, json={"error": "quota exhausted"})

        async with RetryingKeenable(
            api_key="test-key", transport=httpx.MockTransport(handler)
        ) as client:
            with self.assertRaises(KeenableAPIError):
                await client.search("library")
        self.assertEqual(len(requests), 1)

    async def test_options_reach_the_wire_and_page_error_is_not_retried(self):
        import json

        requests = []

        def handler(request):
            requests.append((request.url.path, json.loads(request.content)))
            if request.url.path.endswith("/fetch"):
                return httpx.Response(200, json={"results": [{
                    "url": "https://sf.gov/x",
                    "error": {"status": 404, "error": "not found"}}]})
            return httpx.Response(200, json={"results": []})

        async with RetryingKeenable(
            api_key="test-key", transport=httpx.MockTransport(handler)
        ) as client:
            await client.search("library", max_results=25, disable_cards=True,
                                exclude_domains=["reddit.com"], objective="find it")
            page = (await client.fetch("https://sf.gov/x", max_chars=400000)).results[0]
        self.assertEqual(page.error.status, 404)
        self.assertEqual(len(requests), 2)
        search_body, fetch_body = requests[0][1], requests[1][1]
        self.assertEqual(search_body["max_results"], 25)
        self.assertEqual(search_body["exclude_domains"], ["reddit.com"])
        self.assertEqual(search_body["objective"], "find it")
        self.assertIn("disable_cards", json.dumps(search_body))
        self.assertEqual(fetch_body["content"]["max_chars"], 400000)
