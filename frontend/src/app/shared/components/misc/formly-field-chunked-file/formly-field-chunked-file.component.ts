import { Component, OnDestroy, OnInit } from "@angular/core";
import { State } from "@app/store/state";
import { Store } from "@ngrx/store";
import { FieldType } from "@ngx-formly/core";
import { TranslateService } from "@ngx-translate/core";
import { FileUpload } from "@shared/components/misc/formly-field-chunked-file/file-upload";
import { Constants } from "@shared/constants";
import { AuthService } from "@shared/services/auth.service";
import { ClassicRoutesService } from "@shared/services/classic-routes.service";
import { PopNotificationsService } from "@shared/services/pop-notifications.service";
import { UploadDataService } from "@shared/services/upload-metadata/upload-data.service";
import { UserSubscriptionService } from "@shared/services/user-subscription/user-subscription.service";
import { UtilsService } from "@shared/services/utils/utils.service";
import { Tus, UploadState, UploadxOptions, UploadxService } from "ngx-uploadx";
import { forkJoin, Observable, of, Subscription } from "rxjs";
import { filter, map, take } from "rxjs/operators";

// PLEASE NOTE: due to the usage of the UploaderDataService, there can be only one chunked file upload field on a page
// at any given time.

@Component({
  selector: "astrobin-formly-field-chunked-file",
  templateUrl: "./formly-field-chunked-file.component.html",
  styleUrls: ["./formly-field-chunked-file.component.scss"]
})
export class FormlyFieldChunkedFileComponent extends FieldType implements OnInit, OnDestroy {
  upload: FileUpload;
  uploadSize: number;
  uploadState: UploadState;
  uploadOptions: UploadxOptions = {
    allowedTypes: Constants.ALLOWED_UPLOAD_EXTENSIONS.join(","),
    uploaderClass: Tus,
    chunkSize: 1024 * 1024,
    multiple: false,
    autoUpload: false,
    authorize: req => {
      const token = this.authService.getClassicApiToken();
      req.headers.Authorization = `Token ${token}`;
      return req;
    },
    metadata: {
      filename: new UtilsService().uuid()
    }
  };

  private _metadataChangesSubscription: Subscription;
  private _endpointChangesSubscription: Subscription;
  private _allowedTypesChangesSubscription: Subscription;

  constructor(
    public readonly store: Store<State>,
    public readonly authService: AuthService,
    public readonly uploaderService: UploadxService,
    public readonly uploadDataService: UploadDataService,
    public readonly utilsService: UtilsService,
    public readonly popNotificationsService: PopNotificationsService,
    public readonly translateService: TranslateService,
    public readonly userSubscriptionService: UserSubscriptionService,
    public readonly classicRoutesService: ClassicRoutesService
  ) {
    super();
  }

  get status$(): Observable<string> {
    if (!this.uploadState) {
      return of("");
    }

    if (this.isInitializingUpload()) {
      return this.translateService.stream("Initializing upload, please wait...");
    } else if (this.isUploading()) {
      return this.translateService.stream("Uploading...");
    } else if (this.isFinalizingUpload() || this.isComplete()) {
      return this.translateService.stream("Finalizing upload, please wait...");
    }

    return of("");
  }

  ngOnInit() {
    this.uploaderService.init(this.uploadOptions);
    this.uploaderService.events.subscribe((state: UploadState) => {
      this.uploadState = state;

      if (state.status === "error") {
        let message: string;

        switch (state.responseStatus) {
          case 401:
            message = this.translateService.instant("Authentication error. Please log out and in again.");
            break;
          case 400:
            message = this.translateService.instant("Invalid data, please refresh the page and try again.");
            break;
          case 415:
            message = this.translateService.instant(
              "AstroBin could not read your file as an image. Please try a different format."
            );
            break;
          default:
            message = this.translateService.instant("Unknown error, please refresh the page and try again.");
            break;
        }

        this.popNotificationsService.error(message, null, {
          disableTimeOut: true
        });
      } else if (state.status === "added") {
        // We only allow one upload at a time.
        this.uploaderService.queue = this.uploaderService.queue.slice(-1);

        forkJoin({
          extensionCheck: this._checkFileExtension(state.name),
          fileSizeCheck: this._checkFileSize(state.size),
          imageDimensionsCheck: this._checkImageDimensions(state.file)
        }).subscribe(result => {
          if (result.extensionCheck && result.fileSizeCheck && result.imageDimensionsCheck) {
            this.upload = new FileUpload(state);
            this.uploadSize = state.size;
            this.formControl.setValue(this.uploadState.file);
          } else {
            this.formControl.setValue(null);
          }
        });
      }
    });

    this._metadataChangesSubscription = this.uploadDataService.metadataChanges$
      .pipe(filter(event => !!event))
      .subscribe(event => {
        this.uploadOptions.metadata = {
          ...this.uploadOptions.metadata,
          ...event.metadata
        };
        this.uploaderService.queue.forEach(
          queue => (queue.metadata = { ...queue.metadata, ...this.uploadOptions.metadata })
        );
      });

    this._endpointChangesSubscription = this.uploadDataService.endpointChanges$.subscribe(endpoint => {
      this.uploadOptions.endpoint = endpoint;
    });

    this._allowedTypesChangesSubscription = this.uploadDataService.allowedTypesChanges$.subscribe(allowedTypes => {
      this.uploadOptions.allowedTypes = allowedTypes;
    });
  }

  isActive(): boolean {
    return !this.uploadState || ["queue", "uploading", "paused", "complete"].indexOf(this.uploadState.status) === -1;
  }

  isInitializingUpload(): boolean {
    return this.uploadState && this.uploadState.status === "uploading" && !this.uploadState.progress;
  }

  isUploading(): boolean {
    return (
      this.uploadState &&
      ["uploading", "retry"].indexOf(this.uploadState.status) > -1 &&
      this.uploadState.progress &&
      this.uploadState.progress > 0
    );
  }

  isFinalizingUpload(): boolean {
    return this.uploadState && this.uploadState.status === "uploading" && this.uploadState.progress === 100;
  }

  isComplete(): boolean {
    return this.uploadState && this.uploadState.status === "complete";
  }

  ngOnDestroy(): void {
    if (this._metadataChangesSubscription) {
      this._metadataChangesSubscription.unsubscribe();
    }

    if (this._endpointChangesSubscription) {
      this._endpointChangesSubscription.unsubscribe();
    }

    if (this._allowedTypesChangesSubscription) {
      this._allowedTypesChangesSubscription.unsubscribe();
    }
  }

  private _checkFileExtension(filename: string): Observable<boolean> {
    const extension = this.utilsService.fileExtension(filename).toLowerCase();

    if (this.uploadOptions.allowedTypes.indexOf(`.${extension}`) > -1) {
      this._warnAbout16BitTiff(filename);
      return of(true);
    }

    this.popNotificationsService.error(this.translateService.instant("File type not supported") + `: ${extension}`);

    return of(false);
  }

  private _checkFileSize(size: number): Observable<boolean> {
    return this.userSubscriptionService.fileSizeAllowed(size).pipe(
      map(result => {
        if (result.allowed) {
          this._warnAboutVeryLargeFile(size);
          return true;
        } else {
          this.popNotificationsService.error(
            this.translateService.instant(
              "Sorry, but this image is too large. Under your current subscription plan, the maximum " +
                "allowed image size is {{max}}.",
              {
                max: result.max / 1024 / 1024 + " MB"
              }
            )
          );
          return false;
        }
      })
    );
  }

  private _checkImageDimensions(file: File): Observable<boolean> {
    if (this.utilsService.isImage(file.name)) {
      return new Observable<boolean>(observer => {
        // @ts-ignore
        const image = new Image();
        image.onload = () => {
          this.store
            .pipe(
              take(1),
              map(state => state.app.backendConfig)
            )
            .subscribe(backendConfig => {
              if (image.width * image.height > backendConfig.MAX_IMAGE_PIXELS) {
                const message =
                  "Sorry, but this image is too large. The maximum allowed total number of pixels is {{max}}.";
                this.popNotificationsService.error(
                  this.translateService.instant(message, {
                    max: +backendConfig.MAX_IMAGE_PIXELS
                  })
                );
                observer.next(false);
              } else {
                this.uploadDataService.patchMetadata("image-upload", {
                  width: image.width,
                  height: image.height
                });
                observer.next(true);
              }
              observer.complete();
            });
        };
        image.src = URL.createObjectURL(file);
      });
    }

    return of(true);
  }

  private _warnAboutVeryLargeFile(size: number): void {
    const MB = 1024 * 1024;
    let message;

    if (size > 200 * MB) {
      message = this.translateService.instant(
        "Warning! That's a large file you got there! AstroBin does not impose artificial limitation in the file " +
          "size you can upload with an Ultimate subscription, but we cannot guarantee that all images above 200 MB or " +
          "~8000x8000 pixels will work. Feel free to give it a shot tho!"
      );
    } else if (size > 100 * MB) {
      message = this.translateService.instant(
        "Heads up! Are you sure you want to upload such a large file? It's okay to do so but probably not many " +
          "people will want to see it at its full resolution, if it will take too long for them to download it."
      );
    }

    if (!!message) {
      this.popNotificationsService.warning(message);
    }
  }

  private _warnAbout16BitTiff(filename: string): void {
    if (!this.to.experimentalTiffSupportWarning) {
      return;
    }

    const extension = this.utilsService.fileExtension(filename).toLowerCase();

    if (extension === "tif" || extension === "tiff") {
      const message = this.translateService.instant(
        "Heads up! TIFF support on AstroBin is experimental. Grayscale images that are 16-bit or higher, or " +
          "with floating points precision, currently are not supported. If your file is a color image, or already an " +
          "8-bit depth grayscale, please ignore this warning message."
      );
      this.popNotificationsService.warning(message);
    }
  }
}
