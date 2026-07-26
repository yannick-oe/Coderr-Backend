"""Tests for the paginated, filterable offer list endpoint."""

from datetime import timedelta

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from offers_app.models import Offer
from offers_app.tests.utils import make_user, offer_with

OFFERS_URL = "/api/offers/"
ENVELOPE_KEYS = {"count", "next", "previous", "results"}
ITEM_KEYS = [
    "id",
    "user",
    "title",
    "image",
    "description",
    "created_at",
    "updated_at",
    "details",
    "min_price",
    "min_delivery_time",
    "user_details",
]
USER_DETAILS_KEYS = ["first_name", "last_name", "username"]


class OfferListEnvelopeTests(APITestCase):
    """Envelope, item shape and pagination of the offer list."""

    def setUp(self):
        """Create one business user with one offer."""
        self.user = make_user("biz", ProfileType.BUSINESS)
        self.offer = offer_with(self.user, min_price=100, min_days=5)

    def bulk(self, count):
        """Create ``count`` extra offers for the same user."""
        for _ in range(count):
            offer_with(self.user, min_price=100, min_days=5)

    def test_envelope_keys_and_results_is_list(self):
        """The response is the paginated envelope with a list."""
        response = self.client.get(OFFERS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), ENVELOPE_KEYS)
        self.assertIsInstance(response.data["results"], list)

    def test_item_keys_in_order_with_user_details(self):
        """Each item has the exact keys and order, incl. user_details."""
        item = self.client.get(OFFERS_URL).data["results"][0]
        self.assertEqual(list(item), ITEM_KEYS)
        self.assertEqual(list(item["user_details"]), USER_DETAILS_KEYS)

    def test_details_are_absolute_id_url_links(self):
        """List details stay {id, url} links with absolute /api urls."""
        item = self.client.get(OFFERS_URL).data["results"][0]
        link = item["details"][0]
        self.assertEqual(list(link), ["id", "url"])
        self.assertIn("/api/offerdetails/", link["url"])

    def test_unauthenticated_access_succeeds(self):
        """The list is readable without authentication."""
        response = self.client.get(OFFERS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_default_page_size_is_six(self):
        """The first page holds six offers and links to the next."""
        self.bulk(6)
        data = self.client.get(OFFERS_URL).data
        self.assertEqual(len(data["results"]), 6)
        self.assertIsNotNone(data["next"])

    def test_second_page_has_the_remaining_offer(self):
        """The seventh offer appears on the second page."""
        self.bulk(6)
        data = self.client.get(f"{OFFERS_URL}?page=2").data
        self.assertEqual(len(data["results"]), 1)

    def test_page_size_parameter_overrides_default(self):
        """An explicit page_size caps the results per page."""
        self.bulk(3)
        data = self.client.get(f"{OFFERS_URL}?page_size=2").data
        self.assertEqual(len(data["results"]), 2)


class OfferListFilterTests(APITestCase):
    """Filtering and empty-parameter handling on the offer list."""

    def setUp(self):
        """Create two offers by two creators with distinct minimums."""
        self.a = make_user("a", ProfileType.BUSINESS)
        self.b = make_user("b", ProfileType.BUSINESS)
        self.o1 = offer_with(self.a, min_price=100, min_days=5)
        self.o2 = offer_with(self.b, min_price=300, min_days=15)
        self.both = {self.o1.id, self.o2.id}

    def ids(self, query=""):
        """Return the set of result ids for a query string."""
        response = self.client.get(f"{OFFERS_URL}{query}")
        return {item["id"] for item in response.data["results"]}

    def test_filter_by_creator_id(self):
        """creator_id keeps only that creator's offers."""
        self.assertEqual(self.ids(f"?creator_id={self.a.id}"), {self.o1.id})

    def test_min_price_is_a_lower_bound(self):
        """min_price keeps offers priced at or above the value."""
        self.assertEqual(self.ids("?min_price=200"), {self.o2.id})

    def test_max_delivery_time_is_an_upper_bound(self):
        """max_delivery_time keeps offers at or below the value."""
        self.assertEqual(self.ids("?max_delivery_time=10"), {self.o1.id})

    def test_empty_creator_id_is_no_filter(self):
        """An empty creator_id returns every offer."""
        self.assertEqual(self.ids("?creator_id="), self.both)

    def test_empty_min_price_is_no_filter(self):
        """An empty min_price returns every offer."""
        self.assertEqual(self.ids("?min_price="), self.both)

    def test_empty_max_delivery_time_is_no_filter(self):
        """An empty max_delivery_time returns every offer."""
        self.assertEqual(self.ids("?max_delivery_time="), self.both)

    def test_empty_search_is_no_filter(self):
        """An empty search returns every offer."""
        self.assertEqual(self.ids("?search="), self.both)

    def test_empty_ordering_is_no_filter(self):
        """An empty ordering returns every offer."""
        self.assertEqual(self.ids("?ordering="), self.both)

    def test_empty_page_defaults_to_first_page(self):
        """An empty page value serves the first page, not a 404."""
        response = self.client.get(f"{OFFERS_URL}?page=")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_full_empty_five_parameter_string(self):
        """The frontend's all-empty parameter string returns everything."""
        query = "?creator_id=&search=&ordering=&page=1&max_delivery_time="
        self.assertEqual(self.ids(query), self.both)

    def test_invalid_creator_id_returns_400(self):
        """A non-numeric creator_id is a genuine 400."""
        response = self.client.get(f"{OFFERS_URL}?creator_id=abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OfferListOrderingTests(APITestCase):
    """The four accepted ordering values produce the right sequence."""

    def setUp(self):
        """Create three offers with distinct prices and update times."""
        self.user = make_user("biz", ProfileType.BUSINESS)
        self.a = offer_with(self.user, min_price=300, min_days=10)
        self.b = offer_with(self.user, min_price=100, min_days=3)
        self.c = offer_with(self.user, min_price=200, min_days=5)
        self.stagger_updated_at()

    def stagger_updated_at(self):
        """Give a < b < c strictly increasing updated_at values."""
        base = timezone.now()
        for index, offer in enumerate([self.a, self.b, self.c]):
            Offer.objects.filter(pk=offer.pk).update(
                updated_at=base + timedelta(minutes=index)
            )

    def ids(self, ordering):
        """Return the ordered list of result ids."""
        response = self.client.get(f"{OFFERS_URL}?ordering={ordering}")
        return [item["id"] for item in response.data["results"]]

    def test_order_by_min_price_ascending(self):
        """min_price sorts cheapest first."""
        self.assertEqual(
            self.ids("min_price"), [self.b.id, self.c.id, self.a.id]
        )

    def test_order_by_min_price_descending(self):
        """-min_price sorts most expensive first."""
        self.assertEqual(
            self.ids("-min_price"), [self.a.id, self.c.id, self.b.id]
        )

    def test_order_by_updated_at_ascending(self):
        """updated_at sorts oldest first."""
        self.assertEqual(
            self.ids("updated_at"), [self.a.id, self.b.id, self.c.id]
        )

    def test_order_by_updated_at_descending(self):
        """-updated_at sorts newest first."""
        self.assertEqual(
            self.ids("-updated_at"), [self.c.id, self.b.id, self.a.id]
        )


class OfferListSearchTests(APITestCase):
    """Search matches the title and the description fields."""

    def setUp(self):
        """Create one offer matched by title and one by description."""
        self.user = make_user("biz", ProfileType.BUSINESS)
        self.by_title = self.make_offer("AlphaWidget", "plain")
        self.by_desc = self.make_offer("plain", "BetaSauce inside")

    def make_offer(self, title, description):
        """Create a searchable offer with title and description."""
        return offer_with(
            self.user,
            min_price=100,
            min_days=5,
            title=title,
            description=description,
        )

    def ids(self, term):
        """Return the set of result ids for a search term."""
        response = self.client.get(f"{OFFERS_URL}?search={term}")
        return {item["id"] for item in response.data["results"]}

    def test_search_matches_title(self):
        """A title word matches only the title offer."""
        self.assertEqual(self.ids("Alpha"), {self.by_title.id})

    def test_search_matches_description(self):
        """A description word matches only the description offer."""
        self.assertEqual(self.ids("Beta"), {self.by_desc.id})


class OfferListQueryCountTests(APITestCase):
    """The list endpoint issues a constant number of queries."""

    def setUp(self):
        """Create six offers for one business user."""
        self.user = make_user("biz", ProfileType.BUSINESS)
        for _ in range(6):
            offer_with(self.user, min_price=100, min_days=5)

    def test_query_count_constant_across_page_size(self):
        """A page of six uses the same query count as a page of one."""
        with CaptureQueriesContext(connection) as six:
            self.client.get(f"{OFFERS_URL}?page_size=6")
        with CaptureQueriesContext(connection) as one:
            self.client.get(f"{OFFERS_URL}?page_size=1")
        self.assertEqual(len(six.captured_queries), len(one.captured_queries))
