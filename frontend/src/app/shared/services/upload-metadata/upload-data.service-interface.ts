export interface UploadDataServiceInterface {
  setMetadata(filename: string, metadata: { [key: string]: any }): void;
}
