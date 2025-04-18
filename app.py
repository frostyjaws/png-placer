# Png Placer - Fully Patched Version with Progress Bar and Placement Fixes
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageChops
import os
import zipfile
import io
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

st.set_page_config(page_title="Png Placer", layout="wide")
st.title("Png Placer")

pngs = []
uploaded_files = st.file_uploader("Upload PNGs or a ZIP file", type=['png', 'zip'], accept_multiple_files=True)
line1 = st.text_input("Line 1")
line2 = st.text_input("Line 2")
line3 = st.text_input("Line 3")
line4 = st.text_input("Line 4")
include_heart = st.checkbox("Include Heart Graphic", value=True)

mockup = Image.open("assets/mockup.png").convert("RGBA")
heart = Image.open("assets/watercolor_heart.png").convert("RGBA")
font_path = "assets/AmaticSC-Regular.ttf"
red_box = (220, 300, 880, 1100)
max_width = red_box[2] - red_box[0]
max_height = red_box[3] - red_box[1]

pdf_output_dir = r"C:\\Users\\sfbuc\\OneDrive\\Graphic Tee SVGS\\Png Placer"
os.makedirs(pdf_output_dir, exist_ok=True)

def trim_transparency(img):
    bg = Image.new(img.mode, img.size, (0, 0, 0, 0))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    return img.crop(bbox) if bbox else img

def place_graphic_on_mockup(graphic):
    trimmed = trim_transparency(graphic)
    trimmed.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    x = red_box[0] + (max_width - trimmed.width) // 2
    y = red_box[1]
    canvas_img = mockup.copy()
    canvas_img.paste(trimmed, (x, y), trimmed)
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

def generate_print_pdf(title, trimmed_graphic):
    file_path = os.path.join(pdf_output_dir, f"{title}.pdf")
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    temp_path = f"/tmp/{title}.png"
    trimmed_graphic.save(temp_path)
    c.drawImage(temp_path, 100, 300, width=400, preserveAspectRatio=True, mask='auto')
    c.showPage()
    c.save()
    return file_path

text_lines = [line for line in [line1, line2, line3, line4] if line.strip() != ""]
if text_lines:
    preview = draw_text_overlay(text_lines, include_heart)
    st.image(preview, caption="Text + Heart Preview", use_container_width=True)

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

selected_titles = []
mockup_zip = io.BytesIO()

if pngs:
    st.subheader("Generated Mockups")
    progress = st.progress(0)
    total = len(pngs)
    count = 0

    with zipfile.ZipFile(mockup_zip, "w") as zip_mock:
        for name, graphic in pngs:
            title = generate_smart_title(name)
            st.markdown(f"**{title}** ({len(title)} / 200 characters including Amazon suffix)")
            trimmed_graphic = trim_transparency(graphic)
            mock_img = place_graphic_on_mockup(trimmed_graphic)

            col1, col2 = st.columns([4, 1])
            with col1:
                st.image(mock_img, caption=title, use_container_width=True)
            with col2:
                if st.button(f"Regenerate '{title}'", key=f"regen_{title}"):
                    mock_img = place_graphic_on_mockup(trimmed_graphic)
                if st.checkbox(f"Submit '{title}' to uploader", value=True, key=f"chk_{title}"):
                    selected_titles.append((title, mock_img, trimmed_graphic))

            img_bytes = io.BytesIO()
            mock_img.save(img_bytes, format='PNG')
            st.download_button(f"Download {title}.png", img_bytes.getvalue(), file_name=f"{title}.png", mime="image/png", key=f"dl_{title}")
            zip_mock.writestr(f"{title}.png", img_bytes.getvalue())

            generate_print_pdf(title, trimmed_graphic)

            count += 1
            progress.progress(count / total)

    mockup_zip.seek(0)
    st.download_button("Download All Mockups (ZIP)", mockup_zip, "Mockups.zip")
