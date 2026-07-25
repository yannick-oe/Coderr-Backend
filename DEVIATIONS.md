# Deviations

A dated log of deliberate deviations from the binding standards in
`CLAUDE.md` and the reference documents in `docs/`. Every deviation is
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

### 2026-07-25 — Offer detail URLs are absolute and include /api/

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

### 2026-07-25 — Customer profile list omits business-only fields

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

### 2026-07-25 — Email uniqueness enforced at registration

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
