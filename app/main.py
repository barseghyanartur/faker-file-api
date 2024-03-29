import inspect
import json
import os
from copy import deepcopy
from enum import Enum
from io import BytesIO
from operator import itemgetter
from textwrap import indent
from typing import Any, Dict, Optional, Tuple, Type

from faker import Faker
from faker_file.base import FileMixin
from faker_file.providers.bin_file import BinFileProvider
# from faker_file.providers.bmp_file import (
#     BmpFileProvider,
#     GraphicBmpFileProvider,
# )
from faker_file.providers.csv_file import CsvFileProvider
from faker_file.providers.docx_file import DocxFileProvider
from faker_file.providers.eml_file import EmlFileProvider
from faker_file.providers.epub_file import EpubFileProvider
from faker_file.providers.generic_file import GenericFileProvider
# from faker_file.providers.gif_file import (
#     GifFileProvider,
#     GraphicGifFileProvider,
# )
from faker_file.providers.ico_file import (
    GraphicIcoFileProvider,
    IcoFileProvider,
)
from faker_file.providers.jpeg_file import (
    GraphicJpegFileProvider,
    JpegFileProvider,
)
from faker_file.providers.json_file import JsonFileProvider
from faker_file.providers.mixins.image_mixin import (
    IMAGEKIT_IMAGE_GENERATOR,
    PIL_IMAGE_GENERATOR,
)
# from faker_file.providers.mixins.image_mixin import (
#     WEASYPRINT_IMAGE_GENERATOR
# )
from faker_file.providers.mp3_file import (
    EDGE_TTS_MP3_GENERATOR,
    GTTS_MP3_GENERATOR,
    Mp3FileProvider,
)
from faker_file.providers.odp_file import OdpFileProvider
from faker_file.providers.ods_file import OdsFileProvider
from faker_file.providers.odt_file import OdtFileProvider
from faker_file.providers.pdf_file import (
    PDFKIT_PDF_GENERATOR,
    PIL_PDF_GENERATOR,
    REPORTLAB_PDF_GENERATOR,
    GraphicPdfFileProvider,
    PdfFileProvider,
)
from faker_file.providers.png_file import (
    GraphicPngFileProvider,
    PngFileProvider,
)
from faker_file.providers.pptx_file import PptxFileProvider
from faker_file.providers.rtf_file import RtfFileProvider
from faker_file.providers.svg_file import SvgFileProvider
from faker_file.providers.tar_file import TarFileProvider
# from faker_file.providers.tiff_file import (
#     GraphicTiffFileProvider,
#     TiffFileProvider,
# )
from faker_file.providers.txt_file import TxtFileProvider
from faker_file.providers.webp_file import GraphicWebpFileProvider
from faker_file.providers.xlsx_file import XlsxFileProvider
from faker_file.providers.xml_file import XmlFileProvider
from faker_file.providers.zip_file import ZipFileProvider
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseConfig, BaseModel, create_model

__author__ = "Artur Barseghyan <artur.barseghyan@gmail.com>"
__copyright__ = "2023 Artur Barseghyan"
__license__ = "MIT"
__all__ = [
    "providers",
    "root",
]


class PDFGeneratorCls(str, Enum):
    PIL_PDF_GENERATOR = PIL_PDF_GENERATOR
    PDFKIT_PDF_GENERATOR = PDFKIT_PDF_GENERATOR
    REPORTLAB_PDF_GENERATOR = REPORTLAB_PDF_GENERATOR


class ImageGeneratorCls(str, Enum):
    IMAGEKIT_IMAGE_GENERATOR = IMAGEKIT_IMAGE_GENERATOR
    PIL_IMAGE_GENERATOR = PIL_IMAGE_GENERATOR
    # WeasyPrint has some system dependencies that aren't properly
    # installed on onrender.com. Therefore, temporarily disable
    # WeasyPrint (although it works perfectly when installed on
    # a system with full control).
    # WEASYPRINT_IMAGE_GENERATOR = WEASYPRINT_IMAGE_GENERATOR


class Mp3GeneratorCls(str, Enum):
    GTTS_MP3_GENERATOR = GTTS_MP3_GENERATOR
    EDGE_TTS_MP3_GENERATOR = EDGE_TTS_MP3_GENERATOR


KWARGS_DROP = {
    "self",  # Drop as irrelevant
    "storage",  # Drop as non-supported arg
    "return",  # Drop as irrelevant
    # "mp3_generator_cls",  # Drop as non-supported arg
    # "mp3_generator_kwargs",  # Drop as non-supported arg
    # "pdf_generator_cls",  # Drop as non-supported arg
    # "pdf_generator_kwargs",  # Drop as non-supported arg
    "format_func",  # Drop as non-supported arg
    "raw",  # Drop `raw`, because we will be forcing raw=True for streaming
}

OVERRIDES = {
    # "BmpFileProvider.bmp_file": {
    #     "annotations": {
    #         "image_generator_cls": ImageGeneratorCls,
    #     },
    #     "model_props": {
    #         "image_generator_cls": (
    #             ImageGeneratorCls.WEASYPRINT_IMAGE_GENERATOR
    #         ),
    #     },
    # },
    "DocxFileProvider.docx_file": {
        "annotations": {
            "content": str,
        },
        "model_props": {
            "content": None,
        },
    },
    "GenericFileProvider.generic_file": {
        "annotations": {
            "content": str,
            "basename": Optional[str],
            "prefix": Optional[str],
        },
        "model_props": {
            "basename": None,
            "prefix": None,
        },
    },
    # "GifFileProvider.gif_file": {
    #     "annotations": {
    #         "image_generator_cls": ImageGeneratorCls,
    #     },
    #     "model_props": {
    #         "image_generator_cls": (
    #             ImageGeneratorCls.WEASYPRINT_IMAGE_GENERATOR
    #         ),
    #     },
    # },
    "IcoFileProvider.ico_file": {
        "annotations": {
            "image_generator_cls": ImageGeneratorCls,
        },
        "model_props": {
            "image_generator_cls": ImageGeneratorCls.IMAGEKIT_IMAGE_GENERATOR,
        },
    },
    "JpegFileProvider.jpeg_file": {
        "annotations": {
            "image_generator_cls": ImageGeneratorCls,
        },
        "model_props": {
            "image_generator_cls": ImageGeneratorCls.IMAGEKIT_IMAGE_GENERATOR,
        },
    },
    "Mp3FileProvider.mp3_file": {
        "annotations": {
            "mp3_generator_cls": Mp3GeneratorCls,
        },
        "model_props": {
            "mp3_generator_cls": Mp3GeneratorCls.GTTS_MP3_GENERATOR,
        },
    },
    "OdtFileProvider.odt_file": {
        "annotations": {
            "content": str,
        },
        "model_props": {
            "content": None,
        },
    },
    "PdfFileProvider.pdf_file": {
        "annotations": {
            "content": str,
            "pdf_generator_cls": PDFGeneratorCls,
        },
        "model_props": {
            "content": None,
            "pdf_generator_cls": PDFGeneratorCls.PIL_PDF_GENERATOR,
        },
    },
    "PngFileProvider.png_file": {
        "annotations": {
            "image_generator_cls": ImageGeneratorCls,
        },
        "model_props": {
            "image_generator_cls": ImageGeneratorCls.IMAGEKIT_IMAGE_GENERATOR,
        },
    },
    "SvgFileProvider.svg_file": {
        "annotations": {
            "image_generator_cls": ImageGeneratorCls,
        },
        "model_props": {
            "image_generator_cls": ImageGeneratorCls.IMAGEKIT_IMAGE_GENERATOR,
        },
    },
    # "TiffFileProvider.tiff_file": {
    #     "annotations": {
    #         "image_generator_cls": ImageGeneratorCls,
    #     },
    #     "model_props": {
    #         "image_generator_cls": (
    #             ImageGeneratorCls.WEASYPRINT_IMAGE_GENERATOR
    #         ),
    #     },
    # },
}


class Category(str, Enum):
    BINARY = "Binary"
    RICH_TEXT = "Rich Text"
    IMAGE = "Image"
    SPREADSHEET = "Spreadsheet"
    ARCHIVE = "Archive"
    PUBLISHING = "Publishing"
    MARKUP = "Markup"
    DATA = "Data"
    GENERIC = "Generic"
    AUDIO = "Audio"
    PRESENTATION = "Presentation"
    TEXT = "Text"


PROVIDERS = {
    BinFileProvider.bin_file.__name__: (
        BinFileProvider,
        Category.BINARY.value,
    ),
    # BmpFileProvider.bmp_file.__name__: (
    #     BmpFileProvider,
    #     Category.IMAGE.value,
    # ),
    CsvFileProvider.csv_file.__name__: (
        CsvFileProvider,
        Category.SPREADSHEET.value,
    ),
    DocxFileProvider.docx_file.__name__: (
        DocxFileProvider,
        Category.RICH_TEXT.value,
    ),
    EmlFileProvider.eml_file.__name__: (
        EmlFileProvider,
        Category.ARCHIVE.value,
    ),
    EpubFileProvider.epub_file.__name__: (
        EpubFileProvider,
        Category.PUBLISHING.value,
    ),
    # GifFileProvider.gif_file.__name__: (
    #     GifFileProvider,
    #     Category.IMAGE.value,
    # ),
    GenericFileProvider.generic_file.__name__: (
        GenericFileProvider,
        Category.GENERIC.value,
    ),
    # GraphicBmpFileProvider.graphic_bmp_file.__name__: (
    #     GraphicBmpFileProvider,
    #     Category.IMAGE.value,
    # ),
    # GraphicGifFileProvider.graphic_gif_file.__name__: (
    #     GraphicGifFileProvider,
    #     Category.IMAGE.value,
    # ),
    GraphicIcoFileProvider.graphic_ico_file.__name__: (
        GraphicIcoFileProvider,
        Category.IMAGE.value,
    ),
    GraphicJpegFileProvider.graphic_jpeg_file.__name__: (
        GraphicJpegFileProvider,
        Category.IMAGE.value,
    ),
    GraphicPdfFileProvider.graphic_pdf_file.__name__: (
        GraphicPdfFileProvider,
        Category.PUBLISHING.value,
    ),
    GraphicPngFileProvider.graphic_png_file.__name__: (
        GraphicPngFileProvider,
        Category.IMAGE.value,
    ),
    # GraphicTiffFileProvider.graphic_tiff_file.__name__: (
    #     GraphicTiffFileProvider,
    #     Category.IMAGE.value,
    # ),
    GraphicWebpFileProvider.graphic_webp_file.__name__: (
        GraphicWebpFileProvider,
        Category.IMAGE.value,
    ),
    IcoFileProvider.ico_file.__name__: (
        IcoFileProvider,
        Category.IMAGE.value,
    ),
    JpegFileProvider.jpeg_file.__name__: (
        JpegFileProvider,
        Category.IMAGE.value,
    ),
    JsonFileProvider.json_file.__name__: (
        JsonFileProvider,
        Category.DATA.value,
    ),
    Mp3FileProvider.mp3_file.__name__: (
        Mp3FileProvider,
        Category.AUDIO.value,
    ),
    OdpFileProvider.odp_file.__name__: (
        OdpFileProvider,
        Category.PRESENTATION.value,
    ),
    OdsFileProvider.ods_file.__name__: (
        OdsFileProvider,
        Category.SPREADSHEET.value,
    ),
    OdtFileProvider.odt_file.__name__: (
        OdtFileProvider,
        Category.RICH_TEXT.value,
    ),
    PdfFileProvider.pdf_file.__name__: (
        PdfFileProvider,
        Category.PUBLISHING.value,
    ),
    PngFileProvider.png_file.__name__: (
        PngFileProvider,
        Category.IMAGE.value,
    ),
    PptxFileProvider.pptx_file.__name__: (
        PptxFileProvider,
        Category.PRESENTATION.value,
    ),
    RtfFileProvider.rtf_file.__name__: (
        RtfFileProvider,
        Category.RICH_TEXT.value,
    ),
    SvgFileProvider.svg_file.__name__: (
        SvgFileProvider,
        Category.IMAGE.value,
    ),
    TarFileProvider.tar_file.__name__: (
        TarFileProvider,
        Category.ARCHIVE.value,
    ),
    # TiffFileProvider.tiff_file.__name__: (
    #     TiffFileProvider,
    #     Category.IMAGE.value,
    # ),
    TxtFileProvider.txt_file.__name__: (
        TxtFileProvider,
        Category.TEXT.value,
    ),
    # WebpFileProvider.webp_file.__name__: (
    #     WebpFileProvider,
    #     Category.IMAGE.value,
    # ),
    XlsxFileProvider.xlsx_file.__name__: (
        XlsxFileProvider,
        Category.SPREADSHEET.value,
    ),
    XmlFileProvider.xml_file.__name__: (
        XmlFileProvider,
        Category.DATA,
    ),
    ZipFileProvider.zip_file.__name__: (
        ZipFileProvider,
        Category.ARCHIVE,
    ),
}

# See this
# https://docs.pydantic.dev/usage/models/#model-creation-from-namedtuple-or-typeddict
# https://github.com/pydantic/pydantic/issues/1612


def build_schema_extra(annotations, model_props) -> Dict[str, Any]:
    """Build schema extra values.

    {
        "schema_extra": {
            "example": {
                "prefix": "",
            },
        }
    }
    """
    clean_props = dict(filter(itemgetter(1), model_props.items()))
    if clean_props:
        # For example, [clean_props, {"a": "A"}]
        return {"schema_extra": {"examples": [clean_props, {}]}}
    return {}


def build_pydantic_model(
    cls: Type[FileMixin], method_name: str
) -> Tuple[Type[BaseModel], Dict[str, Any]]:
    """Build pydantic model."""
    method = getattr(cls, method_name)
    method_specs = inspect.getfullargspec(method)

    kwargs = deepcopy(method_specs.args[1:])  # Omit `self`
    defaults = deepcopy(method_specs.defaults)
    model_props = dict(zip(kwargs, defaults))
    annotations = deepcopy(method_specs.annotations)

    # Override the type definition for mp3_generator_cls
    override = OVERRIDES.get(f"{cls.__name__}.{method_name}", None)
    if override:
        annotations.update(override["annotations"])
        model_props.update(override["model_props"])

    for kwarg_name in KWARGS_DROP:
        annotations.pop(kwarg_name, None)
        model_props.pop(kwarg_name, None)

    model_config = {
        k: (v, model_props.get(k, ...)) for k, v in annotations.items()
    }

    config_kwargs = {
        "title": method_name.split("_file")[0],
        "arbitrary_types_allowed": True,
    }
    config_kwargs.update(build_schema_extra(annotations, model_props))
    config_cls: BaseConfig = type("Config", (BaseConfig,), config_kwargs)
    method_model_cls = create_model(  # noqa
        __model_name=f"{method_name}_model",
        __config__=config_cls,
        **model_config,
    )

    return method_model_cls, model_props


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Expose 'Content-Disposition' header
    expose_headers=["Content-Disposition"],
)


@app.exception_handler(Exception)
async def validation_exception_handler(request: Request, exc: Exception):
    """Generic error handling."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            {"detail": str(exc), "body": type(exc).__name__}
        ),
    )


@app.get("/heartbeat/")
async def root():
    """Heartbeat."""
    return {"message": "Heartbeat"}


@app.get("/providers/")
async def providers():
    """Providers."""
    return {
        f"/{name}/": cls.__doc__.split("\n")[0]
        for name, (cls, tag) in PROVIDERS.items()
    }


def generate_func(__method_name, __provider, __tag):
    __model, __props = build_pydantic_model(__provider, __method_name)
    __json = indent(
        json.dumps(__props, indent=4)[1:-1].replace("\n", "\n"), "    "
    )
    __description = f"""\n**Example Value:**\n
    {{
    {__json}
    }}
    """

    @app.post(
        f"/{__method_name}/",
        summary=__provider.__doc__.split("\n")[0],
        description=f"{__description}",
        tags=[__tag],
    )
    async def _provider_func(item: __model):
        _faker = Faker()  # TODO: Let specify the locale in the params
        _method = getattr(__provider(_faker), __method_name)
        _kwargs = deepcopy(item.__dict__)
        _kwargs.update(
            {"raw": True}
        )  # Force bytes, so that we stream the response
        _raw = _method(**_kwargs)
        _test_file = BytesIO(_raw)
        _test_file.name = os.path.basename(_raw.data["filename"])
        return StreamingResponse(
            _test_file,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"inline; filename={_test_file.name}"
            },
        )

    return _provider_func


for __method_name, (__provider, __tag) in PROVIDERS.items():
    __provider_func = generate_func(__method_name, __provider, __tag)
    __provider_func.__doc__ = __method_name
    globals()[__method_name] = deepcopy(__provider_func)
    __all__.append(__method_name)

del __provider_func
del __method_name
del __provider

__all__ = tuple(__all__)
