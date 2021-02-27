import { UploadState } from "ngx-uploadx";

export class FileUpload {
  name: string;
  uploadId: string;
  progress: number;
  status: string;

  constructor(state: UploadState) {
    this.uploadId = state.uploadId;
    this.name = state.name;
    this.progress = state.progress;
    this.status = state.status;
  }
}
