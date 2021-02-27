export class Constants {
  static readonly AUTO_REFRESH_INTERVAL = 30000;
  static readonly ALLOWED_UPLOAD_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff"];
  static readonly ALLOWED_UNCOMPRESSED_SOURCE_UPLOAD_EXTENSIONS = [
    ".xisf",
    ".fits",
    ".fit",
    ".fts",
    ".tif",
    ".tiff",
    ".psd"
  ];
  static readonly NO_VALUE = "NO_VALUE";
  static readonly ORIGINAL_REVISION = "0";
  static readonly SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "CHF", "CNY"];
}
