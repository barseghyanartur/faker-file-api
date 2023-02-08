import inspect
import os
from copy import deepcopy
from io import BytesIO
from operator import itemgetter
from typing import Any, Dict, Type

from faker import Faker
from faker_file.base import FileMixin
from faker_file.providers.bin_file import BinFileProvider
from faker_file.providers.csv_file import CsvFileProvider
from faker_file.providers.docx_file import DocxFileProvider
from faker_file.providers.eml_file import EmlFileProvider
from faker_file.providers.epub_file import EpubFileProvider
from faker_file.providers.ico_file import IcoFileProvider
from faker_file.providers.jpeg_file import JpegFileProvider
from faker_file.providers.mp3_file import Mp3FileProvider
from faker_file.providers.odp_file import OdpFileProvider
from faker_file.providers.ods_file import OdsFileProvider
from faker_file.providers.odt_file import OdtFileProvider
from faker_file.providers.pdf_file import PdfFileProvider
from faker_file.providers.png_file import PngFileProvider
from faker_file.providers.pptx_file import PptxFileProvider
from faker_file.providers.rtf_file import RtfFileProvider
from faker_file.providers.svg_file import SvgFileProvider
from faker_file.providers.tar_file import TarFileProvider
from faker_file.providers.txt_file import TxtFileProvider
from faker_file.providers.webp_file import WebpFileProvider
from faker_file.providers.xlsx_file import XlsxFileProvider
from faker_file.providers.zip_file import ZipFileProvider
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, BaseConfig
from pydantic import create_model

__author__ = "Artur Barseghyan <artur.barseghyan@gmail.com>"
__copyright__ = "2023 Artur Barseghyan"
__license__ = "MIT"
__all__ = ["root", "providers",]

KWARGS_DROP = {
    "self",  # Drop as irrelevant
    "storage",  # Drop as non-supported arg
    "return",  # Drop as irrelevant
    "mp3_generator_cls",  # Drop as non-supported arg
    "mp3_generator_kwargs",  # Drop as non-supported arg
    "raw",  # Drop `raw`, because we will be forcing raw=True for streaming
}
PROVIDERS = {
    BinFileProvider.bin_file.__name__: BinFileProvider,
    CsvFileProvider.csv_file.__name__: CsvFileProvider,
    DocxFileProvider.docx_file.__name__: DocxFileProvider,
    EmlFileProvider.eml_file.__name__: EmlFileProvider,
    EpubFileProvider.epub_file.__name__: EpubFileProvider,
    IcoFileProvider.ico_file.__name__: IcoFileProvider,
    JpegFileProvider.jpeg_file.__name__: JpegFileProvider,
    Mp3FileProvider.mp3_file.__name__: Mp3FileProvider,
    OdpFileProvider.odp_file.__name__: OdpFileProvider,
    OdsFileProvider.ods_file.__name__: OdsFileProvider,
    OdtFileProvider.odt_file.__name__: OdtFileProvider,
    PdfFileProvider.pdf_file.__name__: PdfFileProvider,
    PngFileProvider.png_file.__name__: PngFileProvider,
    PptxFileProvider.pptx_file.__name__: PptxFileProvider,
    RtfFileProvider.rtf_file.__name__: RtfFileProvider,
    SvgFileProvider.svg_file.__name__: SvgFileProvider,
    TarFileProvider.tar_file.__name__: TarFileProvider,
    TxtFileProvider.txt_file.__name__: TxtFileProvider,
    WebpFileProvider.webp_file.__name__: WebpFileProvider,
    XlsxFileProvider.xlsx_file.__name__: XlsxFileProvider,
    ZipFileProvider.zip_file.__name__: ZipFileProvider,
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
        return {"schema_extra": {"example": clean_props}}
    return {}


def build_pydantic_model(cls: Type[FileMixin], method_name: str) -> Type[BaseModel]:
    """Build pydantic model."""
    method = getattr(cls, method_name)
    method_specs = inspect.getfullargspec(method)

    kwargs = deepcopy(method_specs.args[1:])  # Omit `self`
    defaults = deepcopy(method_specs.defaults)
    model_props = dict(zip(kwargs, defaults))
    annotations = deepcopy(method_specs.annotations)

    for kwarg_name in KWARGS_DROP:
        annotations.pop(kwarg_name, None)
        model_props.pop(kwarg_name, None)

    model_config = {k: (v, model_props.get(k, ...)) for k, v in annotations.items()}
    config_kwargs = {
        "arbitrary_types_allowed": True,
    }
    config_kwargs.update(build_schema_extra(annotations, model_props))
    config_cls: BaseConfig = type("Config", (BaseConfig,), config_kwargs)
    method_model_cls = create_model(  # noqa
        __model_name=f"{method_name}_model",
        __config__=config_cls,
        **model_config,
    )

    return method_model_cls


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/heartbeat/")
async def root():
    """Heartbeat."""
    return {"message": "Heartbeat"}


@app.get("/providers/")
async def providers():
    """Providers."""
    return {f"/{name}/": cls.__doc__.split("\n")[0] for name, cls in PROVIDERS.items()}


def generate_func(__method_name, __provider):
    __model = build_pydantic_model(__provider, __method_name)

    @app.post(
        f"/{__method_name}/",
        summary=f"{__method_name}",  # TODO
        description=f"{__method_name}",  # TODO
    )
    async def _provider_func(item: __model):
        _faker = Faker()  # TODO: Let specify the locale in the params
        _method = getattr(__provider(_faker), __method_name)
        _kwargs = deepcopy(item.__dict__)
        _kwargs.update({"raw": True})  # Force bytes, so that we stream the response
        _raw = _method(**_kwargs)
        _test_file = BytesIO(_raw)
        _test_file.name = os.path.basename(_raw.data["filename"])
        return StreamingResponse(
            _test_file,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"inline; filename={_test_file.name}"}
        )

    return _provider_func


for __method_name, __provider in PROVIDERS.items():
    __provider_func = generate_func(__method_name, __provider)
    __provider_func.__doc__ = __method_name
    globals()[__method_name] = deepcopy(__provider_func)
    __all__.append(__method_name)

del __provider_func
del __method_name
del __provider

__all__ = tuple(__all__)
