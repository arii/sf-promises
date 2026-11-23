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
