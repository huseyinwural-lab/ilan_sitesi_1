import re

class AIChatService:
    def __init__(self):
        # MVP: Keyword based moderation
        self.toxic_patterns = [
            r"stupid", r"idiot", r"scam", r"fuck"
        ]
        self.fraud_patterns = [
            r"western union", r"whatsapp me", r"bank transfer", r"send money"
        ]

    def check_safety(self, text: str) -> dict:
        """
        Returns {'safe': bool, 'reason': str}
        """
        text_lower = text.lower()
        
        for p in self.toxic_patterns:
            if re.search(p, text_lower):
                return {"safe": False, "reason": "Toxicity detected"}
                
        for p in self.fraud_patterns:
            if re.search(p, text_lower):
                return {"safe": False, "reason": "Potential fraud detected"}
                
        return {"safe": True, "reason": None}

    def generate_smart_replies(self, last_message: str) -> list:
        """
        Context-aware suggestions
        """
        text = last_message.lower()
        
        if "available" in text or "duruyor mu" in text:
            return ["Evet, duruyor.", "Rezerve edildi.", "Hayır, satıldı."]
            
        if "price" in text or "fiyat" in text or "ne kadar" in text:
            return ["Fiyat sondur.", "Teklifiniz nedir?", "Açıklamada yazıyor."]
            
        if "where" in text or "nerede" in text:
            return ["İstanbul'da.", "Konum atabilirim.", "Elden teslim."]
            
        # Default
        return ["Teşekkürler.", "Müsait değilim.", "Tamam."]
