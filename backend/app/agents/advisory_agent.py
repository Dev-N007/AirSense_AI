import os
import json
from pydantic import BaseModel
from google import genai
from google.genai import types
from backend.app.config import settings

class AdvisorySchema(BaseModel):
    recommendations: str
    citizen_advisory_en: str
    citizen_advisory_hi: str

class AdvisoryAgent:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                print("Advisory Agent: Gemini GenAI client initialized.")
            except Exception as e:
                print(f"Error initializing Gemini client: {e}")

    def generate_advisory(self, station_name: str, forecast_data: dict, shap_explanations: list) -> dict:
        # Extract features and SHAP values for the prompt
        shap_summary = ", ".join([f"{item['feature']} (Impact: {item['shap_value']})" for item in shap_explanations[:5]])
        
        predicted_24 = forecast_data["predicted_aqi_24h"]
        predicted_48 = forecast_data["predicted_aqi_48h"]
        predicted_72 = forecast_data["predicted_aqi_72h"]
        
        # Compile a rich contextual prompt for Gemini
        prompt = f"""
        You are the Lead Urban Air Quality Policy Advisor and Health Expert for Delhi.
        Analyze the following real-time air quality forecast data for the station '{station_name}':
        
        FORECAST:
        - 24-Hour Ahead AQI: {predicted_24}
        - 48-Hour Ahead AQI: {predicted_48}
        - 72-Hour Ahead AQI: {predicted_72}
        
        SHAP ATTRIBUTIONS (Top pollution drivers):
        {shap_summary}
        
        Please generate:
        1. **Administrative Recommendations**: Specific, concrete, evidence-backed interventions for city administrators. These must be targeted to the predicted severity and the drivers (e.g. if wind speed is low, suggest dust control and road sweeping; if industrial proximity is a factor, restrict emissions; if AQI > 300, restrict heavy vehicle entry, deploy anti-smog guns near sensitive receptors).
        2. **Citizen Advisory (English)**: Public health advisories including mask recommendations (N95), indoor activity suggestions, air purifier advice, and specific warnings for vulnerable populations (children, elderly, asthmatics).
        3. **Citizen Advisory (Hindi)**: An accurate, natural, and clear Hindi translation of the English citizen advisory.
        
        Format your response precisely using the requested JSON schema.
        """
        
        # If client is initialized, request Gemini
        if self.client:
            try:
                print(f"Sending prompt to Gemini 2.5 Flash for station: {station_name}...")
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=AdvisorySchema,
                        temperature=0.2,
                    ),
                )
                
                # Parse JSON output
                res_dict = json.loads(response.text)
                return {
                    "recommendations": res_dict.get("recommendations", ""),
                    "citizen_advisory_en": res_dict.get("citizen_advisory_en", ""),
                    "citizen_advisory_hi": res_dict.get("citizen_advisory_hi", ""),
                }
            except Exception as e:
                print(f"Gemini generation encountered an error: {e}. Falling back to rule-based system.")
                
        # Rule-based fallback generator
        return self._generate_fallback_advisory(station_name, predicted_24, shap_explanations)

    def _generate_fallback_advisory(self, station_name: str, predicted_24: int, shap_explanations: list) -> dict:
        print("Using local rule-based advisory engine...")
        # Determine AQI category
        if predicted_24 <= 50:
            status = "Good"
            color = "Green"
            rec = "Maintain routine city operations. No restrictions are required."
            adv_en = "Air quality is satisfactory, and air pollution poses little or no risk. Outdoor activities are highly encouraged."
            adv_hi = "वायु गुणवत्ता संतोषजनक है, और वायु प्रदूषण से बहुत कम या कोई खतरा नहीं है। बाहरी गतिविधियां पूरी तरह से सुरक्षित हैं।"
        elif predicted_24 <= 100:
            status = "Satisfactory"
            color = "Light Green"
            rec = "Increase street sweeping and maintain water spraying on high-traffic roads to control dust particles."
            adv_en = "Air quality is acceptable. However, highly sensitive individuals should reduce prolonged outdoor exertion."
            adv_hi = "वायु गुणवत्ता स्वीकार्य है। हालांकि, अत्यधिक संवेदनशील लोगों को लंबे समय तक बाहर शारीरिक श्रम करने से बचना चाहिए।"
        elif predicted_24 <= 200:
            status = "Moderate"
            color = "Yellow"
            rec = "Enforce stricter emission control at construction sites. Deploy mechanical sweepers on primary roads."
            adv_en = "Air quality is moderate. Sensitive groups (children, elderly, asthmatics) may experience respiratory discomfort and should limit heavy outdoor activities."
            adv_hi = "वायु गुणवत्ता मध्यम है। संवेदनशील समूहों (बच्चों, बुजुर्गों, दमा रोगियों) को सांस लेने में तकलीफ हो सकती है और उन्हें बाहर जाने से बचना चाहिए।"
        elif predicted_24 <= 300:
            status = "Poor"
            color = "Orange"
            rec = "Implement Stage 1 of the Graded Response Action Plan (GRAP). Restrict diesel generator usage. Deploy water sprinklers at commercial hubs."
            adv_en = "Air quality is poor. Wear N95 masks if outdoors for extended periods. Sensitive groups should remain indoors. Limit intense outdoor exercise."
            adv_hi = "वायु गुणवत्ता खराब है। लंबे समय तक बाहर रहने पर N95 मास्क पहनें। संवेदनशील वर्ग घर के अंदर ही रहें। बाहरी व्यायाम कम करें।"
        elif predicted_24 <= 400:
            status = "Very Poor"
            color = "Red"
            rec = "Enforce Stage 2/3 of GRAP. Ban coal and firewood usage in eateries. Halt non-essential construction work near schools and hospitals. Deploy anti-smog guns at hotspots."
            adv_en = "Air quality is Very Poor. Health warnings of emergency conditions. Everyone should avoid outdoor physical activities. Vulnerable groups must stay indoors and use air purifiers if possible."
            adv_hi = "वायु गुणवत्ता बहुत खराब है। स्वास्थ्य आपातकाल की स्थिति। सभी लोग बाहर शारीरिक गतिविधियों से बचें। कमजोर वर्ग घर के अंदर रहें और हो सके तो एयर प्यूरीफायर चलाएं।"
        else:
            status = "Severe"
            color = "Dark Red"
            rec = "Enforce Stage 4 of GRAP (Emergency). Ban entry of heavy diesel trucks into Delhi (except essential commodities). Stop all construction. Transition schools to online learning and mandate work-from-home for offices."
            adv_en = "AQI is in the SEVERE/HAZARDOUS range. Serious risk of respiratory effects on the general public. Mandatorily wear N95 masks. Keep windows shut, run air purifiers on high, and strictly avoid going outdoors."
            adv_hi = "वायु गुणवत्ता अति गंभीर (आपातकालीन) श्रेणी में है। सामान्य जनता पर गंभीर स्वास्थ्य जोखिम। अनिवार्य रूप से N95 मास्क पहनें। खिड़कियां बंद रखें, एयर प्यूरीफायर चलाएं और बाहर जाने से पूरी तरह बचें।"

        # Add custom driver-based context to the administrative recommendations
        drivers_text = []
        for item in shap_explanations[:2]:
            feat = item["feature"]
            shap_val = item["shap_value"]
            if shap_val > 5:
                if "Wind Speed" in feat:
                    drivers_text.append("low wind speed causing heavy pollutant stagnation")
                elif "PM2.5" in feat:
                    drivers_text.append("elevated local PM2.5 levels from ground sources")
                elif "Road" in feat:
                    drivers_text.append("vehicle exhaust accumulation along congested traffic corridors")
                elif "Industrial" in feat:
                    drivers_text.append("nearby industrial boiler emissions")
        
        if drivers_text:
            rec = f"Identify high-risk hotspots driven by {', and '.join(drivers_text)}. {rec}"
            
        return {
            "recommendations": rec,
            "citizen_advisory_en": adv_en,
            "citizen_advisory_hi": adv_hi
        }
