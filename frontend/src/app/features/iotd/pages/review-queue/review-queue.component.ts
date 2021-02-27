import { Component, OnInit } from "@angular/core";
import { SetBreadcrumb } from "@app/store/actions/breadcrumb.actions";
import { State } from "@app/store/state";
import { BasePromotionQueueComponent } from "@features/iotd/components/base-promotion-queue/base-promotion-queue.component";
import { VoteInterface } from "@features/iotd/services/iotd-api.service";
import { LoadReviewQueue, LoadVotes } from "@features/iotd/store/iotd.actions";
import { ReviewImageInterface } from "@features/iotd/store/iotd.reducer";
import { selectReviewQueue, selectReviews } from "@features/iotd/store/iotd.selectors";
import { Store } from "@ngrx/store";
import { TranslateService } from "@ngx-translate/core";
import { BackendConfigInterface } from "@shared/interfaces/backend-config.interface";
import { PaginatedApiResultInterface } from "@shared/services/api/interfaces/paginated-api-result.interface";
import { PopNotificationsService } from "@shared/services/pop-notifications.service";
import { TitleService } from "@shared/services/title/title.service";
import { WindowRefService } from "@shared/services/window-ref.service";
import { Observable } from "rxjs";

@Component({
  selector: "astrobin-review-queue",
  templateUrl: "./review-queue.component.html",
  styleUrls: ["./review-queue.component.scss"]
})
export class ReviewQueueComponent extends BasePromotionQueueComponent implements OnInit {
  queue$: Observable<PaginatedApiResultInterface<ReviewImageInterface>> = this.store$.select(selectReviewQueue);
  promotions$: Observable<VoteInterface[]> = this.store$.select(selectReviews);

  constructor(
    public readonly store$: Store<State>,
    public readonly translateService: TranslateService,
    public readonly popNotificationsService: PopNotificationsService,
    public readonly titleService: TitleService,
    public readonly windowRefService: WindowRefService
  ) {
    super(store$, popNotificationsService, translateService, windowRefService);
  }

  ngOnInit(): void {
    super.ngOnInit();

    const title = this.translateService.instant("Review queue");
    this.titleService.setTitle(title);
    this.store$.dispatch(
      new SetBreadcrumb({
        breadcrumb: [{ label: "IOTD" }, { label: title }]
      })
    );
  }

  loadQueue(page: number): void {
    this.store$.dispatch(new LoadReviewQueue({ page }));
  }

  loadPromotions(): void {
    this.store$.dispatch(new LoadVotes());
  }

  maxPromotionsPerDay(backendConfig: BackendConfigInterface): number {
    return backendConfig.IOTD_REVIEW_MAX_PER_DAY;
  }
}
