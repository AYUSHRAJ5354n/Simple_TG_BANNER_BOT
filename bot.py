import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Bot configuration
api_id = "708575"
api_hash = "431d3ae02dd51dd7c26ab9f9a08dae84"
bot_token = "7937563107:AAFVvLlvKuSwDy6Go8zKOQu1vXRQA2FxAOo"
forwarding_channel = "-1002206233283"

TIMEOUT = 600  # 1 Minute

# Initialize Pyrogram client
app = Client("banner_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Store user state
user_states = {}

# Function to create banner
def create_banner(data):
    try:
        user_id = data["user_id"]
        main_image_path = data["main_image"]
        background_image_path = data["background_image"]
        title = data["title"]
        studio = data["studio"]
        season = data["season"]
        episodes = data["episodes"]
        rating = data["rating"]
        genres = data["genres"]

        # Load images
        main_image = Image.open(main_image_path).convert("RGBA")
        background_image = Image.open(background_image_path).convert("RGBA")

        # Resize background and apply blur
        background_image = background_image.resize((1280, 720))
        background_image = background_image.filter(ImageFilter.GaussianBlur(8))

        # Create a blank image for the banner
        banner = Image.new("RGBA", (1280, 720), (50, 50, 50, 255))  # solid dark gray background
        banner.paste(background_image, (0, 0), background_image)

        # Resize and create square-round shape for main image
        main_image = main_image.resize((500, 500))
        mask = Image.new("L", main_image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, 500, 500), radius=70, fill=255)
        main_image = Image.composite(main_image, Image.new("RGBA", main_image.size), mask)

        # Paste the main image onto the banner
        banner.paste(main_image, (40, 110), main_image)

        # Add text to the banner
        draw = ImageDraw.Draw(banner)
        title_font = ImageFont.truetype("FenomenSans-SCNSemiBold.ttf", 60)  # large bold font for title
        studio_font = ImageFont.truetype("FenomenSans-SCNSemiBold.ttf", 40)  # smaller font for studio
        details_font = ImageFont.truetype("FenomenSans-SCNSemiBold.ttf", 35)  # smaller font for details
        rating_font = ImageFont.truetype("FenomenSans-SCNSemiBold.ttf", 50)  # large font for rating

        # Define text colors
        text_color = (255, 255, 255)
        studio_color = (255, 0, 0)
        rating_color = (255, 255, 255)
        star_color = (255, 215, 0)

        # Title
        draw.text((640, 50), title, fill=text_color, font=title_font, anchor="mm")

        # Studio
        draw.text((640, 150), studio, fill=studio_color, font=studio_font, anchor="mm")

        # Details (align left)
        details_text = f"Season: {season}\nEpisodes: {episodes}"
        draw.text((40, 650), details_text, fill=text_color, font=details_font, anchor="lm")

        # Rating
        draw.text((1080, 50), "★", fill=star_color, font=rating_font, anchor="mm")
        draw.text((1120, 50), f"{rating}%", fill=rating_color, font=rating_font, anchor="lm")

        # Genres (as buttons)
        genre1, genre2 = genres.split(", ")
        button_font = ImageFont.truetype("FenomenSans-SCNSemiBold.ttf", 35)
        button_color = (50, 50, 50)
        button_text_color = (255, 255, 255)
        draw.rounded_rectangle((900, 150, 1050, 200), radius=10, fill=button_color)
        draw.rounded_rectangle((1100, 150, 1250, 200), radius=10, fill=button_color)
        draw.text((975, 175), genre1, fill=button_text_color, font=button_font, anchor="mm")
        draw.text((1175, 175), genre2, fill=button_text_color, font=button_font, anchor="mm")

        # Save the final image
        output_path = f"banner_{user_id}.png"
        banner.save(output_path)
        return output_path
    except Exception as e:
        return f"Error: {e}"

# Timeout handler
async def timeout_handler(user_id):
    await asyncio.sleep(TIMEOUT)
    if user_id in user_states:
        user_data = user_states[user_id]
        # Delete all files uploaded by the user
        for key in ["main_image", "background_image"]:
            if key in user_data and os.path.exists(user_data[key]):
                os.remove(user_data[key])
        del user_states[user_id]
        try:
            await app.send_message(
                user_id,
                f"<blockquote>⏳ Timeout! You took too long to respond. Please start over using the /banner command. 😊</blockquote>"
            )
        except Exception as e:
            print(f"Failed to send timeout message: {e}")
        return True
    return False

# /start command handler
@app.on_message(filters.command("start") & filters.private)
async def welcome_user(client, message):
    welcome_text = (
        f"<blockquote><b>Welcome to the Banner Bot!\n\n"
        f"I'm just a bot created by [RAHAT](https://t.me/r4h4t_69).\n\n"
        f"You can use me to create custom banners.\n\n"
        f"To get started, use the /banner command.</b></blockquote>"
    )
    await message.reply_text(welcome_text, disable_web_page_preview=True)

# /banner command handler
@app.on_message(filters.command("banner") & filters.private)
async def start_banner_process(client, message):
    user_id = message.from_user.id
    user_states[user_id] = {"step": "main_image", "user_id": user_id}
    await message.reply_text(f"<blockquote>Please send the **main image** for the banner.</blockquote>")
    asyncio.create_task(timeout_handler(user_id))

# Handle subsequent inputs
@app.on_message(filters.private)
async def handle_inputs(client, message):
    user_id = message.from_user.id

    # Check if the user is in an active state
    if user_id not in user_states:
        return

    state = user_states[user_id]

    # Reset timeout if new input is received
    asyncio.create_task(timeout_handler(user_id))

    # Main image step
    if state["step"] == "main_image":
        if not message.photo:
            await message.reply_text(f"<blockquote>Please send a valid image.</blockquote>")
            return

        main_image = await message.download()
        state["main_image"] = main_image
        state["step"] = "background_image"
        await message.reply_text(f"<blockquote>Please send the **background image** for the banner.</blockquote>")

    # Background image step
    elif state["step"] == "background_image":
        if not message.photo:
            await message.reply_text(f"<blockquote>Please send a valid image.</blockquote>")
            return

        background_image = await message.download()
        state["background_image"] = background_image
        state["step"] = "title"
        await message.reply_text(f"<blockquote>What is the **title** of the banner?</blockquote>")

    # Title step
    elif state["step"] == "title":
        state["title"] = message.text
        state["step"] = "media_type"
        await message.reply_text(f"<blockquote>What is the **media type** (e.g., Donghua, Anime, etc.)?</blockquote>")

    # Media type step
    elif state["step"] == "media_type":
        state["media_type"] = message.text
        state["step"] = "season"
        await message.reply_text(f"<blockquote>What is the **season**?</blockquote>")

    # Season step
    elif state["step"] == "season":
        state["season"] = message.text
        state["step"] = "episode"
        await message.reply_text(f"<blockquote>What is the **Total episode number**?</blockquote>")

    # Episode step
    elif state["step"] == "episode":
        state["episode"] = message.text
        state["step"] = "score"
        await message.reply_text(f"<blockquote>What is the **score** (e.g., 8.89)?</blockquote>")

    # Score step
    elif state["step"] == "score":
        state["score"] = message.text
        state["step"] = "rating"
        await message.reply_text(f"<blockquote>What is the **rating** (e.g., 89%)?</blockquote>")

    # Rating step
    elif state["step"] == "rating":
        state["rating"] = message.text

        # Generate banner
        banner_path = create_banner(state)

        if isinstance(banner_path, str) and banner_path.endswith(".png"):
            await message.reply_photo(banner_path, caption="Here is your banner!")
            username = message.from_user.username or "Unknown User"
            caption = f"<blockquote><b>Banner created by @{username}</b></blockquote>"
            await client.send_photo(forwarding_channel, banner_path, caption=caption)

            # Delete all generated files
            for file in [state["main_image"], state["background_image"], banner_path]:
                if os.path.exists(file):
                    os.remove(file)
        else:
            await message.reply_text(f"Failed to create banner: {banner_path}")

        # Clear user state
        del user_states[user_id]

# Run the bot
if __name__ == "__main__":
    app.run()
            
