import { Component, OnInit } from "@angular/core";
import { FormGroup } from "@angular/forms";
import { SetBreadcrumb } from "@app/store/actions/breadcrumb.actions";
import { State } from "@app/store/state";
import { Store } from "@ngrx/store";
import { FormlyFieldConfig } from "@ngx-formly/core";
import { TranslateService } from "@ngx-translate/core";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { ClassicRoutesService } from "@shared/services/classic-routes.service";
import { TitleService } from "@shared/services/title/title.service";
import { UploadDataService } from "@shared/services/upload-metadata/upload-data.service";
import { UserSubscriptionService } from "@shared/services/user-subscription/user-subscription.service";
import { WindowRefService } from "@shared/services/window-ref.service";
import { SubscriptionName } from "@shared/types/subscription-name.type";
import { UploadState, UploadxService } from "ngx-uploadx";
import { takeUntil } from "rxjs/operators";

@Component({
  selector: "astrobin-uploader-page",
  templateUrl: "./uploader-page.component.html",
  styleUrls: ["./uploader-page.component.scss"]
})
export class UploaderPageComponent extends BaseComponentDirective implements OnInit {
  form = new FormGroup({});
  uploadState: UploadState;
  SubscriptionName: typeof SubscriptionName = SubscriptionName;
  pageTitle = this.translate.instant("Uploader");

  model = {
    title: "",
    image_file: ""
  };

  fields: FormlyFieldConfig[] = [
    {
      key: "title",
      id: "title",
      type: "input",
      templateOptions: {
        label: this.translate.instant("Title"),
        required: true,
        change: this._onTitleChange.bind(this)
      }
    },
    {
      key: "image_file",
      id: "image_file",
      type: "chunked-file",
      templateOptions: {
        required: true,
        experimentalTiffSupportWarning: true
      },
      validators: {
        validation: [{ name: "file-size", options: { max: 0 } }]
      }
    }
  ];

  uploadAllowed$ = this.userSubscriptionService.uploadAllowed();

  constructor(
    public readonly store$: Store<State>,
    public translate: TranslateService,
    public uploaderService: UploadxService,
    public uploadDataService: UploadDataService,
    public windowRef: WindowRefService,
    public classicRoutesService: ClassicRoutesService,
    public titleService: TitleService,
    public userSubscriptionService: UserSubscriptionService
  ) {
    super();
  }

  subscriptionWithYearlySlotsMessage(name: string, counter: number, slots: number): string {
    return this.translate.instant(
      "You have a <strong>{{0}}</strong> subscription. You have used <strong>{{1}}</strong> of " +
        "your <strong>{{2}}</strong> yearly upload slots.",
      {
        0: name,
        1: counter,
        2: slots
      }
    );
  }

  subscriptionWithTotalSlotsMessage(name: string, counter: number, slots: number): string {
    return this.translate.instant(
      "You have a <strong>{{0}}</strong> subscription. You have used <strong>{{1}}</strong> of " +
        "your <strong>{{2}}</strong> upload slots.",
      {
        0: name,
        1: counter,
        2: slots
      }
    );
  }

  subscriptionWithUnlimitedSlotsMessage(name: string): string {
    return this.translate.instant("You have a <strong>{{0}}</strong> subscription. Enjoy your unlimited uploads!", {
      0: name
    });
  }

  ngOnInit(): void {
    this.titleService.setTitle(this.pageTitle);
    this.store$.dispatch(
      new SetBreadcrumb({
        breadcrumb: [{ label: this.pageTitle }]
      })
    );

    this.uploadDataService.setMetadata("image-upload", { is_wip: true });
    this.uploadDataService.setMetadata("image-upload", { skip_notifications: true });

    this.userSubscriptionService.fileSizeAllowed(0).subscribe(result => {
      const field = this.fields.filter(x => x.key === "image_file")[0];
      const validator = field.validators.validation.filter(x => x.name === "file-size")[0];
      validator.options.max = result.max;
    });

    this.uploaderService.events.pipe(takeUntil(this.destroyed$)).subscribe(uploadState => {
      this.uploadState = uploadState;

      if (uploadState.status === "complete") {
        const response = JSON.parse(uploadState.response as string);
        const hash = response.hash;
        this.windowRef.nativeWindow.location.assign(`${this.classicRoutesService.EDIT_IMAGE_THUMBNAILS(hash)}?upload`);
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

  private _onTitleChange() {
    this.uploadDataService.setMetadata("image-upload", { title: this.model.title });
  }
}
