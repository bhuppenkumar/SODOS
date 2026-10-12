import os
import gc
import io
import pypdfium2 as pdfium
from pypdf import PdfReader, PdfWriter
from PIL import Image, ImageEnhance

def get_all_pdf_previews(pdf_path, max_size=(220, 220)):
    """Renders all pages of a single PDF into a list of PIL preview images."""
    previews = []
    try:
        pdf = pdfium.PdfDocument(pdf_path)
        for page in pdf:
            pil_img = page.render(scale=0.8).to_pil()
            pil_img.thumbnail(max_size)
            previews.append(pil_img)
    except Exception:
        pass
    return previews

def get_multiple_pdf_previews(pdf_paths, max_size=(220, 220)):
    """Renders all pages across multiple PDFs for merging previews."""
    previews = []
    for f_idx, path in enumerate(pdf_paths):
        try:
            pdf = pdfium.PdfDocument(path)
            fname = os.path.basename(path)
            for p_idx, page in enumerate(pdf):
                pil_img = page.render(scale=0.8).to_pil()
                pil_img.thumbnail(max_size)
                previews.append((f_idx, p_idx, fname, pil_img))
        except Exception:
            pass
    return previews

def get_image_previews(image_paths, max_size=(220, 220)):
    """Renders preview thumbnails for a list of image files."""
    previews = []
    for path in image_paths:
        try:
            img = Image.open(path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail(max_size)
            previews.append((os.path.basename(path), img))
        except Exception:
            pass
    return previews

def apply_effects_to_preview(pil_img, brightness=1.0, contrast=1.0, sharpness=1.0, angle=0):
    """Applies rotation, brightness, contrast, and sharpness adjustments to a preview image."""
    if pil_img is None:
        return None
    img = pil_img.copy()
    if angle != 0:
        img = img.rotate(-angle, expand=True)
    if brightness != 1.0:
        img = ImageEnhance.Brightness(img).enhance(brightness)
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if sharpness != 1.0:
        img = ImageEnhance.Sharpness(img).enhance(sharpness)
    return img

def strip_metadata(writer):
    """Strips sensitive tracking metadata from output PDFs."""
    writer.add_metadata({
        '/Producer': 'SODOS Offline Privacy Engine',
        '/Creator': 'SODOS',
        '/Author': 'Anonymous',
        '/Title': 'Document'
    })

def parse_page_ranges(range_str, total_pages):
    """Parses page ranges like '5-10, 12' into zero-indexed integer lists."""
    pages = set()
    parts = range_str.replace(" ", "").split(",")
    for part in parts:
        if not part:
            continue
        if "-" in part:
            subparts = part.split("-")
            if len(subparts) == 2 and subparts[0].isdigit() and subparts[1].isdigit():
                start = max(1, int(subparts[0]))
                end = min(total_pages, int(subparts[1]))
                for p in range(start, end + 1):
                    pages.add(p - 1)
        elif part.isdigit():
            p = int(part)
            if 1 <= p <= total_pages:
                pages.add(p - 1)
    return sorted(list(pages))

def compress_pdf_to_target(pdf_path, output_path, target_bytes, brightness=1.0, contrast=1.0, sharpness=1.0, page_rotations=None, deleted_pages=None):
    """Low-RAM page-by-page streaming engine with rotation, deletion, brightness, contrast, and sharpness control."""
    deleted = deleted_pages or set()
    rotations = page_rotations or {}

    reader = PdfReader(pdf_path)
    if os.path.getsize(pdf_path) <= target_bytes and not deleted and not rotations and brightness == 1.0 and contrast == 1.0 and sharpness == 1.0:
        writer = PdfWriter()
        for idx, page in enumerate(reader.pages):
            if idx not in deleted:
                writer.add_page(page)
        strip_metadata(writer)
        with open(output_path, "wb") as f:
            writer.write(f)
        return True

    quality_setting = 75
    scale_factor = 1.0

    for _ in range(4):
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for idx, page in enumerate(reader.pages):
            if idx in deleted:
                continue

            if idx in rotations and rotations[idx] != 0:
                page.rotate(rotations[idx])

            for img_obj in page.images:
                try:
                    raw_img = Image.open(io.BytesIO(img_obj.data))
                    if raw_img.mode in ("RGBA", "P"):
                        raw_img = raw_img.convert("RGB")
                    
                    if scale_factor < 1.0:
                        new_w = int(raw_img.width * scale_factor)
                        new_h = int(raw_img.height * scale_factor)
                        raw_img = raw_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    if brightness != 1.0:
                        raw_img = ImageEnhance.Brightness(raw_img).enhance(brightness)
                    if contrast != 1.0:
                        raw_img = ImageEnhance.Contrast(raw_img).enhance(contrast)
                    if sharpness != 1.0:
                        raw_img = ImageEnhance.Sharpness(raw_img).enhance(sharpness)

                    img_obj.replace(raw_img, quality=quality_setting)
                    del raw_img
                except Exception:
                    continue
            
            page.compress_content_streams()
            writer.add_page(page)

        strip_metadata(writer)
        with open(output_path, "wb") as f:
            writer.write(f)

        del reader, writer
        gc.collect()

        if os.path.getsize(output_path) <= target_bytes:
            break
        
        quality_setting -= 20
        scale_factor *= 0.75

    return True

def compress_image_to_target(image_path, output_path, target_bytes, brightness=1.0, contrast=1.0, sharpness=1.0, angle=0):
    """Compresses an image under target bytes with rotation, brightness, contrast, and sharpness tuning."""
    with Image.open(image_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        if angle != 0:
            img = img.rotate(-angle, expand=True)
        if brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        if sharpness != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(sharpness)

        quality = 85
        while quality >= 15:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", optimize=True, quality=quality)
            if buffer.tell() <= target_bytes or quality <= 15:
                with open(output_path, "wb") as f:
                    f.write(buffer.getvalue())
                break
            quality -= 10
    gc.collect()
    return True

def extract_pdf_range(pdf_path, output_path, page_indices, page_rotations=None, deleted_pages=None):
    """Extracts page indices with rotation and deletion support into a single PDF."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    rotations = page_rotations or {}
    deleted = deleted_pages or set()
    
    for idx in page_indices:
        if idx < len(reader.pages) and idx not in deleted:
            page = reader.pages[idx]
            if idx in rotations and rotations[idx] != 0:
                page.rotate(rotations[idx])
            writer.add_page(page)
            
    strip_metadata(writer)
    with open(output_path, "wb") as f:
        writer.write(f)
    return True

def split_pdf_pages_individual(pdf_path, output_folder, page_indices, page_rotations=None, deleted_pages=None):
    """Splits specified pages into separate individual files with rotation/deletion support."""
    reader = PdfReader(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    rotations = page_rotations or {}
    deleted = deleted_pages or set()
    
    for idx in page_indices:
        if idx < len(reader.pages) and idx not in deleted:
            writer = PdfWriter()
            page = reader.pages[idx]
            if idx in rotations and rotations[idx] != 0:
                page.rotate(rotations[idx])
            writer.add_page(page)
            strip_metadata(writer)
            
            out_file = os.path.join(output_folder, f"{base_name}_page_{idx + 1}.pdf")
            with open(out_file, "wb") as f:
                writer.write(f)
            del writer
            gc.collect()
    return True

def merge_pdfs_advanced(pdf_paths, output_path, page_rotations=None, deleted_pages=None):
    """Merges multiple PDFs with page-level rotation and deletion support."""
    writer = PdfWriter()
    rotations = page_rotations or {}
    deleted = deleted_pages or set()
    
    global_idx = 0
    for path in pdf_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            if global_idx not in deleted:
                if global_idx in rotations and rotations[global_idx] != 0:
                    page.rotate(rotations[global_idx])
                writer.add_page(page)
            global_idx += 1
            
    strip_metadata(writer)
    with open(output_path, "wb") as f:
        writer.write(f)
    return True

def images_to_pdf(image_paths, output_path, page_rotations=None, deleted_pages=None):
    """Combines multiple images into a single PDF with rotation and deletion support."""
    rotations = page_rotations or {}
    deleted = deleted_pages or set()
    pil_images = []
    
    for idx, path in enumerate(image_paths):
        if idx in deleted:
            continue
        img = Image.open(path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        if idx in rotations and rotations[idx] != 0:
            img = img.rotate(-rotations[idx], expand=True)
        pil_images.append(img)
        
    if pil_images:
        pil_images[0].save(output_path, "PDF", resolution=100.0, save_all=True, append_images=pil_images[1:])
    return True

def pdf_to_images(pdf_path, output_folder, page_rotations=None, deleted_pages=None):
    """Extracts PDF pages as PNG images with rotation and deletion support."""
    rotations = page_rotations or {}
    deleted = deleted_pages or set()
    pdf = pdfium.PdfDocument(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    for idx, page in enumerate(pdf):
        if idx in deleted:
            continue
        pil_img = page.render(scale=1.5).to_pil()
        if idx in rotations and rotations[idx] != 0:
            pil_img = pil_img.rotate(-rotations[idx], expand=True)
        out_file = os.path.join(output_folder, f"{base_name}_page_{idx + 1}.png")
        pil_img.save(out_file, "PNG")
    return True

def encrypt_pdf(input_path, output_path, password, page_rotations=None, deleted_pages=None):
    """Encrypts a PDF document with password protection, rotation, and page deletion support."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    rotations = page_rotations or {}
    deleted = deleted_pages or set()
    
    for idx, page in enumerate(reader.pages):
        if idx not in deleted:
            if idx in rotations and rotations[idx] != 0:
                page.rotate(rotations[idx])
            writer.add_page(page)
            
    writer.encrypt(password)
    strip_metadata(writer)
    with open(output_path, "wb") as f:
        writer.write(f)
    return True