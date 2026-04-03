import requests
from bs4 import BeautifulSoup
import json
import asyncio
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 🔑 حط التوكن هنا
TOKEN ="8625366148:AAFmnyHPEjWpe4Din_e565FsSVxdB2hTTnY"

products = {}

# تحميل البيانات
def load():
    global products
    try:
        with open("data.json", "r") as f:
            products = json.load(f)
    except:
        products = {}

# حفظ البيانات
def save():
    with open("data.json", "w") as f:
        json.dump(products, f)

# جلب السعرdef get_price(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9"
    }

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    # الطريقة 1
    price = soup.select_one(".a-price .a-offscreen")
    if price:
        txt = price.text.replace("جنيه", "").replace(",", "").strip()
        try:
            return int(float(txt))
        except:
            pass

    # الطريقة 2
    price = soup.select_one("#priceblock_ourprice")
    if price:
        txt = price.text.replace("جنيه", "").replace(",", "").strip()
        try:
            return int(float(txt))
        except:
            pass

    # الطريقة 3
    price = soup.select_one("#priceblock_dealprice")
    if price:
        txt = price.text.replace("جنيه", "").replace(",", "").strip()
        try:
            return int(float(txt))
        except:
            pass

    return None

# بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.application.bot_data.setdefault("users", set()).add(update.effective_chat.id)
    await update.message.reply_text("👋 أهلاً بيك\nاستخدم /add لإضافة منتج")

# إضافة منتج
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = context.args[0]
        target = int(context.args[1])

        price = get_price(url)

        products[url] = {
            "target": target,
            "last": price
        }

        save()

        await update.message.reply_text(f"✅ تمت الإضافة\nالسعر الحالي: {price}")

    except:
        await update.message.reply_text("❌ استخدم:\n/add link price")

# عرض المنتجات
async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not products:
        await update.message.reply_text("❌ لا يوجد منتجات")
        return

    msg = ""
    for url, data in products.items():
        msg += f"\n🔗 {url}\n🎯 الهدف: {data['target']}\n💰 آخر سعر: {data['last']}\n"

    await update.message.reply_text(msg)

# حذف منتج
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = context.args[0]
        products.pop(url)
        save()
        await update.message.reply_text("🗑️ تم الحذف")
    except:
        await update.message.reply_text("❌ اكتب اللينك")

# متابعة الأسعار
async def check_prices(app):
    while True:
        for url, data in products.items():
            price = get_price(url)

            if price and data["last"]:
                # انخفاض
                if price < data["last"]:
                    await app.bot.send_message(
                        chat_id=list(app.bot_data["users"])[0],
                        text=f"🔻 السعر نزل!\n{url}\n💰 {data['last']} → {price}"
                    )

                # زيادة
                elif price > data["last"]:
                    await app.bot.send_message(
                        chat_id=list(app.bot_data["users"])[0],
                        text=f"🔺 السعر زاد!\n{url}\n💰 {data['last']} → {price}"
                    )

                products[url]["last"] = price
                save()

        await asyncio.sleep(1800)  # كل 30 دقيقة

# تشغيل المتابعة في Thread
def run_checker(app):
    asyncio.run(check_prices(app))

# تشغيل البوت
def main():
    load()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_products))
    app.add_handler(CommandHandler("remove", remove))

    # تشغيل المتابعة بدون crash
    threading.Thread(target=run_checker, args=(app,), daemon=True).start()

    app.run_polling()

if __name__ == "__main__":
    main()