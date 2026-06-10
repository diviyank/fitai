from app.i18n import t


def test_translation_lookup_and_fallback():
    assert t("nav.home") == "Accueil"
    assert t("does.not.exist") == "does.not.exist"
