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
import { ThumbnailGroupApiService } from "@shared/services/api/classic/images/thumbnail-group/thumbnail-group-api.service";
import { ClassicRoutesService } from "@shared/services/classic-routes.service";
import { TitleService } from "@shared/services/title/title.service";
import { UploadDataService } from "@shared/services/upload-metadata/upload-data.service";
import { WindowRefService } from "@shared/services/window-ref.service";
import { UploadState, UploadxService } from "ngx-uploadx";
import { Observable } from "rxjs";
import { map, takeUntil } from "rxjs/operators";

@Component({
  selector: "astrobin-revision-uploader-page",
  templateUrl: "./revision-uploader-page.component.html",
  styleUrls: ["./revision-uploader-page.component.scss"]
})
export class RevisionUploaderPageComponent extends BaseComponentDirective implements OnInit {
  form = new FormGroup({});
  uploadState: UploadState;
  pageTitle = this.translate.instant("Revision uploader");

  model = {
    image_file: "",
    description: "",
    skip_notifications: false,
    mark_as_final: true
  };

  fields: FormlyFieldConfig[] = [
    {
      key: "image_file",
      id: "image_file",
      type: "chunked-file",
      templateOptions: {
        required: true,
        experimentalTiffSupportWarning: true
      }
    },
    {
      key: "description",
      id: "description",
      type: "textarea",
      templateOptions: {
        label: this.translate.instant("Description"),
        required: false,
        change: this._onDescriptionChange.bind(this),
        rows: 4
      }
    },
    {
      key: "skip_notifications",
      id: "skip_notifications",
      type: "checkbox",
      templateOptions: {
        label: this.translate.instant("Skip notifications"),
        description: this.translate.instant("Do not notify your followers about this revision."),
        change: this._onSkipNotificationsChange.bind(this)
      }
    },
    {
      key: "mark_as_final",
      id: "mark_as_final",
      type: "checkbox",
      templateOptions: {
        label: this.translate.instant("Mark as final"),
        description: this.translate.instant("Mark this revision as the final rendition of your image."),
        change: this._onMarkAsFinalChange.bind(this)
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
    public readonly thumbnailGroupApiService: ThumbnailGroupApiService
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
    this.uploadDataService.patchMetadata("image-upload", { is_revision: true });
    this.uploadDataService.patchMetadata("image-upload", { description: Constants.NO_VALUE });

    this.imageThumbnail$ = this.thumbnailGroupApiService
      .getThumbnailGroup(this.image.pk, Constants.ORIGINAL_REVISION)
      .pipe(map(thumbnailGroup => thumbnailGroup.gallery));

    this._onDescriptionChange();
    this._onSkipNotificationsChange();
    this._onMarkAsFinalChange();

    this.uploadDataService.setEndpoint(`${environment.classicBaseUrl}/api/v2/images/image-revision/`);

    this.uploaderService.events.pipe(takeUntil(this.destroyed$)).subscribe(uploadState => {
      this.uploadState = uploadState;

      if (uploadState.status === "complete") {
        const response = JSON.parse(uploadState.response as string);
        // @ts-ignore
        this.windowRef.nativeWindow.location.assign(this.classicRoutesService.EDIT_IMAGE_REVISION(response.pk));
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

  private _onDescriptionChange() {
    this.uploadDataService.patchMetadata("image-upload", { description: this.model.description || Constants.NO_VALUE });
  }

  private _onSkipNotificationsChange() {
    this.uploadDataService.patchMetadata("image-upload", { skip_notifications: this.model.skip_notifications });
  }

  private _onMarkAsFinalChange() {
    this.uploadDataService.patchMetadata("image-upload", { mark_as_final: this.model.mark_as_final });
  }
}
