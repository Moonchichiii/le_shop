# Today's Implementation Tasks

## Implementation Order

1. Add CustomerProfile + Address models
2. Migrate
3. Add forms (AddressForm + ProfileForm)
4. Add minimal views:
    - `/account/settings/` (name + phone)
    - `/account/addresses/` (list/create)
    - `/account/addresses/<id>/edit`
    - `/account/addresses/<id>/delete`
    - `/account/danger-zone/` (delete account)
5. Tests (start small but real):
    - model: default address behavior
    - view: login required
    - view: user cannot access another user's address
6. Smoke run: signup → login → add address → logout → login again

## Next Steps

If you want, paste your current `accounts/models.py` (even if empty) and I'll adapt it to fit your existing style + your test structure (`factories.py`, `conftest.py`, `test_models.py`, `test_views.py`) without bloating anything.
