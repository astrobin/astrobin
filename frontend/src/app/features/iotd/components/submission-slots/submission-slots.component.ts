import { Component } from "@angular/core";
import { selectIotdMaxSubmissionsPerDay } from "@app/store/selectors/app/app.selectors";
import { State } from "@app/store/state";
import { BasePromotionSlotsComponent } from "@features/iotd/components/base-promotion-slots/base-promotion-slots.component";
import { SubmissionInterface } from "@features/iotd/services/iotd-api.service";
import { selectSubmissions } from "@features/iotd/store/iotd.selectors";
import { select, Store } from "@ngrx/store";
import { Observable } from "rxjs";

@Component({
  selector: "astrobin-submission-slots",
  templateUrl: "../base-promotion-slots/base-promotion-slots.component.html",
  styleUrls: ["../base-promotion-slots/base-promotion-slots.component.scss"]
})
export class SubmissionSlotsComponent extends BasePromotionSlotsComponent {
  promotions$: Observable<SubmissionInterface[]> = this.store$.select(selectSubmissions);
  slotsCount$: Observable<number> = this.store$.pipe(select(selectIotdMaxSubmissionsPerDay));

  constructor(public readonly store$: Store<State>) {
    super(store$);
  }
}
