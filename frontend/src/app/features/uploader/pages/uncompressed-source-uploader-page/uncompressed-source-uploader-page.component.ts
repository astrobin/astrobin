import { Component, OnInit } from "@angular/core";
import { FormGroup } from "@angular/forms";
import { ActivatedRoute } from "@angular/router";
import { SetBreadcrumb } from "@app/store/actions/breadcrumb.actions";
import { State } from "@app/store/state";
import { environment } from "@env/environment";
import { Store } from "@ngrx/store";
import { FormlyFieldConfig } from "@ngx-formly/core";
import { TranslateService } from "@ngx-translate/core";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { Constants } from "@shared/constants";
import { ImageInterface } from "@shared/interfaces/image.interface";
import { ImageApiService } from "@shared/services/api/classic/images/image/image-api.service";
import { ThumbnailGroupApiService } from "@shared/services/api/classic/images/thumbnail-group/thumbnail-group-api.service";
import { ClassicRoutesService } from "@shared/services/classic-routes.service";
import { TitleService } from "@shared/services/title/title.service";
import { UploadDataService } from "@shared/services/upload-metadata/upload-data.service";
import { WindowRefService } from "@shared/services/window-ref.service";
import { UploadState, UploadxService } from "ngx-uploadx";
import { Observable } from "rxjs";
import { map, take, takeUntil } from "rxjs/operators";

@Component({
  selector: "astrobin-uncompressed-source-uploader-page",
  templateUrl: "./uncompressed-source-uploader-page.component.html",
  styleUrls: ["./uncompressed-source-uploader-page.component.scss"]
})
export class UncompressedSourceUploaderPageComponent extends BaseComponentDirective implements OnInit {
  form = new FormGroup({});
  uploadState: UploadState;
  pageTitle = this.translate.instant("Uncompressed source uploader");

  model = {
    image_file: ""
  };

  fields: FormlyFieldConfig[] = [
    {
      key: "image_file",
      id: "image_file",
      type: "chunked-file",
      templateOptions: {
        required: true
      }
    }
  ];

  imageThumbnail$: Observable<string>;

  image: ImageInterface;

  constructor(
    public readonly store$: Store<State>,
    public readonly translate: TranslateService,
    public readonly uploaderService: UploadxService,
    public readonly uploadDataService: UploadDataService,
    public readonly windowRef: WindowRefService,
    public readonly classicRoutesService: ClassicRoutesService,
    public readonly route: ActivatedRoute,
    public readonly titleService: TitleService,
    public readonly thumbnailGroupApiService: ThumbnailGroupApiService,
    public readonly imageApiService: ImageApiService
  ) {
    super();
  }

  ngOnInit(): void {
    this.image = this.route.snapshot.data.image;

    this.titleService.setTitle(this.pageTitle);
    this.store$.dispatch(
      new SetBreadcrumb({
        breadcrumb: [
          { label: this.translate.instant("Image") },
          { label: this.image.title },
          { label: this.pageTitle }
        ]
      })
    );

    this.uploadDataService.patchMetadata("image-upload", { image_id: this.image.pk });
    this.uploadDataService.patchMetadata("image-upload", {
      allowedExtensions: Constants.ALLOWED_UNCOMPRESSED_SOURCE_UPLOAD_EXTENSIONS
    });

    this.imageThumbnail$ = this.thumbnailGroupApiService
      .getThumbnailGroup(this.image.pk, Constants.ORIGINAL_REVISION)
      .pipe(map(thumbnailGroup => thumbnailGroup.gallery));

    this.uploadDataService.setEndpoint(`${environment.classicBaseUrl}/api/v2/images/uncompressed-source-upload/`);
    this.uploadDataService.setAllowedTypes(Constants.ALLOWED_UNCOMPRESSED_SOURCE_UPLOAD_EXTENSIONS.join(","));

    this.uploaderService.events.pipe(takeUntil(this.destroyed$)).subscribe(uploadState => {
      this.uploadState = uploadState;

      if (uploadState.status === "complete") {
        const response = JSON.parse(uploadState.response as string);
        this.imageApiService
          .getImage(response.image)
          .pipe(take(1))
          .subscribe(image => {
            // @ts-ignore
            this.windowRef.nativeWindow.location.assign(this.classicRoutesService.IMAGE(image.hash || "" + image.pk));
          });
      }
    });
  }

  onSubmit() {
    if (this.form.valid) {
      this.uploaderService.control({ action: "upload" });
    }
  }

  uploadButtonLoading(): boolean {
    return (
      this.form.valid &&
      this.uploadState &&
      ["queue", "uploading", "retry", "complete"].indexOf(this.uploadState.status) > -1
    );
  }
}
