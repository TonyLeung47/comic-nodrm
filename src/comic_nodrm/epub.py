from pathlib import Path, PurePath
import zipfile
from bs4 import BeautifulSoup, element
import os

IMAGE_SUFFIX = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]


def epub2cbz(epub: Path, output: Path):
    """
    Convert epub to cbz

    Args:
        epub (Path): epub file
        output (Path): output name
    """
    with zipfile.ZipFile(epub, "r") as z:
        container_xml = z.read("META-INF/container.xml").decode()
        opf_path = container_xml.split('full-path="')[1].split('"')[0]
        opf = z.read(opf_path).decode()
        soup = BeautifulSoup(opf, "xml")
        items: dict[str, str] = {item.get("id"): item.get("href") for item in soup.find_all("item")}
        itemrefs = [i.get("idref") for i in soup.find_all("itemref")]

        images: list[PurePath] = []
        for itemref in itemrefs:
            item_path = PurePath(opf_path).parent / items[itemref]

            # when item is image
            if item_path.suffix in IMAGE_SUFFIX:
                images.append(item_path)

            # when item is xhtml
            elif item_path.suffix in (".xhtml", ".html"):
                xhtml = z.read(item_path.as_posix()).decode()
                soup = BeautifulSoup(xhtml, "html.parser")
                image_tag = soup.find("image") or soup.find("img")
                if type(image_tag) == element.Tag:
                    link = image_tag.get("xlink:href") or image_tag.get("src")
                    if type(link) == list:
                        images.extend([item_path.parent / l for l in link])
                    elif type(link) == str:
                        images.append(item_path.parent / link)

        with zipfile.ZipFile(output, "w") as zout:
            for index, image_path in enumerate(images, 1):
                image = z.read(PurePath(os.path.normpath(image_path)).as_posix())
                zout.writestr(f"{index:05}{image_path.suffix}", image)
