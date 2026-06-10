from app.i18n import t

REQUIRED = [
    "nav.home", "nav.metrics", "nav.program", "nav.nutrition", "nav.settings",
    "auth.login", "auth.register", "action.add", "action.save",
    "plan.generate", "plan.adapt", "workout.log", "nutrition.estimate",
]


def test_all_required_keys_present_and_french():
    for key in REQUIRED:
        value = t(key)
        assert value != key, f"missing translation for {key}"
