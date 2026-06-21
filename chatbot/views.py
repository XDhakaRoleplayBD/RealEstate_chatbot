from django.shortcuts import render
from django.http import JsonResponse
from .models import Property
import requests
import json
import re


# ---------------- HOME ----------------
def home(request):
    return JsonResponse({"msg": "Real Estate AI Running"})


# ---------------- CHAT PAGE ----------------
def chat_page(request):
    return render(request, "chatbot/index.html")


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
You are a Real Estate AI extractor.

Extract structured data from messy user text.

RULES:
- "uttara te" = location
- "dhaka city" = dhaka
- "4 room / 4 bedroom" = bedrooms
- "budget 500000 / under 50 lakh" = price_max
- Always extract what you can

OUTPUT ONLY JSON:

{
  "location": null,
  "bedrooms": null,
  "price_max": null,
  "intent": true
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
        res = requests.post(url, json=payload, timeout=10)
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
        "price_max": None,
        "intent": True
    }


# ---------------- SMART FALLBACK FIX ----------------
def smart_fix(data, message):
    message = message.lower()

    # LOCATION FIX
    if not data.get("location"):
        locations = ["dhaka", "uttara", "gulshan", "banani", "mirpur", "chittagong", "rajshahi"]
        for loc in locations:
            if loc in message:
                data["location"] = loc
                break

    # BEDROOM FIX
    if not data.get("bedrooms"):
        words = message.split()
        for i, w in enumerate(words):
            if w.isdigit():
                if i + 1 < len(words):
                    if "room" in words[i + 1] or "bed" in words[i + 1]:
                        data["bedrooms"] = int(w)
                        break

    # BUDGET FIX
    if not data.get("price_max"):
        nums = re.findall(r"\d+", message)
        for n in nums:
            if len(n) >= 5:  # assume budget
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
    message = request.GET.get("message", "").lower().strip()

    # ---------------- GREETING ----------------
    if any(g in message for g in ["hi", "hello", "hey"]):
        return JsonResponse({
            "reply": "👋 Hello sir!\nTry: Uttara 4 room budget 500000"
        }, json_dumps_params={"ensure_ascii": False})

    # ---------------- AI PARSE ----------------
    data = parse_with_grok(message)

    # ---------------- SMART FIX ----------------
    data = smart_fix(data, message)

    location = data.get("location")
    bedrooms = data.get("bedrooms")
    price_max = data.get("price_max")

    # ---------------- MISSING INFO CHECK ----------------
    missing = []

    if not location:
        missing.append("location")
    if not bedrooms:
        missing.append("rooms")
    if not price_max:
        missing.append("budget")

    # ❗ ONLY ASK IF EVERYTHING IS MISSING
    if len(missing) == 3:
        return JsonResponse({
            "reply": "🤔 Sir, please tell me location, rooms and budget."
        }, json_dumps_params={"ensure_ascii": False})

    # ---------------- SEARCH ----------------
    results = apply_filters(data)

    matched = []

    for p in results[:5]:
        matched.append(
            f"🏡 {p.project_name}\n"
            f"📍 {p.location}\n"
            f"🛏 {p.bedrooms} room\n"
            f"📏 {p.size_sqft} sqft\n"
            f"💰 {p.price}\n"
            f"🚗 Parking: {p.parking}"
        )

    # ---------------- RESPONSE ----------------
    if matched:
        return JsonResponse({
            "reply": "Here are best matches:\n\n" + "\n\n".join(matched)
        }, json_dumps_params={"ensure_ascii": False})

    return JsonResponse({
        "reply": "❌ Sorry sir, no property found for your requirement."
    }, json_dumps_params={"ensure_ascii": False})