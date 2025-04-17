# Png Placer v1.1 - With Heart Toggle, Font Scaling, Char Count, Regenerate
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os
import zipfile
import io
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

st.set_page_config(page_title="Png Placer", layout="wide")
st.title("Png Placer")

uploaded_files = st.file_uploader("Upload PNGs or a ZIP file", type=['png', 'zip'], accept_multiple_files=True)
line1 = st.text_input("Line 1")
line2 = st.text_input("Line 2")
line3 = st.text_input("Line 3")
line4 = st.text_input("Line 4")
include_heart = st.checkbox("Include Heart Graphic", value=True)

mockup = Image.open("assets/Mockup.png").convert("RGBA")
heart = Image.open("assets/watercolor_heart.png").convert("RGBA")
font_path = "assets/AmaticSC-Regular.ttf"
red_box = (220, 300, 880, 1100)
max_width = red_box[2] - red_box[0]
max_height = red_box[3] - red_box[1]

pngs = []
if uploaded_files:
    for file in uploaded_files:
        if file.name.endswith('.zip'):
            with zipfile.ZipFile(file, 'r') as zip_ref:
                for name in zip_ref.namelist():
                    if name.endswith('.png'):
                        with zip_ref.open(name) as image_file:
                            img = Image.open(image_file).convert("RGBA")
                            pngs.append((name, img))
        elif file.name.endswith('.png'):
            img = Image.open(file).convert("RGBA")
            pngs.append((file.name, img))

def place_graphic_on_mockup(graphic):
    resized = graphic.copy()
    resized.thumbnail((max_width, max_height), Image.ANTIALIAS)
    x = red_box[0] + (max_width - resized.width) // 2 - 20
    y = red_box[1] + (max_height - resized.height) // 2
    canvas_img = mockup.copy()
    canvas_img.paste(resized, (x, y), resized)
    return canvas_img

def generate_smart_title(name):
    base = os.path.splitext(os.path.basename(name))[0].replace("_", " ").replace("-", " ")
    title = " ".join(word.capitalize() for word in base.split())
    return title[:150]

def draw_text_overlay(lines, include_heart):
    canvas = mockup.copy()
    draw = ImageDraw.Draw(canvas)
    font_size = 120
    font = ImageFont.truetype(font_path, font_size)
    total_height = sum(draw.textsize(line, font=font)[1] + 20 for line in lines)
    while total_height > max_height and font_size > 40:
        font_size -= 4
        font = ImageFont.truetype(font_path, font_size)
        total_height = sum(draw.textsize(line, font=font)[1] + 20 for line in lines)
    y = red_box[1] + (max_height - total_height) // 2
    for line in lines:
        w, h = draw.textsize(line, font=font)
        x = red_box[0] + (max_width - w) // 2 - 20
        draw.text((x, y), line, font=font, fill="black")
        y += h + 20
    if include_heart:
        canvas.paste(heart, (x, y + 50), heart)
    return canvas

text_lines = [line for line in [line1, line2, line3, line4] if line.strip() != ""]
if text_lines:
    preview = draw_text_overlay(text_lines, include_heart)
    st.image(preview, caption="Text + Heart Preview", use_column_width=True)

selected_titles = []
if pngs:
    st.subheader("Generated Mockups")
    for name, graphic in pngs:
        title = generate_smart_title(name)
        st.markdown(f"**{title}** ({len(title)} / 200 characters including Amazon suffix)")
        mock_img = place_graphic_on_mockup(graphic)
        col1, col2 = st.columns([4, 1])
        with col1:
            st.image(mock_img, caption=title, use_column_width=True)
        with col2:
            if st.button(f"Regenerate '{title}'", key=f"regen_{title}"):
                mock_img = place_graphic_on_mockup(graphic)
            if st.checkbox(f"Submit '{title}' to uploader", value=True, key=f"chk_{title}"):
                selected_titles.append((title, mock_img, graphic))

    if st.button("Submit Selected to Uploader"):
        for title, mock_img, _ in selected_titles:
            try:
                img_bytes = io.BytesIO()
                mock_img.save(img_bytes, format='PNG')
                img_bytes.seek(0)

                response = requests.post(
                    "https://your-uploader-app.com/upload",  # <-- Replace with your real URL
                    files={"file": (f"{title}.png", img_bytes, "image/png")},
                    data={"title": title},
                    headers={"Authorization": "Bearer YOUR_API_KEY"}  # <-- Replace or remove if not needed
                )

                if response.status_code == 200:
                    st.success(f"✅ Submitted {title}.png to uploader!")
                else:
                    st.error(f"❌ Failed to submit {title}. Status code: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Error uploading {title}: {str(e)}")

        st.balloons()

    with io.BytesIO() as zip_buf:
        with zipfile.ZipFile(zip_buf, "w") as z:
            for title, mock_img, _ in selected_titles:
                img_byte_arr = io.BytesIO()
                mock_img.save(img_byte_arr, format='PNG')
                z.writestr(f"{title}.png", img_byte_arr.getvalue())
        zip_buf.seek(0)
        st.download_button("Download All Mockups (ZIP)", zip_buf, "Mockups.zip")
