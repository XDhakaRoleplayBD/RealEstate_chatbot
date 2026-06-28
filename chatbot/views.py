from django.shortcuts import render
from django.http import JsonResponse
from .models import Property

from deep_translator import GoogleTranslator
import requests
import json
import re


# ---------------- HOME ----------------
def home(request):
    return JsonResponse({"msg": "Real Estate AI Running"})


# ---------------- CHAT PAGE ----------------
def chat_page(request):
    return render(request, "chatbot/index.html")


# ---------------- BANGLA CHECK ----------------
def is_bangla(text):
    for ch in text:
        if '\u0980' <= ch <= '\u09FF':
            return True
    return False


# ---------------- TRANSLATE ----------------
def translate_text(text):
    try:
        return GoogleTranslator(
            source="auto",
            target="en"
        ).translate(text).lower()
    except:
        return text.lower()


# ---------------- GROK AI PARSER ----------------
def parse_with_grok(message):

    url = "https://api.x.ai/v1/chat/completions"

    headers = {
        "Authorization": "Bearer YOUR_GROK_API_KEY",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "grok-2",
        "messages": [
            {
                "role": "system",
                "content": """
Extract location, bedrooms, price_max from messy text.

Return ONLY JSON:
{
  "location": null,
  "bedrooms": null,
  "price_max": null
}
"""
            },
            {
                "role": "user",
                "content": message
            }
        ]
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        data = res.json()

        content = data["choices"][0]["message"]["content"]

        match = re.search(r"\{.*\}", content, re.DOTALL)

        if match:
            return json.loads(match.group())

    except:
        pass

    return {
        "location": None,
        "bedrooms": None,
        "price_max": None
    }


# ---------------- SMART FIX (IMPROVED ONLY) ----------------
def smart_fix(data, message):

    message = message.lower()

    # LOCATION FIX (DB)
    if not data.get("location"):
        locations = Property.objects.values_list("location", flat=True).distinct()

        for loc in locations:
            if loc and str(loc).lower() in message:
                data["location"] = loc
                break

    # ROOM FIX (messy text)
    if not data.get("bedrooms"):
        match = re.search(r"(\d+)\s*(room|rooms|bed|bedroom|bedrooms)", message)
        if match:
            data["bedrooms"] = int(match.group(1))

    # BUDGET FIX
    if not data.get("price_max"):
        nums = re.findall(r"\d+", message)

        for n in nums:
            if len(n) >= 5:
                data["price_max"] = int(n)
                break

    return data


# ---------------- APPLY FILTERS ----------------
def apply_filters(filters):

    qs = Property.objects.all()

    if filters.get("location"):
        qs = qs.filter(location__icontains=filters["location"])

    if filters.get("bedrooms"):
        qs = qs.filter(bedrooms=filters["bedrooms"])

    if filters.get("price_max"):
        qs = qs.filter(price__lte=filters["price_max"])

    return qs


# ---------------- CHAT RESPONSE ----------------
def chat_response(request):

    message = request.GET.get("message", "").strip()
    lower = message.lower()

    # ---------------- GREETING (BANGLA + ENGLISH) ----------------
    if any(x in lower for x in ["hi", "hello", "hey"]):
        return JsonResponse({
            "reply": "👋 আসসালামু আলাইকুম sir।\nআপনি location, room, budget বলুন।"
        }, json_dumps_params={"ensure_ascii": False})

    # ---------------- TRANSLATE ONLY IF BANGLA ----------------
    if is_bangla(message):
        message = translate_text(message)

    # ---------------- AI PARSE ----------------
    data = parse_with_grok(message)

    # ---------------- SMART FIX ----------------
    data = smart_fix(data, message)

    # ---------------- VALIDATION (NEW ADD ONLY) ----------------
    if not any([data.get("location"), data.get("bedrooms"), data.get("price_max")]):
        return JsonResponse({
            "reply": "❌ sir, দয়া করে valid location / room / budget দিন।"
        }, json_dumps_params={"ensure_ascii": False})

    # ---------------- SEARCH ----------------
    results = apply_filters(data)

    if not results.exists():
        return JsonResponse({
            "reply": "❌ দুঃখিত sir, কোনো property পাওয়া যায়নি।"
        }, json_dumps_params={"ensure_ascii": False})

    # ---------------- OUTPUT (BANGLA MAINTAINED) ----------------
    output = []

    for p in results[:10]:
        output.append(f"""
🏡 প্রজেক্ট: {p.project_name}
📍 এলাকা: {p.location}
🛏 রুম: {p.bedrooms}
📏 আয়তন: {p.size_sqft} sqft
💰 দাম: {p.price}
🚗 পার্কিং: {p.parking}
""")

    return JsonResponse({
        "reply": "আপনার চাহিদা অনুযায়ী পাওয়া গেছে:\n\n" + "\n".join(output)
    }, json_dumps_params={"ensure_ascii": False})