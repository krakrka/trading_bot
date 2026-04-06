# core/nlp_agent/macro_analyzer.py

import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)

def analyze_macro_event(event_name: str, actual: str, forecast: str, currency: str = "USD"):
    prompt = PromptTemplate(
        input_variables=["event", "actual", "forecast", "currency"],
        template="""
        Tu es un analyste quantitatif institutionnel senior.
        Analyse l'événement macroéconomique suivant et détermine l'impact fondamental immédiat.

        RÈGLES ET EXEMPLES HISTORIQUES (Few-Shot) :
        - Règle 1 : La crypto est un actif à risque ultra-sensible à la liquidité. Si le DXY (Dollar) monte, la Crypto chute lourdement.
        - Règle 2 : Une hausse de l'inflation (CPI Actual > Forecast) ou des taux de la Fed est HAUSSIÈRE pour le DXY, BAISSIÈRE pour le NASDAQ, et TRES BAISSIÈRE pour la Crypto.
        - Règle 3 : Un ralentissement économique (NFP/Chômage Actual < Forecast) fait baisser le DXY, monter le NASDAQ et monter la Crypto (anticipation de baisse des taux).
        
        Événement à analyser :
        - Événement : {event} ({currency})
        - Chiffre actuel (Actual) : {actual}
        - Prévision (Forecast) : {forecast}
        
        Renvoie UNIQUEMENT un objet JSON valide avec ce format exact :
        {{
            "dxy_bias": float (de -2.0 pour très baissier à 2.0 pour très haussier),
            "nasdaq_bias": float (de -2.0 à 2.0),
            "crypto_bias": float (de -2.0 à 2.0),
            "confidence": float (de 0.0 à 1.0),
            "reasoning": "Explication en 1 phrase de la logique macro"
        }}
        """
    )
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({"event": event_name, "actual": actual, "forecast": forecast, "currency": currency})
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        return json.loads(content.strip())
        
    except Exception as e:
        print(f"❌ Erreur Agent NLP : {e}")
        return None

if __name__ == "__main__":
    print("🧠 Test de l'Agent Macroéconomique avec intégration Crypto...")
    test_result = analyze_macro_event("Core CPI m/m", "0.4%", "0.2%")
    print(json.dumps(test_result, indent=4, ensure_ascii=False))