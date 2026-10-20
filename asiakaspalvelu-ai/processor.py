import os
from openai import OpenAI
import json

client = OpenAI()

def analyze_ticket(text: str) -> dict:
    prompt = f"""
Analysoi seuraava asiakaspalveluviesti. Palauta vastaus puhtaana JSON-objektina, jossa on seuraavat avaimet:
- "category": Pääkategoria (esim. Laskutus, Tekninen vika, Palautus, Yleinen kysely)
- "urgency": Kiireellisyys (Kiireellinen, Normaali, Matala)
- "summary": Lyhyt tiivistelmä asiakkaan ongelmasta suomeksi
- "draft_reply": Ammattimainen ja kohtelias vastausluonnos asiakkaalle suomeksi

Asiakkaan viesti:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Olet asiantunteva asiakaspalvelupäällikkö. Vastaa aina validina JSON-muotona ilman mitään ylimääräisiä merkkejä tai markdown-tageja."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    content = response.choices[0].message.content.strip()
    
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    return json.loads(content)