import io
from pathlib import Path

import img2pdf
import streamlit as st
from pdf2image import convert_from_bytes
from PIL import Image

DPI = 300
BLEED_IN = 0.125
WHITE_PPI = 0.002252
CREAM_PPI = 0.0025

LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"
BRAND_NAME = "Kingdom Ink"
BRAND_TAGLINE = "Print-ready KDP wraparound covers, in minutes."


def in_to_px(inches: float) -> int:
    return int(round(inches * DPI))


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def load_upload(upload) -> Image.Image:
    data = upload.getvalue()
    name = upload.name.lower()
    if name.endswith(".pdf"):
        pages = convert_from_bytes(data, dpi=DPI)
        if not pages:
            raise ValueError(f"Could not rasterize PDF: {upload.name}")
        return pages[0].convert("RGB")
    return Image.open(io.BytesIO(data)).convert("RGB")


def fit_cover(img: Image.Image, w_px: int, h_px: int) -> Image.Image:
    """Scale to fully cover the panel using LANCZOS, center-crop overflow."""
    iw, ih = img.size
    scale = max(w_px / iw, h_px / ih)
    new_w = max(1, int(round(iw * scale)))
    new_h = max(1, int(round(ih * scale)))
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - w_px) // 2
    top = (new_h - h_px) // 2
    return resized.crop((left, top, left + w_px, top + h_px))


def extend_bleed(
    trim_img: Image.Image, top: int, right: int, bottom: int, left: int
) -> Image.Image:
    """Add bleed by replicating edge pixels outward."""
    w, h = trim_img.size
    new = Image.new("RGB", (w + left + right, h + top + bottom))
    new.paste(trim_img, (left, top))
    if top > 0:
        strip = trim_img.crop((0, 0, w, 1)).resize((w, top), Image.LANCZOS)
        new.paste(strip, (left, 0))
    if bottom > 0:
        strip = trim_img.crop((0, h - 1, w, h)).resize((w, bottom), Image.LANCZOS)
        new.paste(strip, (left, top + h))
    if left > 0:
        strip = trim_img.crop((0, 0, 1, h)).resize((left, h), Image.LANCZOS)
        new.paste(strip, (0, top))
    if right > 0:
        strip = trim_img.crop((w - 1, 0, w, h)).resize((right, h), Image.LANCZOS)
        new.paste(strip, (left + w, top))
    if top > 0 and left > 0:
        new.paste(trim_img.crop((0, 0, 1, 1)).resize((left, top)), (0, 0))
    if top > 0 and right > 0:
        new.paste(
            trim_img.crop((w - 1, 0, w, 1)).resize((right, top)), (left + w, 0)
        )
    if bottom > 0 and left > 0:
        new.paste(
            trim_img.crop((0, h - 1, 1, h)).resize((left, bottom)), (0, top + h)
        )
    if bottom > 0 and right > 0:
        new.paste(
            trim_img.crop((w - 1, h - 1, w, h)).resize((right, bottom)),
            (left + w, top + h),
        )
    return new


def build_cover(
    front: Image.Image,
    back: Image.Image,
    trim_w: float,
    trim_h: float,
    spine_w: float,
    has_bleed: bool,
    spine_color_hex: str,
) -> tuple[Image.Image, dict]:
    canvas_w_in = trim_w * 2 + spine_w + BLEED_IN * 2
    canvas_h_in = trim_h + BLEED_IN * 2

    canvas_w_px = in_to_px(canvas_w_in)
    canvas_h_px = in_to_px(canvas_h_in)
    bleed_px = in_to_px(BLEED_IN)
    trim_w_px = in_to_px(trim_w)
    trim_h_px = in_to_px(trim_h)
    spine_w_px = in_to_px(spine_w)

    # Recompute panel widths from canvas to absorb rounding
    back_panel_w = bleed_px + trim_w_px
    front_panel_x = back_panel_w + spine_w_px
    front_panel_w = canvas_w_px - front_panel_x
    panel_h = canvas_h_px

    spine_rgb = hex_to_rgb(spine_color_hex)
    canvas = Image.new("RGB", (canvas_w_px, canvas_h_px), spine_rgb)

    if has_bleed:
        back_fit = fit_cover(back, back_panel_w, panel_h)
        front_fit = fit_cover(front, front_panel_w, panel_h)
    else:
        back_trim = fit_cover(back, trim_w_px, trim_h_px)
        front_trim = fit_cover(front, trim_w_px, trim_h_px)
        back_fit = extend_bleed(
            back_trim, top=bleed_px, right=0, bottom=bleed_px, left=bleed_px
        )
        front_fit = extend_bleed(
            front_trim, top=bleed_px, right=bleed_px, bottom=bleed_px, left=0
        )

    canvas.paste(back_fit, (0, 0))
    canvas.paste(front_fit, (front_panel_x, 0))

    spec = {
        "canvas_w_in": canvas_w_in,
        "canvas_h_in": canvas_h_in,
        "canvas_w_px": canvas_w_px,
        "canvas_h_px": canvas_h_px,
        "spine_w_in": spine_w,
        "fold_left_in": BLEED_IN + trim_w,
        "fold_right_in": BLEED_IN + trim_w + spine_w,
    }
    return canvas, spec


def canvas_to_pdf(canvas: Image.Image, w_in: float, h_in: float) -> bytes:
    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=95, dpi=(DPI, DPI), subsampling=0)
    buf.seek(0)
    layout = img2pdf.get_layout_fun(
        pagesize=(img2pdf.in_to_pt(w_in), img2pdf.in_to_pt(h_in))
    )
    return img2pdf.convert(buf.getvalue(), layout_fun=layout)


def render_brand() -> None:
    if LOGO_PATH.exists() and hasattr(st, "logo"):
        try:
            st.logo(str(LOGO_PATH), size="large")
        except Exception:
            pass

    st.title("KDP Wraparound Cover Generator")
    st.caption(
        "Composite a print-ready wraparound paperback cover at 300 DPI for "
        "Amazon KDP."
    )


def main() -> None:
    page_icon = str(LOGO_PATH) if LOGO_PATH.exists() else "📖"
    st.set_page_config(
        page_title=f"{BRAND_NAME} — KDP Cover Studio",
        page_icon=page_icon,
        layout="wide",
    )

    render_brand()

    with st.sidebar:
        st.header("Cover files")
        front_file = st.file_uploader(
            "Front cover", type=["pdf", "png", "jpg", "jpeg"], key="front"
        )
        back_file = st.file_uploader(
            "Back cover", type=["pdf", "png", "jpg", "jpeg"], key="back"
        )

        st.header("Book specs")
        trim_w = st.number_input(
            "Trim width (inches)",
            min_value=4.0,
            max_value=8.5,
            value=6.0,
            step=0.125,
            format="%.3f",
        )
        trim_h = st.number_input(
            "Trim height (inches)",
            min_value=6.0,
            max_value=11.0,
            value=9.0,
            step=0.125,
            format="%.3f",
        )
        page_count = st.number_input(
            "Page count", min_value=24, max_value=828, value=200, step=2
        )
        paper = st.selectbox(
            "Paper type",
            ["White (0.002252″/page)", "Cream (0.0025″/page)"],
        )

        st.header("Layout")
        has_bleed = st.checkbox(
            "Uploaded covers include bleed?", value=False
        )
        spine_color = st.color_picker("Spine color", value="#FFFFFF")

    ppi = WHITE_PPI if paper.startswith("White") else CREAM_PPI
    spine_w = page_count * ppi

    canvas_w_in = trim_w * 2 + spine_w + BLEED_IN * 2
    canvas_h_in = trim_h + BLEED_IN * 2
    fold_left = BLEED_IN + trim_w
    fold_right = fold_left + spine_w

    st.subheader("Spec summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Canvas", f"{canvas_w_in:.4f}″ × {canvas_h_in:.4f}″")
    c2.metric("Spine width", f"{spine_w:.4f}″")
    c3.metric("Left fold", f"{fold_left:.4f}″")
    c4.metric("Right fold", f"{fold_right:.4f}″")

    if spine_w < 0.0625:
        st.error(
            f"Spine width is {spine_w:.4f}″ — too narrow for spine text. "
            "KDP recommends a minimum of 0.0625″ (about 80 pages) before "
            "placing text on the spine."
        )
    elif spine_w < 0.25:
        st.warning(
            f"Spine width is {spine_w:.4f}″ — keep spine text minimal. "
            "Use a small font and tight margins."
        )

    st.divider()

    if not (front_file and back_file):
        st.info("Upload both a front and back cover in the sidebar to begin.")
        return

    if st.button("Generate cover", type="primary"):
        try:
            with st.spinner("Rasterizing inputs…"):
                front_img = load_upload(front_file)
                back_img = load_upload(back_file)

            with st.spinner("Compositing canvas at 300 DPI…"):
                canvas, spec = build_cover(
                    front=front_img,
                    back=back_img,
                    trim_w=trim_w,
                    trim_h=trim_h,
                    spine_w=spine_w,
                    has_bleed=has_bleed,
                    spine_color_hex=spine_color,
                )

            with st.spinner("Building preview…"):
                preview_w = 1400
                ratio = preview_w / canvas.size[0]
                preview = canvas.resize(
                    (preview_w, int(canvas.size[1] * ratio)), Image.LANCZOS
                )
                st.image(
                    preview,
                    caption=(
                        f"{spec['canvas_w_in']:.3f}″ × "
                        f"{spec['canvas_h_in']:.3f}″ "
                        f"({spec['canvas_w_px']} × {spec['canvas_h_px']} px)"
                    ),
                    use_container_width=True,
                )

            with st.spinner("Writing PDF…"):
                pdf_bytes = canvas_to_pdf(
                    canvas, spec["canvas_w_in"], spec["canvas_h_in"]
                )

            st.success("Cover ready.")
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name="kingdom-ink-cover.pdf",
                mime="application/pdf",
                type="primary",
            )
        except Exception as exc:
            st.exception(exc)

    st.divider()
    st.markdown(
        f"<p style='text-align:center;color:#888;font-size:0.85rem;"
        f"margin-top:1rem;'>{BRAND_NAME} &middot; KDP Cover Studio</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
