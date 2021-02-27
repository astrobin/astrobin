import { Component } from "@angular/core";
import { State } from "@app/store/state";
import { BasePromotionEntryComponent } from "@features/iotd/components/base-promotion-entry/base-promotion-entry.component";
import { DeleteVote, PostVote } from "@features/iotd/store/iotd.actions";
import { selectReviewForImage } from "@features/iotd/store/iotd.selectors";
import { NgbModal } from "@ng-bootstrap/ng-bootstrap";
import { Store } from "@ngrx/store";
import { LoadingService } from "@shared/services/loading.service";
import { Observable } from "rxjs";
import { distinctUntilChanged, map, take, tap } from "rxjs/operators";

@Component({
  selector: "astrobin-review-entry",
  templateUrl: "../base-promotion-entry/base-promotion-entry.component.html",
  styleUrls: ["../base-promotion-entry/base-promotion-entry.component.scss"]
})
export class ReviewEntryComponent extends BasePromotionEntryComponent {
  constructor(
    public readonly store$: Store<State>,
    public readonly loadingService: LoadingService,
    public modalService: NgbModal
  ) {
    super(store$, modalService);
  }

  isPromoted$(imageId: number): Observable<boolean> {
    return this.store$.select(selectReviewForImage, imageId).pipe(
      map(review => review !== null),
      distinctUntilChanged()
    );
  }

  alreadyPromoted$(imageId: number): Observable<boolean> {
    return this.store$.select(selectReviewForImage, imageId).pipe(map(review => !!review));
  }

  promote(imageId: number): void {
    this.store$.dispatch(new PostVote({ imageId }));
  }

  retractPromotion(imageId: number): void {
    this.store$
      .select(selectReviewForImage, imageId)
      .pipe(
        take(1),
        tap(review => this.store$.dispatch(new DeleteVote({ id: review.id })))
      )
      .subscribe();
  }
}
