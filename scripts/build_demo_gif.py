"""Assemble the real saved-result UI screenshots, not a live inference recording."""

from pathlib import Path

from PIL import Image


def main():
    folder = Path(__file__).resolve().parents[1] / "docs/images"
    names = (
        "accepted-capex-desktop.png",
        "accepted-fact-desktop.png",
        "accepted-refusal-desktop.png",
    )
    images = []
    for name in names:
        with Image.open(folder / name) as image:
            images.append(image.convert("RGB"))
    size = (max(i.width for i in images), max(i.height for i in images))
    frames = []
    for image in images:
        canvas = Image.new("RGB", size, "white")
        canvas.paste(image, (0, 0))
        frames.append(canvas)
    target = folder / "accepted-workspace.gif"
    frames[0].save(
        target, save_all=True, append_images=frames[1:], duration=4000, loop=0, disposal=2
    )
    with Image.open(target) as output:
        assert output.n_frames == 3 and output.size == size
    print(f"Saved-result walkthrough: {target}")


if __name__ == "__main__":
    main()
