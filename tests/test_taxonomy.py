import unittest

from src.taxonomy import screen_taxonomy


class TaxonomyTests(unittest.TestCase):
    def test_allowed_labels_still_need_independent_review(self):
        self.assertEqual(screen_taxonomy(
            entity_name="City of San Francisco", entity_type="City Agency",
            sector="Housing & Land Use", neighborhood="Parkmerced",
            quote="We will build at Parkmerced.",
        ), [])

    def test_rejects_hallucinated_location_sector_and_spokesperson(self):
        failures = screen_taxonomy(
            entity_name="Company spokesperson", entity_type="Other",
            sector="Made up sector", neighborhood="Treasure Island",
            quote="We will build at Parkmerced.",
        )
        self.assertIn("entity_type_invalid", failures)
        self.assertIn("sector_invalid", failures)
        self.assertIn("spokesperson_not_entity", failures)
        self.assertIn("geography_conflict", failures)

    def test_regional_location_requires_an_independently_verified_sf_link(self):
        kwargs = dict(entity_name="State of California", entity_type="State Regulator",
                      sector="Housing & Land Use", neighborhood="Regional / Northern California",
                      quote="We will build homes.")
        self.assertIn("regional_sf_link_unverified", screen_taxonomy(**kwargs))
        self.assertNotIn("regional_sf_link_unverified",
                         screen_taxonomy(**kwargs, has_verified_sf_link=True))


if __name__ == "__main__":
    unittest.main()
