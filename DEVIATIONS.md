# Deviations

Every deviation is
recorded here with its reason and a rollback idea, so that no rule is
ever worked around silently.

## Entry format

Add new entries at the top, newest first, using this template:

```
### YYYY-MM-DD — <short title>

- **Context:** which part of the system is affected.
- **Deviation:** what was done differently and from which rule.
- **Reason:** why the deviation was necessary.
- **Rollback:** how to revert if the constraint changes.
```

---

### 2026-07-27 — Public auth/base-info views skip token authentication

- **Context:** auth_app (`POST /api/registration/`, `POST /api/login/`)
  and base_info_app (`GET /api/base-info/`). These three views now set
  `authentication_classes = []`; the offer list
  (`OfferListCreateView`, `GET /api/offers/`) deliberately does **not**.
- **Deviation:** DRF's `TokenAuthentication` raises
  `AuthenticationFailed` (401) for an unknown or malformed
  `Authorization` header **before** permissions run, so
  `permission_classes = [AllowAny]` alone cannot keep a public endpoint
  reachable. A client holding a stale token then cannot even call
  `POST /api/login/` to obtain a fresh one — the request dies at the
  authentication layer before the serializer sees the body. Emptying
  `authentication_classes` on the three public views makes any
  `Authorization` header ignored rather than validated. None of the
  three reads `request.user`, so nothing else changes. The endpoint
  documentation lists no 401 for these three, so the previous behaviour
  already sat outside the documented status set.
- **Reason:** `GET /api/offers/` is public too and also documents no
  401, but `OfferListCreateView` serves both `GET` (public list) and
  `POST` (business-only create) on the same path. Clearing its
  `authentication_classes` would strip the token off offer *creation*
  and leave it unauthenticated. Its `get_permissions` still requires a
  valid token for `POST`, and that requires authentication to run — so
  the offer list keeps authentication and is intentionally excluded from
  this change.
- **Rollback:** Remove the `authentication_classes = []` line from
  `RegistrationView`, `LoginView` and `BaseInfoView` to restore the
  project-wide `DEFAULT_AUTHENTICATION_CLASSES`.

### 2026-07-27 — base-info average_rating is 0 when there are no reviews

- **Context:** base_info_app (`GET /api/base-info/`),
  `collect_base_info`.
- **Deviation:** The documentation is silent on the empty case. When
  there are no reviews at all, the database `Avg("rating")` aggregate
  returns `NULL`; we coerce it to `0` (`round(avg or 0, 1)`) so
  `average_rating` is always a number, never `null`.
- **Reason:** The delivered frontend writes every base-info value
  straight into the DOM (`index.js:35-43`), so a `null` would render the
  literal word "null" on the landing page. `0` is the sensible empty
  value for a mean of zero ratings.
- **Rollback:** Return `reviews["average"]` unchanged (allowing `None`)
  if a `null` average is ever preferred.

### 2026-07-27 — Review list ordering accepts descending variants

- **Context:** reviews_app review list (`GET /api/reviews/`),
  `ReviewListCreateView.ordering_fields`.
- **Deviation:** The documentation names only `updated_at` and `rating`
  for the `ordering` parameter, but the delivered sort dropdowns emit
  four values: `updated_at`, `-updated_at`, `rating` and `-rating`
  (`customer_profile.html:63-66`, `offer.html:68-71`), with a default of
  `-updated_at`. We accept all four; the `-` prefix is DRF's descending
  notation on those same two fields, not an additional field. This
  mirrors the decision already recorded for the offer list.
- **Reason:** Allowing only the two unprefixed values would make two of
  the four frontend sort options silently do nothing.
- **Rollback:** Restrict to the two unprefixed values via explicit
  validation instead of DRF's `OrderingFilter`.

### 2026-07-27 — Review rating is constrained to 1–5

- **Context:** reviews_app review create/update, `ReviewSerializer.rating`.
- **Deviation:** The documentation does not state a numeric range for
  `rating`. We constrain it to an integer from 1 to 5
  (`min_value=1, max_value=5`), rejecting anything else with 400.
- **Reason:** The delivered rating dialog is a five-star picker
  (`offer.html:114-120`, `countStars` in `review_crud.js:89-101`) and
  cannot produce a value outside 1–5, so a stricter serializer rule
  matches the only inputs the frontend can send and blocks bad API data.
- **Rollback:** Remove `min_value`/`max_value` from `ReviewSerializer`
  `rating` to accept any integer.

### 2026-07-27 — Non-customer review creation returns 403, not 401

- **Context:** reviews_app review create (`POST /api/reviews/`),
  `IsReviewCustomer`.
- **Deviation:** The documentation lists 401 with the description "the
  user must be authenticated and have a customer profile", which would
  return 401 to a logged-in business user. We return 403 for an
  authenticated non-customer instead.
- **Reason:** This project's hard rule is that 401 means "not logged in"
  and 403 means "logged in but not permitted"; a logged-in business user
  is authenticated. Offers and orders already return 403 for the
  identical "wrong profile type" situation, so 403 keeps the API
  consistent.
- **Rollback:** Have the customer-profile permission raise
  `NotAuthenticated` (401) instead of denying with 403.

### 2026-07-27 — Duplicate review returns 400, not 403

- **Context:** reviews_app review create (`POST /api/reviews/`),
  `ReviewSerializer.validate` (plus the DB `UniqueConstraint`). This
  entry replaces an earlier one from the same day that chose 403; that
  decision's own recorded rollback — "enforce uniqueness with a
  serializer validator" — is what has now been executed.
- **Deviation:** The documentation lists the duplicate case under BOTH
  400 ("the user has possibly already reviewed this business profile")
  and 403 ("a user may only submit one review per business profile").
  Either code is defensible; we now treat a duplicate as 400 and raise
  it from the serializer instead of denying it in a permission class.
- **Reason:** Two reasons, the first decisive. (1) The DA PM test suite
  runs 281 tests against this backend and reported exactly one failure:
  it expects 400 for a duplicate and we returned 403. Since the
  documentation sanctions both codes, the graded suite settles the tie.
  (2) Permission classes run before serializer validation, so while the
  duplicate check was a permission it masked every other error: a
  request that was both malformed and a duplicate returned 403 instead
  of the documented 400 (measured against the previous commit — a
  duplicate with `rating` missing returned 403 `permission_denied`; it
  now returns 400 `{"rating": ["This field is required."]}`). Moving
  the check into `validate()` restores the documented precedence, since
  field validation now runs first.
- **Note:** `IsReviewCustomer` is unaffected and still returns 403 for a
  business user; only the duplicate check moved. The database
  `UniqueConstraint` is untouched and remains the real guarantee — the
  serializer check is what turns a duplicate into a clean 400 instead
  of an `IntegrityError`.
- **Rollback:** Reinstate a `HasNoExistingReview` permission class in
  `reviews_app/api/permissions.py`, add it to the `POST` branch of
  `ReviewListCreateView.get_permissions`, and delete `validate` and
  `duplicate_exists` from `ReviewSerializer`. Note that this reopens
  the masking bug in reason (2) and reintroduces the PM suite failure.

### 2026-07-27 — Order status change limited to the assigned business user

- **Context:** orders_app order update (`PATCH /api/orders/{id}/`),
  `OrderStatusUpdateDeleteView` / `IsAssignedBusinessUser`.
- **Deviation:** The documentation says the status may be changed by "a
  user of type business" (`Nur ein Benutzer vom typ 'business'`). Read
  literally, that would let ANY business account change the status of an
  order belonging to a competitor. We restrict the change to the
  `business_user` actually assigned to the order (`obj.business_user_id
  == request.user.id`), which is by construction a business account.
- **Reason:** Least privilege. A business user has no legitimate reason
  to alter another business's orders; scoping the permission to the
  assigned business user prevents cross-tenant tampering while still
  satisfying the "must be a business user" intent.
- **Rollback:** Relax `IsAssignedBusinessUser` to a profile-type check
  alone — allow any authenticated user whose profile `type` is
  `business` (mirroring `offers_app.IsBusinessUser`) regardless of
  whether they are the assigned business user.

### 2026-07-27 — Detail updates match on offer_type, id is ignored

- **Context:** offers_app offer update (`PATCH /api/offers/{id}/`),
  `OfferDetailUpdateSerializer` and `apply_detail_updates`.
- **Deviation:** The frontend sends each detail in the PATCH body with
  both `id` and `offer_type` (it replaced the `{id, url}` stubs with full
  detail objects). The documentation names `offer_type` as the key that
  identifies a detail for update and never mentions matching by `id`. We
  match strictly on `offer_type` and deliberately ignore any `id` present
  in a detail entry (`id` is not a field on the update serializer).
- **Reason:** `offer_type` is unique per offer (a database constraint)
  and is the documented identifier. Trusting a client-supplied `id` would
  risk pointing an update at a detail belonging to another offer; matching
  by `offer_type` updates the right rows in place and keeps their ids
  stable, as the documentation requires.
- **Rollback:** Add an `id` field to `OfferDetailUpdateSerializer` and
  match on it instead, validating that the id belongs to the target
  offer. The documentation does not require this.

### 2026-07-27 — Offer list `min_price` filter is a lower bound

- **Context:** offers_app offer list (`GET /api/offers/`),
  `OfferFilter.min_price`.
- **Deviation:** The documentation describes the `min_price` query
  parameter only as "filtert Angebote mit einem Mindestpreis" (filters
  offers with a minimum price), which is ambiguous about the comparison
  direction. We read it as a **lower bound**: the filter keeps offers
  whose annotated `min_price` is greater than or equal to the value
  (`lookup_expr="gte"`). This mirrors `max_delivery_time`, which the
  documentation defines as an upper bound (`lte`).
- **Reason:** A "minimum price" filter paired with a "maximum delivery
  time" filter reads naturally as a price floor and a time ceiling, and
  gives the frontend a usable price range together with the two.
- **Rollback:** Change `lookup_expr` on `OfferFilter.min_price` from
  `"gte"` to `"lte"` to treat the value as an upper bound instead.

### 2026-07-27 — Offer list ordering accepts descending variants

- **Context:** offers_app offer list (`GET /api/offers/`),
  `OfferListCreateView.ordering_fields`.
- **Deviation:** The documentation names only the field names
  `updated_at` and `min_price` for the `ordering` parameter, but the
  delivered frontend's sort dropdown emits four values: `updated_at`,
  `-updated_at`, `min_price` and `-min_price`. We accept all four. The
  `-` prefix is DRF's standard descending notation on those same two
  fields, not an additional field.
- **Reason:** Allowing only the two unprefixed values would make two of
  the four frontend sort options silently do nothing, with no error
  anywhere. `ordering_fields = ["updated_at", "min_price"]` enables both
  directions for each field via DRF's `OrderingFilter`.
- **Rollback:** To reject descending variants, replace `OrderingFilter`
  with an explicit `ChoiceField`/validation limited to the two unprefixed
  values; note this breaks two of the frontend's sort options.

### 2026-07-27 — Offer detail URLs are absolute and include /api/

- **Context:** offers_app offer-detail endpoint
  (`GET /api/offers/{id}/`), `OfferDetailLinkSerializer.get_url`.
- **Deviation:** The documentation is internally inconsistent about the
  `details[].url` field. The offer-**list** example (`GET /api/offers/`)
  shows a relative `"/offerdetails/1/"` **without** the `/api` prefix,
  which does not resolve against this backend (all routes live under
  `/api/`). The offer-**detail** example (`GET /api/offers/{id}/`) shows
  a full absolute `"http://127.0.0.1:8000/api/offerdetails/199/"`. We
  follow the detail example: `url` is an absolute URL built from the
  request via `reverse("offerdetail-detail")`, so it always includes the
  `/api/` prefix and the correct host.
- **Reason:** A relative `/offerdetails/1/` would 404, and the frontend
  prefixes only non-http values with the site root, producing
  `http://127.0.0.1:8000/offerdetails/1/` (still missing `/api/`). The
  absolute, `/api`-prefixed form is the only one that resolves, and it
  matches the endpoint's own detail example.
- **Rollback:** To emit the relative form instead, return
  `reverse("offerdetail-detail", args=[obj.id])` without
  `request.build_absolute_uri`; note this breaks navigation unless the
  frontend is changed to add the `/api` prefix.

### 2026-07-27 — Customer profile list omits business-only fields

- **Context:** auth_app customer list endpoint
  (`GET /api/profiles/customer/`), `CustomerProfileSerializer`.
- **Deviation:** The endpoint documentation contradicts itself for this
  endpoint. Its JSON example lists only `user, username, first_name,
  last_name, file, uploaded_at, type` and names the timestamp
  `uploaded_at`, while its prose says `location, tel, description` and
  `working_hours` must not be null in the response. We follow the
  **example**: the customer list returns exactly `user, username,
  first_name, last_name, file, uploaded_at, type`, exposing the model's
  `created_at` under the alias `uploaded_at`. It omits `location`, `tel`,
  `description`, `working_hours`, `email` and `created_at`.
- **Reason:** The worked example is the concrete shape the frontend's
  `transformApiResponse` consumes; the prose appears copied from the
  other profile responses. Between two conflicting readings, the machine-
  checkable example is the more reliable signal, and matching it avoids
  sending fields the frontend does not expect for customers.
- **Rollback:** To adopt the prose reading instead, add `location`,
  `tel`, `description` and `working_hours` to
  `CustomerProfileSerializer.Meta.fields` in the desired order; they
  already exist on the model and are covered by `BLANK_FIELDS`. No model
  or migration change is required.

### 2026-07-27 — Email uniqueness enforced at registration

- **Context:** auth_app registration endpoint (`POST /api/registration/`),
  `RegistrationSerializer.validate_email`.
- **Deviation:** The endpoint documentation lists no uniqueness rule for
  `email`, and Django's `User` model does not enforce one. Registration
  nevertheless rejects a duplicate email with HTTP 400 (invalid data).
- **Reason:** A duplicate email is ambiguous for support and account
  recovery, and the frontend treats every registration failure as 400.
  The documentation is silent here, not explicitly permissive, so a
  documented stricter rule was judged safer than silently accepting
  duplicates. Enforcement is at the serializer only; no database unique
  constraint was added to `auth.User`.
- **Rollback:** Remove `validate_email` from `RegistrationSerializer`.
  No migration or schema change is required, because no database
  constraint was introduced.
