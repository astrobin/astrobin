import { Component } from "@angular/core";
import { selectIotdMaxReviewsPerDay } from "@app/store/selectors/app/app.selectors";
import { State } from "@app/store/state";
import { BasePromotionSlotsComponent } from "@features/iotd/components/base-promotion-slots/base-promotion-slots.component";
import { VoteInterface } from "@features/iotd/services/iotd-api.service";
import { selectReviews } from "@features/iotd/store/iotd.selectors";
import { select, Store } from "@ngrx/store";
import { Observable } from "rxjs";

@Component({
  selector: "astrobin-review-slots",
  templateUrl: "../base-promotion-slots/base-promotion-slots.component.html",
  styleUrls: ["../base-promotion-slots/base-promotion-slots.component.scss"]
})
export class ReviewSlotsComponent extends BasePromotionSlotsComponent {
  promotions$: Observable<VoteInterface[]> = this.store$.select(selectReviews);
  slotsCount$: Observable<number> = this.store$.pipe(select(selectIotdMaxReviewsPerDay));

  constructor(public readonly store$: Store<State>) {
    super(store$);
  }
}
