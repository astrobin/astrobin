import { Component, ElementRef, OnInit, QueryList, ViewChildren } from "@angular/core";
import { selectApp, selectBackendConfig } from "@app/store/selectors/app/app.selectors";
import { State } from "@app/store/state";
import { HiddenImage, SubmissionInterface, VoteInterface } from "@features/iotd/services/iotd-api.service";
import { LoadDismissedImages, LoadHiddenImages } from "@features/iotd/store/iotd.actions";
import {
  PromotionImageInterface,
  ReviewImageInterface,
  SubmissionImageInterface
} from "@features/iotd/store/iotd.reducer";
import { selectHiddenImages, selectSubmissions } from "@features/iotd/store/iotd.selectors";
import { Store } from "@ngrx/store";
import { TranslateService } from "@ngx-translate/core";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { ImageAlias } from "@shared/enums/image-alias.enum";
import { BackendConfigInterface } from "@shared/interfaces/backend-config.interface";
import { PaginatedApiResultInterface } from "@shared/services/api/interfaces/paginated-api-result.interface";
import { PopNotificationsService } from "@shared/services/pop-notifications.service";
import { distinctUntilChangedObj } from "@shared/services/utils/utils.service";
import { WindowRefService } from "@shared/services/window-ref.service";
import { Observable } from "rxjs";
import { filter, map, switchMap, takeUntil } from "rxjs/operators";

@Component({
  selector: "astrobin-base-promotion-queue",
  template: ""
})
export abstract class BasePromotionQueueComponent extends BaseComponentDirective implements OnInit {
  ImageAlias = ImageAlias;

  page = 1;
  pageSize$: Observable<number> = this.store$
    .select(selectBackendConfig)
    .pipe(map(backendConfig => backendConfig.IOTD_QUEUES_PAGE_SIZE));

  hiddenImages$: Observable<HiddenImage[]> = this.store$.select(selectHiddenImages);

  abstract queue$: Observable<PaginatedApiResultInterface<SubmissionImageInterface | ReviewImageInterface>>;
  abstract promotions$: Observable<SubmissionInterface[] | VoteInterface[]>;

  @ViewChildren("promotionQueueEntries")
  promotionQueueEntries: QueryList<ElementRef>;

  protected constructor(
    public readonly store$: Store<State>,
    public readonly popNotificationsService: PopNotificationsService,
    public readonly translateService: TranslateService,
    public readonly windowRefService: WindowRefService
  ) {
    super();
  }

  ngOnInit(): void {
    this.store$
      .select(selectApp)
      .pipe(
        takeUntil(this.destroyed$),
        map(state => state.backendConfig),
        filter(backendConfig => !!backendConfig),
        distinctUntilChangedObj(),
        switchMap(backendConfig =>
          this.store$.select(selectSubmissions).pipe(map(submissions => ({ backendConfig, submissions })))
        )
      )
      .subscribe(({ backendConfig, submissions }) => {
        if (submissions.length === this.maxPromotionsPerDay(backendConfig)) {
          this.popNotificationsService.info(
            this.translateService.instant(
              "Please note: you don't <strong>have to</strong> use all your slots. It's ok to use fewer if you " +
                "don't think there are that many worthy images today."
            ),
            null,
            {
              enableHtml: true
            }
          );
        }
      });

    this.refresh();
  }

  refresh(): void {
    this.store$.dispatch(new LoadHiddenImages());
    this.store$.dispatch(new LoadDismissedImages());

    this.loadQueue(1);
    this.loadPromotions();
  }

  abstract loadQueue(page: number): void;

  abstract loadPromotions(): void;

  abstract maxPromotionsPerDay(backendConfig: BackendConfigInterface): number;

  pageChange(page: number): void {
    this.page = page;
    this.loadQueue(page);
    this.windowRefService.nativeWindow.scroll({ top: 0, behavior: "smooth" });
  }

  entryExists(imageId: number): boolean {
    return this._getEntryElement(imageId) !== null;
  }

  scrollToEntry(imageId: number): void {
    const element = this._getEntryElement(imageId);

    if (element) {
      element.nativeElement.scrollIntoView({ behavior: "smooth" });
    }
  }

  private _getEntryElement(imageId: number): ElementRef | null {
    const matches = this.promotionQueueEntries.filter(
      entry => entry.nativeElement.id === `promotion-queue-entry-${imageId}`
    );

    if (matches.length > 0) {
      return matches[0];
    }

    return null;
  }
}
