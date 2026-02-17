
import logging

class TranslationService:
    async def translate_text(self, text: str, target_lang: str) -> str:
        """
        Mock Translation Service.
        In prod, integrate Google Translate or DeepL.
        """
        # Simple Mock
        if target_lang == "it":
            if "Car" in text or "Araba" in text: return "Auto"
            if "Home" in text or "Ev" in text: return "Casa"
        return text
