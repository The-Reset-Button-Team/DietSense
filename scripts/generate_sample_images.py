"""
DietSense — Sample Image Generator
Creates realistic sample grocery bill and fridge snapshot images
for testing receipt scanning, vision parsing, and pantry management offline.
"""

import os
import shutil
from PIL import Image, ImageDraw, ImageFont


def get_font(name: str, size: int):
    """Safely loads a font, falling back to default if unavailable."""
    try:
        return ImageFont.truetype(name, size)
    except Exception:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()


def generate_blinkit_bill():
    """Generates a realistic receipt invoice image for quick-commerce delivery."""
    width = 600
    height = 920
    im = Image.new("RGB", (width, height), color="#ffffff")
    draw = ImageDraw.Draw(im)

    # Fonts
    title_font = get_font("calibri.ttf", 32)
    header_font = get_font("calibri.ttf", 22)
    bold_font = get_font("calibri.ttf", 18)
    normal_font = get_font("calibri.ttf", 16)
    small_font = get_font("calibri.ttf", 13)
    mono_font = get_font("consola.ttf", 14)

    # Top Accent Banner
    draw.rectangle([(0, 0), (width, 8)], fill="#e23744")

    # Brand Header
    draw.text((40, 30), "blinkit", fill="#000000", font=title_font)
    draw.rectangle([(145, 34), (240, 62)], fill="#fced4e", outline=None)
    draw.text((155, 38), "10 MINS", fill="#000000", font=bold_font)

    draw.text((40, 75), "Blink Commerce Private Limited", fill="#555555", font=small_font)
    draw.text((40, 93), "Tax Invoice / Cash Receipt · FSSAI: 10819005000236", fill="#777777", font=small_font)

    # Divider
    draw.line([(40, 115), (width - 40, 115)], fill="#dddddd", width=2)

    # Order Metadata
    draw.text((40, 125), "Order #: BK-94821038", fill="#222222", font=bold_font)
    draw.text((width - 220, 125), "Date: 25 Oct 2026, 10:42 AM", fill="#666666", font=small_font)
    draw.text((40, 147), "Delivered To: Sector 62, Noida · Customer: Prasoon", fill="#555555", font=small_font)

    # Table Header
    y = 180
    draw.rectangle([(40, y), (width - 40, y + 32)], fill="#f4f4f4")
    draw.text((50, y + 7), "Item Description", fill="#333333", font=bold_font)
    draw.text((360, y + 7), "Qty", fill="#333333", font=bold_font)
    draw.text((430, y + 7), "Price", fill="#333333", font=bold_font)
    draw.text((500, y + 7), "Total", fill="#333333", font=bold_font)

    # Line Items
    items = [
        ("Mother Dairy Classic Paneer", "200g", "₹95", "₹95"),
        ("Fresh Hydroponic Palak", "250g", "₹45", "₹45"),
        ("Nestle A+ Slim Dahi Tub", "400g", "₹75", "₹75"),
        ("English Oven Whole Wheat Bread", "400g", "₹55", "₹55"),
        ("Amul Taaza Homogenised Milk", "1 L", "₹56", "₹56"),
        ("Farm Fresh Hybrid Tomatoes", "500g", "₹32", "₹32"),
        ("Tata Sampann Moong Dal Split", "500g", "₹78", "₹78"),
        ("Quaker Rolled Oats Pouch", "500g", "₹85", "₹85"),
    ]

    y = 225
    for idx, (name, qty, price, total) in enumerate(items):
        bg = "#fafafa" if idx % 2 == 1 else "#ffffff"
        draw.rectangle([(40, y - 4), (width - 40, y + 34)], fill=bg)

        draw.text((50, y), name, fill="#222222", font=normal_font)
        draw.text((50, y + 18), f"Pack Size: {qty}", fill="#888888", font=small_font)

        draw.text((365, y + 5), "1", fill="#444444", font=normal_font)
        draw.text((430, y + 5), price, fill="#444444", font=normal_font)
        draw.text((500, y + 5), total, fill="#111111", font=bold_font)

        y += 44

    # Subtotals
    y += 10
    draw.line([(40, y), (width - 40, y)], fill="#dddddd", width=1)
    y += 12

    summary_lines = [
        ("Items Subtotal (8 items)", "₹521.00"),
        ("Handling Fee", "₹4.00"),
        ("Delivery Partner Tip", "₹0.00"),
        ("Discounts & Coupons", "-₹25.00"),
    ]

    for label, val in summary_lines:
        draw.text((300, y), label, fill="#666666", font=small_font)
        draw.text((500, y), val, fill="#444444", font=small_font)
        y += 22

    # Grand Total
    y += 6
    draw.rectangle([(40, y), (width - 40, y + 42)], fill="#e8f5e9")
    draw.text((50, y + 10), "Grand Total (Paid via UPI)", fill="#1b5e20", font=header_font)
    draw.text((490, y + 10), "₹500.00", fill="#1b5e20", font=header_font)

    # Barcode representation
    y += 60
    draw.line([(40, y), (width - 40, y)], fill="#e0e0e0", width=1)
    y += 15
    barcode_x = 180
    for w, gap in [(2, 3), (4, 2), (1, 3), (3, 4), (2, 2), (5, 3), (2, 4), (1, 2), (4, 3), (2, 4), (3, 2), (1, 3), (4, 4), (2, 2), (3, 3), (1, 2), (4, 3), (2, 2), (5, 4)]:
        draw.rectangle([(barcode_x, y), (barcode_x + w, y + 36)], fill="#333333")
        barcode_x += w + gap

    draw.text((215, y + 42), "*BK94821038*", fill="#777777", font=mono_font)
    draw.text((150, y + 68), "Thank you for shopping on Blinkit! Eat Healthy.", fill="#999999", font=small_font)

    return im


def generate_fridge_snapshot():
    """Generates an organized, crisp realistic refrigerator interior shelf image."""
    width = 800
    height = 600
    im = Image.new("RGB", (width, height), color="#eaf2f8")
    draw = ImageDraw.Draw(im)

    # Fonts
    title_font = get_font("calibri.ttf", 24)
    item_font = get_font("calibri.ttf", 16)
    sub_font = get_font("calibri.ttf", 12)

    # Fridge Interior Background Gradient/Lighting
    for row in range(height):
        # Soft blue-white top-lit refrigerator gradient
        tint = int(245 - (row / height) * 35)
        blue = int(255 - (row / height) * 20)
        draw.line([(0, row), (width, row)], fill=(tint - 5, tint, blue))

    # Fridge Door Borders
    draw.rectangle([(0, 0), (24, height)], fill="#d5dbdb")
    draw.rectangle([(width - 24, 0), (width, height)], fill="#d5dbdb")

    # Refrigerator LED light bar at top
    draw.rectangle([(100, 10), (width - 100, 26)], fill="#ffffff", outline="#b0c4de")

    # Shelves
    shelf_positions = [260, 480]

    for sy in shelf_positions:
        # Glass shelf
        draw.rectangle([(24, sy - 8), (width - 24, sy)], fill="#aed6f1", outline="#85c1e9")
        # Stainless steel front edge trim
        draw.rectangle([(24, sy), (width - 24, sy + 12)], fill="#bdc3c7", outline="#7f8c8d")

    # --- TOP SHELF ITEMS (sy = 260) ---

    # 1. Milk Carton (x=70 to 170, y=70 to 252)
    draw.rectangle([(70, 70), (170, 252)], fill="#ffffff", outline="#2980b9", width=2)
    # Carton slant roof
    draw.polygon([(70, 70), (120, 35), (170, 70)], fill="#3498db", outline="#2980b9")
    draw.rectangle([(75, 100), (165, 150)], fill="#3498db")
    draw.text((82, 110), "AMUL", fill="#ffffff", font=title_font)
    draw.text((82, 132), "TAAZA MILK", fill="#ffffff", font=sub_font)
    draw.text((85, 180), "500 ml", fill="#333333", font=item_font)
    draw.text((78, 210), "✓ Pasteurized", fill="#27ae60", font=sub_font)

    # 2. Curd / Dahi Tub (x=210 to 330, y=140 to 252)
    draw.ellipse([(210, 130), (330, 165)], fill="#ffffff", outline="#16a085", width=2)
    draw.polygon([(210, 147), (225, 252), (315, 252), (330, 147)], fill="#ffffff", outline="#16a085")
    draw.rectangle([(228, 175), (312, 215)], fill="#e8f8f5")
    draw.text((236, 182), "FRESH DAHI", fill="#16a085", font=item_font)
    draw.text((245, 200), "400g Tub", fill="#555555", font=sub_font)

    # 3. Paneer Vacuum Pack (x=370 to 510, y=130 to 252)
    draw.rectangle([(370, 130), (510, 252)], fill="#fef9e7", outline="#f39c12", width=2)
    draw.rectangle([(380, 140), (500, 185)], fill="#f39c12")
    draw.text((392, 148), "MALAI PANEER", fill="#ffffff", font=item_font)
    draw.text((410, 168), "200g Fresh", fill="#ffffff", font=sub_font)
    draw.text((395, 205), "Rich in Protein", fill="#b7950b", font=sub_font)
    draw.text((400, 225), "High Calcium", fill="#7d6608", font=sub_font)

    # 4. Egg Crate (x=550 to 740, y=160 to 252)
    draw.rectangle([(550, 190), (740, 252)], fill="#d7ccc8", outline="#8d6e63", width=2)
    draw.text((565, 225), "Farm Eggs (6 pcs)", fill="#4e342e", font=item_font)
    # Eggs inside
    for egg_idx, ex in enumerate([570, 600, 630, 660, 690, 720]):
        draw.ellipse([(ex - 12, 155), (ex + 12, 195)], fill="#fff8e1", outline="#ffe082", width=1)

    # --- MIDDLE SHELF ITEMS (sy = 480) ---

    # 1. Fresh Palak / Spinach Bunch (x=70 to 270, y=340 to 472)
    draw.rectangle([(70, 420), (270, 472)], fill="#e8f5e9", outline="#2e7d32", width=2)
    # Leafy greens
    for lx, ly in [(90, 360), (130, 340), (170, 330), (210, 350), (240, 370)]:
        draw.ellipse([(lx - 25, ly - 20), (lx + 25, ly + 25)], fill="#4caf50", outline="#2e7d32")
    draw.rectangle([(110, 430), (230, 465)], fill="#2e7d32")
    draw.text((120, 438), "PALAK (SPINACH)", fill="#ffffff", font=item_font)

    # 2. Fresh Tomatoes Bowl (x=310 to 490, y=350 to 472)
    draw.ellipse([(310, 410), (490, 472)], fill="#ffffff", outline="#c0392b", width=2)
    # Red tomatoes
    for tx, ty in [(350, 370), (400, 355), (450, 370), (380, 395), (425, 395)]:
        draw.ellipse([(tx - 22, ty - 22), (tx + 22, ty + 22)], fill="#e74c3c", outline="#c0392b")
        # Green stem
        draw.rectangle([(tx - 3, ty - 25), (tx + 3, ty - 20)], fill="#27ae60")
    draw.text((365, 442), "Tomatoes (500g)", fill="#c0392b", font=item_font)

    # 3. Whole Wheat Bread Loaf (x=530 to 730, y=330 to 472)
    draw.rectangle([(530, 340), (730, 472)], fill="#ffe0b2", outline="#e65100", width=2)
    draw.rectangle([(545, 370), (715, 420)], fill="#e65100")
    draw.text((560, 380), "BROWN BREAD", fill="#ffffff", font=item_font)
    draw.text((575, 400), "100% Whole Wheat", fill="#ffe0b2", font=sub_font)
    draw.text((580, 440), "400g Fresh Loaf", fill="#bf360c", font=sub_font)

    # Bottom Crisper Drawer Labels
    draw.rectangle([(40, 505), (380, 580)], fill="#ffffff", outline="#bdc3c7")
    draw.text((120, 535), "VEGGIE CRISPER 1", fill="#7f8c8d", font=item_font)

    draw.rectangle([(420, 505), (760, 580)], fill="#ffffff", outline="#bdc3c7")
    draw.text((500, 535), "VEGGIE CRISPER 2", fill="#7f8c8d", font=item_font)

    # Watermark / Tag
    draw.rectangle([(width - 190, 15), (width - 35, 45)], fill="#ffffff", outline="#bdc3c7")
    draw.text((width - 180, 22), "DietSense · Smart Fridge", fill="#581825", font=sub_font)

    return im


def main():
    root_samples = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "samples"))
    public_samples = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "samples"))

    os.makedirs(root_samples, exist_ok=True)
    os.makedirs(public_samples, exist_ok=True)

    print("Generating Blinkit Sample Bill...")
    bill_im = generate_blinkit_bill()
    bill_png_path = os.path.join(root_samples, "blinkit_sample_bill.png")
    bill_pdf_path = os.path.join(root_samples, "blinkit_sample_bill.pdf")

    bill_im.save(bill_png_path, "PNG")
    # Save as PDF using PIL
    bill_rgb = bill_im.convert("RGB")
    bill_rgb.save(bill_pdf_path, "PDF", resolution=100.0)

    print("Generating Fridge Snapshot...")
    fridge_im = generate_fridge_snapshot()
    fridge_png_path = os.path.join(root_samples, "fridge_sample_snapshot.png")
    fridge_im.save(fridge_png_path, "PNG")

    # Copy to frontend/public/samples
    for f in ["blinkit_sample_bill.png", "blinkit_sample_bill.pdf", "fridge_sample_snapshot.png"]:
        src = os.path.join(root_samples, f)
        dst = os.path.join(public_samples, f)
        shutil.copy2(src, dst)
        print(f"Copied {f} to public/samples/")

    # Create README in samples
    readme_path = os.path.join(root_samples, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            "# DietSense Sample Test Assets\n\n"
            "This folder contains high-resolution sample assets for testing DietSense's offline grocery bill scanner and fridge snapshot vision processor.\n\n"
            "## Available Sample Files:\n\n"
            "1. **`blinkit_sample_bill.png`**:\n"
            "   - Realistic Indian quick-commerce grocery receipt (Paneer, Palak, Dahi, Bread, Milk, Tomatoes, Moong Dal, Oats).\n"
            "   - Ideal for testing receipt parsing and OCR fallback.\n\n"
            "2. **`blinkit_sample_bill.pdf`**:\n"
            "   - PDF format invoice for testing PDF text & table extraction.\n\n"
            "3. **`fridge_sample_snapshot.png`**:\n"
            "   - Refrigerator shelf snapshot with dairy, greens, protein, and staples.\n"
            "   - Ideal for testing fridge vision scanning and pantry auto-stocking.\n\n"
            "## How to Test:\n"
            "- Upload or drag & drop any of these files into the **Pantry / Scanner** tab in the web app.\n"
            "- Or click the **'⚡ Scan Sample Blinkit Bill'** or **'📸 Scan Fridge Photo'** preset buttons directly in the UI.\n"
        )
    print("Created samples/README.md successfully.")


if __name__ == "__main__":
    main()
